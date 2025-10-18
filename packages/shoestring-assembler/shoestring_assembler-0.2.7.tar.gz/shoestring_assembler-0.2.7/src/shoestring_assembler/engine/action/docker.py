import select
import subprocess

from shoestring_assembler.model import SolutionModel
from shoestring_assembler.interface.events import (
    Audit,
    Update,
    Progress,
    ProgressSection,
    FatalError,
    Input
)
from shoestring_assembler.interface.events.progress import ProgressBar

from pathlib import Path
import yaml
import json
import datetime
import asyncio

# TODO - look at --progress json tag for all operations - when not affected by bug


class Docker:
    @staticmethod
    def base_compose_command(solution_model):
        if not solution_model.fs.compose_file.exists():
            raise FatalError("Solution hasn't been assembled yet")

        return [
            "docker",
            "compose",
            "--project-directory",
            str(solution_model.fs.root),
            "-f",
            str(solution_model.fs.compose_file),
            "--env-file",
            str(solution_model.fs.env_file),
        ]

    @classmethod
    def logs(cls, solution_model: SolutionModel, service):
        command = [*Docker.base_compose_command(solution_model), "logs", "-f"]
        if service:
            command.append(str(service))
        subprocess.run(command)

    @classmethod
    async def build(cls, solution_model: SolutionModel):
        command = [
            *Docker.base_compose_command(solution_model),
            # "--progress",
            # "json",
            "build",
        ]

        await Audit.submit("docker::build::command", Audit.Type.Log, command=command)
        await Update.InfoMsg(
            "(In future you will be shown step by step updates, but there is currently a bug in docker compose that is preventing this)"
        )  # https://github.com/docker/compose/issues/13164

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out_buffer = bytearray()
        err_buffer = bytearray()
        last_update = datetime.datetime.now()
        while process.returncode == None:
            while True:
                out_line = None
                err_line = None
                no_stdout = False
                no_stderr = False

                read_list, _wlist, _xlist = select.select(
                    [process.stderr, process.stdout], [], [], 1
                )
                if process.stderr in read_list:
                    char = process.stderr.read(1)
                    if char == b"\n":
                        err_line = err_buffer.decode()
                        err_buffer.clear()
                    elif char:
                        err_buffer += char
                    else:
                        no_stdout = True  # end of file
                else:
                    no_stdout = True  # timeout - break to check if process terminated

                if process.stdout in read_list:
                    char = process.stdout.read(1)
                    if char == b"\n":
                        out_line = out_buffer.decode()
                        out_buffer.clear()
                    elif char:
                        out_buffer += char
                    else:
                        no_stderr = True  # end of file
                else:
                    no_stderr = True  # timeout - break to check if process terminated

                if no_stdout and no_stderr:
                    break

                if out_line:
                    await Update.InfoMsg(f"[white]{out_line}", detail_level=2)
                    if datetime.datetime.now() - last_update > datetime.timedelta(
                        seconds=30
                    ):
                        last_update = datetime.datetime.now()
                        await Update.InfoMsg(f"({last_update}) still working...")
                if err_line:
                    await Update.SuccessMsg(f"{err_line}")

            await asyncio.sleep(0) # yield
            process.poll()

        process.wait()

        return process.returncode == 0

    @classmethod
    async def setup_containers(cls, solution_model: SolutionModel):

        if solution_model.compose_spec is None:
            raise FatalError(
                "Solution doesn't have a compose file - this is likely because it hasn't been assembled"
            )

        for service_name, service_spec in solution_model.compose_spec[
            "services"
        ].items():
            setup_cmd = service_spec.get("x-shoestring-setup-command")
            if setup_cmd:
                command = [
                    *Docker.base_compose_command(solution_model),
                    "run",
                    "--rm",
                    service_name,
                ]
                if isinstance(setup_cmd, list):
                    command.extend(setup_cmd)
                else:
                    command.append(setup_cmd)

                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )

                try:
                    await handle_async_setup_process(process)
                except asyncio.CancelledError:  # ensure subprocess is terminated on task cancellation
                    process.kill()
                    await process.wait()
                    raise

                if process.returncode == 0:
                    await Update.InfoMsg(f"{service_name} - Setup Successful")
            else:
                await Update.InfoMsg(f"{service_name} - No setup required")

    @classmethod
    async def start(cls, solution_model: SolutionModel):
        command = [
            *Docker.base_compose_command(solution_model),
            "--progress",
            "json",
            "up",
            "-d",
            "--remove-orphans",
        ]

        await Audit.submit("docker::start::command", Audit.Type.Log, command=command)

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        progress_trackers: dict[str, ProgressBar] = {}
        network_status_map = {"Creating": 2, "Created": 4}
        container_status_map = {
            "Creating": 1,
            "Created": 2,
            "Starting": 3,
            "Started": 4,
            "Running": 4,
        }

        async def handle_line(line_content):
            id_string: str = line_content.get("id")
            target_type, _, target_id = id_string.partition(" ")
            target_id = target_id.removesuffix("-1")
            if target_id not in progress_trackers.keys():
                progress_trackers[target_id] = await Progress.new_tracker(
                    target_id.strip(), target_id, 4, 0
                )
            status = line_content.get("status")
            if target_type == "Network":
                value = network_status_map.get(status)
            else:
                value = container_status_map.get(status)
            await progress_trackers[target_id].update(value)

        async with ProgressSection("start"):
            await parse_docker_json_progress(process, handle_line)

        if process.returncode == 0:
            return True
        else:
            await Update.ErrorMsg("Solution could not be started correctly")

    @classmethod
    async def stop(cls, solution_model: SolutionModel):
        command = [
            *Docker.base_compose_command(solution_model),
            "--progress",
            "json",
            "down",
        ]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        progress_trackers: dict[str, ProgressBar] = {}
        status_map = {"Stopping": 1, "Stopped": 2, "Removing": 3, "Removed": 4}

        async def handle_line(line_content):
            id_string: str = line_content.get("id")
            target_type, _, target_id = id_string.partition(" ")
            target_id = target_id.removesuffix("-1")
            if target_id not in progress_trackers.keys():
                progress_trackers[target_id] = await Progress.new_tracker(
                    target_id.strip(), target_id, 4, 0
                )
            status = line_content.get("status")
            await progress_trackers[target_id].update(status_map.get(status))

        async with ProgressSection("stop"):
            await parse_docker_json_progress(process, handle_line)

        return process.returncode == 0

    @classmethod
    async def get_running_list(cls):
        # docker compose ls --format json
        command = ["docker", "compose", "ls", "--format", "json"]
        result = subprocess.run(command, capture_output=True)

        if result.returncode != 0:
            return None

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None

