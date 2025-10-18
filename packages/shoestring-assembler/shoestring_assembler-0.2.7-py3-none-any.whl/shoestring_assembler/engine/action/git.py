import rich.progress
from pathlib import Path
import subprocess
import re
import select
import os

from shoestring_assembler.interface.events import Update, Audit, Progress


class GetSolutionUsingGit:
    remote_tag_search_regex = re.compile("^\w*\trefs/tags/(?P<tag>[\w\d\.-]*)\s*")
    strict_tag_regex = re.compile("^v(\d*)\.(\d*)\.(\d*)$")

    @classmethod
    async def download(cls, spec):
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = (
            "0"  # prevents hanging on username input if url invalid
        )

        clone_dir = spec["download_location"] / Path(spec["name"].replace(" ", ""))

        command = [
            "git",
            "clone",
            "--progress",  # force inclusion of progress updates
            "--branch",
            spec["selected_version"],
            spec["url"],
            clone_dir,
        ]

        await Audit.submit("solution_download", Audit.Type.Log, command=command)

        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env
        )  # git outputs updates over stderr

        
        await git_clone_progress(process, spec["name"])

        return process.returncode == 0, clone_dir

    @classmethod
    def available_versions(cls, url, minimum_version):
        minimum_vsn_tuple = cls.strict_tag_regex.match(minimum_version).groups()
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = (
            "0"  # prevents hanging on username input if url invalid
        )
        command = ["git", "ls-remote", "--tags", "--sort=-version:refname", url]
        result = subprocess.run(command, capture_output=True, env=env)
        readout = result.stdout.decode()

        tag_entries = []
        for line in readout.split("\n"):
            tags = cls.remote_tag_search_regex.findall(line)

            for tag in tags:
                match = cls.strict_tag_regex.match(tag)
                if match:
                    if match.groups() >= minimum_vsn_tuple:
                        tag_entries.append(tag)

        return tag_entries


# display utilities


async def git_clone_progress(process,name):
    # likely overkill but would be good to be able to relay updates
    buffer = bytearray()
    active_progress_tracker = None
    regex = re.compile(
        "^(remote: )?(?P<label>.*?):?\s*\d{0,3}% \((?P<progress>\d*)/(?P<total>\d*)\).*"
    )
    while process.returncode == None:
        while True:
            line = None
            line_update = False

            read_list, _wlist, _xlist = select.select([process.stderr], [], [], 1)
            if process.stderr in read_list:
                char = process.stderr.read(1)
                if char == b"\r" or char == b"\n":
                    if char == b"\r":
                        line_update = True
                    line = buffer.decode()
                    buffer.clear()
                elif char:
                    buffer += char
                else:
                    break  # end of file
            else:
                break  # timeout - break to check if process terminated

            if line:
                if active_progress_tracker or line_update:  # progress update line
                    m = regex.match(line)
                    if active_progress_tracker is not None:
                        if line_update:  # update
                            await active_progress_tracker.update(
                                int(m.group("progress"))
                            )
                        else:  # end
                            if m:
                                await active_progress_tracker.update(
                                    int(m.group("progress"))
                                )
                            else:
                                await active_progress_tracker.update(
                                    active_progress_tracker.total
                                )
                            active_progress_tracker = None
                    elif line_update:  # new
                        active_progress_tracker = await Progress.new_tracker(
                            re.sub(r'\s+', '',f"{name}-{m.group('label')}"),
                            f"{name} - {m.group('label')}",
                            int(m.group("total")),
                            int(m.group("progress")),
                        )
                else:  # normal line
                    # TODO: work out when this occurs - on errors?
                    pass
            else:
                pass

        process.poll()
