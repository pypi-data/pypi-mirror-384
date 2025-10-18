from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule

import rich.progress
import os

from shoestring_assembler.interface.events import Update
from shoestring_assembler.constants import Constants
from pathlib import Path

PREFIX = "[grey58]> [/grey58]"


class Display:
    root_console = Console()
    alt_console = None
    file_console = Console(
        record=True, file=open(os.devnull, "wt"), color_system="truecolor", width=100
    )
    log_level = Update.LevelOfDetail.ALWAYS
    file_log_level = Update.LevelOfDetail.DEBUG

    @classmethod
    def print_top_header(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(
            console, Rule(f"[bold cyan]{text}", align="center"), log_level=log_level
        )

    @classmethod
    def print_header(cls, text, console=None, log_level=0):
        # console.rule(f"[bold bright_magenta]{text}", style="bright_magenta", align="center")
        cls.__tee_print(
            console, Panel(f"{text}", style="bright_magenta"), log_level=log_level
        )

    @classmethod
    def print_complete(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(
            console,
            Text.from_markup(f"{PREFIX}:white_check_mark:  {text}", style="green"),
            log_level=log_level,
        )

    @classmethod
    def print_notification(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(
            console,
            Panel(
                f"[bold bright_cyan]{text}[/bold bright_cyan]",
                title="[bold bright_cyan]:information:  Notification",
                title_align="left",
                style="bright_cyan",
            ),
            log_level=log_level,
        )

    @classmethod
    def print_next_steps(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(
            console,
            Panel(
                f"[bold bright_cyan]{text}[/bold bright_cyan]",
                title="[bold bright_cyan]:footprints:  Next Steps",
                title_align="left",
                style="bright_cyan",
            ),
            log_level=log_level,
        )

    @classmethod
    def print_warning(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(
            console,
            Panel(
                f"[bold yellow]{text}[/bold yellow]",
                title="[bold yellow]:warning:  Warning",
                title_align="left",
                style="yellow",
            ),
            log_level=log_level,
        )

    @classmethod
    def print_error(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(
            console,
            Panel(
                f"[bold red]{text}[/bold red]",
                title="[bold red]:warning:  Error",
                title_align="left",
                style="red",
            ),
            log_level=log_level,
        )

    @classmethod
    def print_log(cls, text, console=None, log_level=Update.LevelOfDetail.ALWAYS):
        cls.__tee_print(console, Text.from_markup(f"{PREFIX}{text}"), log_level=log_level)

    @classmethod
    def print_debug(cls, text, console=None, log_level=Update.LevelOfDetail.DEBUG):
        cls.__tee_print(
            console,
            Panel(
                f"[bold grey58]{text}[/bold grey58]",
                title="[bold grey58]Verbose log",
                title_align="left",
                style="grey58",
            ),
            log_level=log_level,
        )

    @classmethod
    def open_file(
        cls, file, *args, log_level=Update.LevelOfDetail.ALWAYS, description=None, **kwargs
    ):
        if log_level <= cls.file_log_level:
            cls.file_console.print(f"\[open_file] {file}")

        if log_level <= cls.log_level:
            if description:
                # add prefix and suffix padding
                description = f"{PREFIX}{description}".ljust(30, " ")
            return rich.progress.open(file, *args, description=description, **kwargs)
        else:
            return open(file, *args, **kwargs)

    @classmethod
    def __tee_print(cls, console, *args, log_level=Update.LevelOfDetail.ALWAYS, **kwargs):
        console = cls.__get_console(console)
        if log_level <= cls.log_level:
            console.print(*args, **kwargs)
        if log_level <= cls.file_log_level:
            cls.file_console.print(*args, **kwargs)

    @classmethod
    def __get_console(cls, console):
        if console:
            return console
        else:
            if cls.alt_console:
                return cls.alt_console
            else:
                return cls.root_console

    @classmethod
    def finalise_log(cls):
        cls.file_console.save_html(Constants.CONSOLE_LOG)


from rich.prompt import PromptBase, Confirm, InvalidResponse


# Options are presented using 1 index
class OptionPrompt(PromptBase):
    response_type = int
    validate_error_message = (
        "[prompt.invalid]Please enter the number for one of the options shown"
    )

    def __init__(self, *args, choices=[], **kwargs):
        self.choices_list = choices
        choice_prompts = [str(i) for i in range(1, len(choices) + 1)]
        super().__init__(*args, choices=choice_prompts,  **kwargs)

    def pre_prompt(self):
        for index, choice in enumerate(self.choices_list):
            Display.print_log(f"[magenta]({index+1})[/magenta] - {choice}")

class TailoredConfirm(Confirm):
    pass

class PathPrompt(PromptBase):
    response_type = str
    validate_error_message = (
        "[prompt.invalid]Please enter a valid filesystem path"
    )

    def process_response(self, value: str) -> bool:
        value = value.strip()
        try:
            path = Path(value)
            if not path.is_dir():
                raise InvalidResponse(
                    "[prompt.invalid]Please select a directory"
                )
        except:
            raise InvalidResponse(
                "[prompt.invalid]Please enter a valid filesystem path"
            )
        return path

    def check_choice(self, value):
        Display.print_log(value)
        if super().check_choice(value) == False:
            return False

    # on_validate_error #TODO can override here to tailor response or modify validate error message in check choice
