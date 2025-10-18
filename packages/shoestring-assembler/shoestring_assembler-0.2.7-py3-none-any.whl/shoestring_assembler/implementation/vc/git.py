import rich.progress
from pathlib import Path
import subprocess
import re
import select
import os

from shoestring_assembler.interface.events import Update, Audit


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shoestring_assembler.model.solution import SolutionModel

class SolutionGitVC:
    head_search_regex = re.compile("[^/](?P<has_head>HEAD)")  # TODO: may need some work
    tag_search_regex = re.compile("(?:tag:\s?(?P<tag>[\w\d\.-]*))")
    strict_tag_regex = re.compile("^v\d*\.\d*\.\d*$")

    @classmethod
    async def _fetch_updates(cls,solution_model: 'SolutionModel'):
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = (
            "0"  # prevents hanging on username input if url invalid
        )

        # fetch updates
        command = [
            "git",
            "-C",
            str(solution_model.fs.root),
            "fetch",
            "--progress",
            "--all",
        ]

        await Audit.submit("solution::get_versions_git::command",Audit.Type.Log,command = " ".join(command))

        await Update.InfoMsg("Fetching list of available versions...", detail_level=Update.LevelOfDetail.FEEDBACK)
        result = subprocess.run(command, capture_output=True, env=env)
        await Audit.submit("solution::get_versions_git::result",Audit.Type.from_boolean(result.returncode == 0),return_code = result.returncode, stdout = result.stdout.decode(), stderr = result.stderr.decode())

        if result.returncode != 0:
            await Update.WarningMsg(
                "Unable to fetch the latest list of available versions"
            )

    @classmethod
    async def fetch_version_details(
        cls, solution_model: 'SolutionModel', strict_tags_only=True, full_list=True
    ):
        await cls._fetch_updates(solution_model)

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = (
            "0"  # prevents hanging on username input if url invalid
        )

        # get current version
        command = [
            "git",
            "-C",
            str(solution_model.fs.root),
            "describe",
            "--exact-match",
            "--tags",
        ]
        result = subprocess.run(command, capture_output=True, env=env)
        current_version = result.stdout.decode().strip()

        # check tags
        command = [
            "git",
            "-C",
            str(solution_model.fs.root),
            "log",
            "--all",  # include all commits
            '--format="%D"',  # print list of commit refs (includes HEAD, tags and branches)
            "--simplify-by-decoration",  # filter out commits that have empty ref entries
        ]
        result = subprocess.run(command, capture_output=True, env=env)
        readout = result.stdout.decode()

        tag_entries = []
        for line in readout.split("\n"):
            has_head = cls.head_search_regex.search(line)
            tags = cls.tag_search_regex.findall(line)

            if strict_tags_only:
                tags = [tag for tag in tags if cls.strict_tag_regex.match(tag)]

            if tags:
                tag_entries.extend(
                    [
                        {
                            "has_head": has_head is not None,
                            "tag": tag,
                        }
                        for tag in tags
                    ]
                )
            elif has_head:
                tag_entries.append(
                    {
                        "has_head": has_head is not None,
                        "tag": None,
                    }
                )

        await Audit.submit("solution::parse_versions",Audit.Type.Log,raw=readout, extracted = tag_entries)
        first_current = None
        for index, entry in enumerate(tag_entries):
            is_current = (
                entry["tag"] == current_version
                if current_version
                else entry["has_head"]
            )
            if is_current:
                first_current = index
                break

        current_version = (
            current_version if current_version else None
        )  # converts "" to None
        available_updates = [entry["tag"] for entry in tag_entries[0:first_current]]
        
        return current_version, available_updates

    @classmethod
    async def do_update(cls,solution_model, tag_or_branch):

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = (
            "0"  # prevents hanging on username input if url invalid
        )

        command = ["git", "-C", str(solution_model.fs.root), "checkout", tag_or_branch]

        await Audit.submit("update",Audit.Type.Log,command = command)

        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env
        )  # git outputs updates over stderr

        # likely overkill but would be good to be able to relay updates
        buffer = bytearray()
        while process.returncode == None:
            while True:
                line = None

                read_list, _wlist, _xlist = select.select([process.stderr], [], [], 1)
                if process.stderr in read_list:
                    char = process.stderr.read(1)
                    if char == b"\n":
                        line = buffer.decode()
                        buffer.clear()
                    elif char:
                        buffer += char
                    else:
                        break  # end of file
                else:
                    break  # timeout - break to check if process terminated

                if line:
                    await Update.InfoMsg(f"[white]{line}")
                else:
                    pass

            process.poll()

        if process.returncode == 0:
            await Update.SuccessMsg("Update Complete.")
        else:
            await Update.ErrorMsg("Update failed.")

        return process.returncode == 0
