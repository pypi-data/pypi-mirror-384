from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input
from shoestring_assembler.interface.signals import BackSignal


class ConfirmModal(ModalScreen):
    CSS_PATH = "modals.tcss"

    """Screen to confirm something"""
    def __init__(self, *args, prompt="Continue?", **kwargs):
        super().__init__(*args, classes="modal_screen", **kwargs)
        self.prompt = prompt

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.prompt, id="prompt"),
            Button("Yes", variant="success", id="yes"),
            Button("No", variant="error", id="no"),
            classes="modal_dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class NewName(ModalScreen):
    CSS_PATH = "modals.tcss"

    """Screen to confirm something"""

    def __init__(self, solution,*args, **kwargs):
        super().__init__(*args, classes="modal_screen", **kwargs)
        self.solution = solution
        self.new_name = solution.user_given_name

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Edit deployment name", id="prompt"),
            Input(value=self.new_name, id="text_input"),
            Button("Save", variant="success", id="yes"),
            Button("Cancel", variant="error", id="no"),
            classes="modal_dialog modal_input",
        )

    @on(Input.Blurred)
    def handle_text_input(self, message: Input.Blurred):
        self.new_name = message.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(self.new_name)
        else:
            self.dismiss(BackSignal())


class FatalErrorModal(ModalScreen):
    CSS_PATH = "modals.tcss"
    def __init__(self, *args, error_message="FATAL Error", exit=True, **kwargs):
        super().__init__(*args, classes="modal_screen", **kwargs)
        self.error_message = error_message
        self.exit = exit

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.error_message, id="prompt"),
            Button("Exit", variant="error", id="exit"),
            classes="modal_dialog",
        )

    @on(Button.Pressed, "#exit") 
    def handle_exit(self) -> None:
        if self.exit:
            self.app.exit()
        else:
            self.dismiss("continue")
