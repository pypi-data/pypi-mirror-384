from textual.containers import HorizontalGroup
from textual.widgets import Button
from textual import on
from shoestring_assembler.interface.signals import BackSignal


class BottomBar(HorizontalGroup):
    def __init__(self, *args, classes="", show_continue=True, **kwargs):
        super().__init__(*args, classes=f"bottom_bar {classes}", **kwargs)
        self.show_continue = show_continue

    def compose(self):
        if self.show_continue:
            yield Button("Continue", variant="success", id="continue")
        yield Button.error("Cancel", id="back")

    @on(Button.Pressed, "#back")
    def action_back(self):
        self.screen.dismiss(BackSignal())