async def handle_async_setup_process(process: asyncio.subprocess.Process):
    while process.returncode == None:
        response = await process.stdout.readline()
        try:
            payload = json.loads(response)
            match payload.get("type"):
                case "input":
                    response = await Input.make_request(payload)
                    if response is not None:
                        process.stdin.write((response + "\n").encode())                        
                case "output":
                    message = payload.get("message")
                    match payload.get("variant"):
                        case "heading":
                            await Update.StepHeading(message)
                        case "error":
                            await Update.ErrorMsg(message)
                        case "success":
                            await Update.SuccessMsg(message)
                        case _:
                            await Update.InfoMsg(message)
                case _:
                    print("NO TYPE")
        except json.JSONDecodeError:
            await Update.InfoMsg(response.decode().strip())


async def parse_docker_json_progress(process: subprocess.Popen, callback):
    out_buffer = bytearray()
    err_buffer = bytearray()
    while process.returncode == None:
        while True:
            out_line = None
            err_line = None
            no_stdout = False
            no_stderr = False

            read_list, _wlist, _xlist = select.select(
                [process.stderr, process.stdout], [], [], 1
            )

            if process.stderr in read_list:
                char = process.stderr.read(1)
                if char == b"\n":
                    err_line = err_buffer.decode()
                    err_buffer.clear()
                elif char:
                    err_buffer += char
                else:
                    no_stdout = True  # end of file
            else:
                no_stdout = True

            if process.stdout in read_list:
                char = process.stdout.read(1)
                if char == b"\n":
                    out_line = out_buffer.decode()
                    out_buffer.clear()
                elif char:
                    out_buffer += char
                else:
                    no_stderr = True  # end of file
            else:
                no_stderr = True

            if no_stdout and no_stderr:
                break  # timeout - break to check if process terminated

            if out_line:
                try:
                    line_content = json.loads(out_line)
                    await callback(line_content)
                except:
                    await Update.ErrorMsg(out_line)
            if err_line:
                try:
                    line_content = json.loads(err_line)
                    if "error" in line_content.keys():
                        await Update.ErrorMsg(line_content["message"])
                    elif "level" in line_content.keys():
                        await Update.ErrorMsg(line_content["msg"])
                    else:
                        await callback(line_content)
                except:
                    await Update.ErrorMsg(err_line)
        
        await asyncio.sleep(0)  # yield
        process.poll()

    process.wait()
