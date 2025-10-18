from textual.app import ComposeResult
from textual.widgets import Footer, RichLog, Button, ProgressBar, Label, Static
from textual.widgets import Input as TextualInput, Select
from textual.containers import (
    HorizontalGroup,
    VerticalGroup,
    VerticalScroll,
    Center,
    Middle,
    Container,
)
from textual import on
from textual.reactive import reactive
from textual.screen import Screen
from rich.text import Text
from rich.panel import Panel
from textual.events import Resize

import asyncio

from shoestring_assembler.display import Display
from rich.rule import Rule

from shoestring_assembler.interface.events.audit import Audit, AuditEvent
from shoestring_assembler.interface.events.progress import ProgressEvent, SectionEvent

from shoestring_assembler.interface.events import Update, Input
from textual.message import Message
from textual.binding import Binding


from shoestring_assembler.view.plain_cli.audit_events import audit_event_to_string


class PromptBase(Message):
    def __init__(self, future: asyncio.Future):
        super().__init__()
        self.future = future

    def yes(self):
        self.future.set_result(True)

    def no(self):
        self.future.set_result(False)


class ContinuePrompt(PromptBase):
    pass


class BuildPrompt(PromptBase):
    pass


class StartPrompt(PromptBase):
    pass


class EngineScreen(Screen):
    CSS_PATH = "engine.tcss"

    BINDINGS = {
        Binding(
            key="l",
            action="toggle_show_log",
            description="Show/Hide detailed logs",
            key_display="l",
        ),
    }

    def action_toggle_show_log(self):
        self.query_one(LogSection).toggle_show()

    def __init__(self, update_receiver, name=None, id=None, classes=None):
        super().__init__(name, id, classes)
        self.update_receiver = update_receiver

    def compose(self) -> ComposeResult:
        with Container(id="main_wrapper"):
            with Container(id="stage_log_wrapper"):
                yield Label("Progress:", id="progress_label")
                yield StageLog()
            yield LogSection()
        yield PromptWrapper()
        yield Footer()

    def _on_mount(self, event):
        self.run_worker(self.update_listener())

    def trigger_audit_msg(self, audit_event: AuditEvent):
        self.write_audit_msg(audit_event)

    def write_audit_msg(self, audit_event):
        content = audit_event_to_string(audit_event)
        match audit_event.type:
            case Audit.Type.Expected:
                Display.print_log(content)
            case Audit.Type.Unexpected:
                Display.print_error(content)
            case Audit.Type.Log:
                Display.print_debug(content)

    def handle_input_request(self, msg: Input.Request):
        stage_log: StageLog = self.query_one(StageLog)
        stage_log.add_update(msg)
        Display.print_log(f"[input] {msg.prompt}")

    def notify_fn(self, msg: Update.Event):
        stage_log: StageLog = self.query_one(StageLog)
        match (msg.type):
            case Update.Type.STAGE:
                stage_log.clear()
                stage_log.add_update(msg)
                Display.print_top_header(msg.content)

            case Update.Type.STEP:
                stage_log.add_update(msg)
                Display.print_header(msg.content)

            case Update.Type.INFO:
                Display.print_log(msg.content, log_level=msg.lod)
                if msg.lod == Update.LevelOfDetail.ALWAYS:
                    stage_log.add_update(msg)

            case Update.Type.WARNING:
                Display.print_warning(msg.content)

            case Update.Type.ERROR:
                Display.print_error(msg.content)
                stage_log.add_update(msg)

            case Update.Type.SUCCESS:
                stage_log.add_update(msg)
                Display.print_complete(msg.content)

            case Update.Type.NOTIFY:
                stage_log.add_update(msg)
                self.app.notify(msg.content)
                Display.print_complete(msg.content)

            case Update.Type.DEBUG:
                Display.print_debug(msg.content)

            case Update.Type.ATTENTION:
                Display.print_notification(msg.content)

            case _:
                Display.print_log(msg)

    def create_progress_section(self, msg: SectionEvent):
        stage_log: StageLog = self.query_one(StageLog)
        stage_log.handle_progress_section(msg)

    def diplay_progress_update(self, progress_event: ProgressEvent):
        stage_log: StageLog = self.query_one(StageLog)
        if progress_event.detail_level <= Update.LevelOfDetail.ALWAYS:
            stage_log.handle_progress_update(progress_event)
        Display.print_log(
            f"\[progress] {progress_event.label} {progress_event.value}/{progress_event.total}"
        )

    async def update_listener(self):
        while True:
            msg = await self.update_receiver.recv()
            match msg:
                case AuditEvent():
                    self.trigger_audit_msg(msg)
                case ProgressEvent():
                    self.diplay_progress_update(msg)
                case Update.Event():
                    self.notify_fn(msg)
                case SectionEvent():
                    self.create_progress_section(msg)
                case Input.Request():
                    self.handle_input_request(msg)
                case _:
                    raise Exception(msg)

    @on(PromptBase)
    def handle_can_contiue(self, prompt: PromptBase):
        wrapper: PromptWrapper = self.query_one(PromptWrapper)
        wrapper.current_prompt = prompt


