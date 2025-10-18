from shoestring_assembler.implementation.source import SourceImplementation, SourceABC
import rich.progress
from pathlib import Path
import subprocess
import re
import select
import asyncio
import os
from pathlib import Path
import os
import subprocess
from shoestring_assembler.model.recipe import GitSourceSpec
from shoestring_assembler.interface.events import Audit, Progress, Update


@SourceImplementation.register(GitSourceSpec)
class GitSource(SourceABC):
    async def fetch(self, dest_path: Path):

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = (
            "0"  # prevents hanging on username input if url invalid
        )

        command = [
            "git",
            "clone",
            "--progress",  # force inclusion of progress updates
            "--depth",
            "1",  # only download latest commit - no history (massive speed up)
            "--branch",
            self.source_spec.target,
            self.source_spec.url,
            dest_path,
        ]

        await Audit.submit("fetch_git", Audit.Type.Log, command=command)

        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env
        )  # git outputs updates over stderr

        await git_clone_progress(process, dest_path.name)

        if process.returncode == 0:
            await Audit.submit("clone_git", Audit.Type.Expected, dest=dest_path)
        else:
            await Audit.submit(
                "clone_git", Audit.Type.Unexpected, return_code=process.returncode
            )

        await asyncio.sleep(0.2)
        return process.returncode == 0


async def git_clone_progress(process, name):
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
                            re.sub(r"\s+", "", f"{name}-{m.group('label')}"),
                            f"|- {m.group('label')}",
                            int(m.group("total")),
                            int(m.group("progress")),
                            detail_level=Update.LevelOfDetail.ALWAYS_CLI_ONLY
                        )
                else:  # normal line
                    # TODO: work out when this occurs - on errors?
                    pass
            else:
                pass

        process.poll()