class RichLogConsoleWrapper:
    def __init__(self, rich_log):
        self.rich_log = rich_log

    def print(self, msg):
        self.rich_log.write(msg)

    def rule(self, *args, **kwargs):
        rule = Rule(*args, **kwargs)
        self.print(rule)


class PromptWrapper(HorizontalGroup):
    current_prompt: PromptBase = reactive(None, recompose=True)

    def compose(self):
        match self.current_prompt:
            case ContinuePrompt():
                yield Button("Continue", variant="success", id="continue")
            case BuildPrompt():
                yield Label(
                    "Do you want to build the solution now?", classes="prompt_label"
                )
                yield Button("No", variant="error", id="cancel")
                yield Button("Yes", variant="success", id="continue")
            case StartPrompt():
                yield Label(
                    "Do you want to start the solution now?", classes="prompt_label"
                )
                yield Button("No", variant="error", id="cancel")
                yield Button("Yes", variant="success", id="continue")
            case None:
                yield Static("")

    @on(Button.Pressed)
    def handle_continue(self, event: Button.Pressed):

        if event.button.id == "continue":
            self.current_prompt.yes()
        else:
            self.current_prompt.no()

        self.current_prompt = None


class StageLog(VerticalScroll):
    refresh_flag = reactive(bool, recompose=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contents = {}
        self.id_counter = 0
        self.select_options = {}

    def compose(self):
        for key, entry in self.contents.items():
            match entry:
                case ProgressEvent():
                    # yield Label(f"{entry.label} {entry.value}/{entry.total}")
                    with HorizontalGroup(classes="progress_group"):
                        yield Label(entry.label)
                        bar = ProgressBar(
                            id=entry.key, total=entry.total, show_eta=False
                        )
                        bar.progress = entry.value
                        yield bar
                case Update.Event():
                    match entry.type:
                        case Update.Type.STAGE:
                            yield Label(f"{entry.content}", classes="stage_header")
                        case Update.Type.STEP:
                            yield Label(f"- {entry.content}", classes="step_header")
                        case Update.Type.SUCCESS:
                            yield Label(
                                Text.from_markup(
                                    f":white_check_mark:  {entry.content}",
                                    style="green",
                                )
                            )
                        case Update.Type.INFO:
                            yield Label(
                                Text.from_markup(f"[white] {entry.content} [/white]")
                            )
                        case Update.Type.ERROR:
                            yield Label(f"{entry.content}", classes="error_msg")
                case Input.Request():
                    match entry.variant:
                        case Input.Request.Variant.TEXT:
                            yield Label(
                                f"\[input] {entry.prompt}:", classes="input_msg"
                            )
                            if not entry.resolved:
                                yield TextualInput(name=key)
                            else:
                                yield Label(f"\[answered]", classes="answered_msg")
                        case Input.Request.Variant.CONTINUE:
                            yield Label(f"\[input] {entry.prompt}", classes="input_msg")
                            if not entry.resolved:
                                yield Button(
                                    "Continue",
                                    variant="success",
                                    name=key,
                                    classes="continue_button",
                                )
                        case Input.Request.Variant.CONFIRM:
                            yield Label(f"\[input] {entry.prompt}", classes="input_msg")
                            if not entry.resolved:
                                with HorizontalGroup():
                                    yield Button(
                                        "Yes",
                                        variant="success",
                                        name=key,
                                        classes="yes_button",
                                    )
                                    yield Button(
                                        "No",
                                        variant="error",
                                        name=key,
                                        classes="no_button",
                                    )
                            else:
                                yield Label(f"\[{'Yes' if entry.answer == 'y' else 'No'}]")
                        case Input.Request.Variant.SELECT:
                            yield Label(f"\[input] {entry.prompt}", classes="input_msg")
                            options_list = [
                                (label, k) for k, label in entry.options.items()
                            ]
                            with HorizontalGroup(classes="select_group"):
                                if not entry.resolved:
                                    yield Select(
                                        options_list,
                                        name=key,
                                        classes="select_input",
                                    )
                                    yield Button(
                                            "Select",
                                            name=key,
                                            classes="select_button",
                                        )
                                else:
                                    yield Label(f"\[selected] {entry.options.get(entry.answer,entry.answer)}", classes="answered_msg")

        self.scroll_end(animate=False)

    @on(Select.Changed)
    def handle_select_changed(self, event: Select.Changed):
        self.select_options[event.select.name] = event.value

    @on(Button.Pressed, ".select_button")
    def handle_select_pressed(self, event: Button.Pressed):
        key = event.button.name
        if key in self.select_options:
            self.handle_input_result(key, self.select_options[key])

    @on(Button.Pressed, ".continue_button")
    def handle_continue_pressed(self, event: Button.Pressed):
        self.handle_input_result(event.button.name, "continue")

    @on(Button.Pressed, ".yes_button")
    def handle_yes_pressed(self, event: Button.Pressed):
        self.handle_input_result(event.button.name, "y")

    @on(Button.Pressed, ".no_button")
    def handle_no_pressed(self, event: Button.Pressed):
        self.handle_input_result(event.button.name, "n")

    @on(TextualInput.Submitted)
    def handle_input_submitted(self, event: TextualInput.Submitted):
        self.handle_input_result(event.input.name, event.value)

    def handle_input_result(self, key, output):
        input_request = self.contents.get(key)
        if isinstance(input_request, Input.Request):
            input_request.resolve(output)

    def handle_progress_section(self, msg: SectionEvent):
        pass

    def clear(self):
        self.contents = {}
        self.refresh_flag = not self.refresh_flag

    def set_progress(self):
        # import time
        # time.sleep(2)
        for bar_id, entry in self.contents.items():
            if not isinstance(entry, ProgressEvent):
                continue
            try:
                bar: ProgressBar = self.query_one(f"#{bar_id}")
                bar.progress = entry.value
            except:
                pass

    def handle_progress_update(self, event: ProgressEvent):
        self.contents[event.key] = event
        self.refresh_flag = not self.refresh_flag

    def add_update(self, event):
        self.contents[f"{self.id_counter}"] = event
        self.id_counter += 1
        self.refresh_flag = not self.refresh_flag


class LogSection(VerticalGroup):
    shown = reactive(False, recompose=False)

    def compose(self):
        yield Label(
            "Detailed Log:",
            id="detailed_log_label",
            classes="shown" if self.shown else "hidden",
        )
        log = RichLog(wrap=True, classes="shown" if self.shown else "hidden")
        yield log
        wrapped_console = RichLogConsoleWrapper(log)
        Display.alt_console = wrapped_console

    @on(Button.Pressed, "#do_show")
    def toggle_show(self):
        self.shown = not self.shown

        label = self.query_one("#detailed_log_label")
        label.classes = "shown" if self.shown else "hidden"

        log = self.query_one(RichLog)
        log.classes = "shown" if self.shown else "hidden"

        if self.shown:
            self.remove_class("no_border")
            self.add_class("border")
        else:
            self.remove_class("border")
            self.add_class("no_border")
