from textual import on
from textual.screen import Screen, ModalScreen
import os

from textual.widgets import (
    Button,
    Markdown,
    Header,
    Collapsible,
    Static,
    Label,
    DirectoryTree,
    Footer,
    RadioSet,
    RadioButton,
    Input,
)
from textual.containers import (
    Container,
    Horizontal,
    VerticalScroll,
    HorizontalGroup,
    Grid,
)
from shoestring_assembler.model.installed import InstalledSolutionsModel
from textual.reactive import reactive
from pathlib import Path
from typing import Iterable
from shoestring_assembler.interface.signals import BackSignal
from shoestring_assembler.view.cli_app.components import BottomBar

INSTRUCTIONS = """
## Where do you want to download the solution to?
"""


class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        def meets_criteria(path):
            if path.name.startswith("."):
                return False  # ignore hidden files and folders
            if path.is_file():
                return False  # only show folders
            # return path.name == "recipe.toml"   # only show recipe.toml
            return True

        return [path for path in paths if meets_criteria(path)]


class DownloadLocation(Screen):
    CSS_PATH = "download.tcss"
    SUB_TITLE = "Choose Download Location"
    default_selected = reactive(True, recompose=True)
    path = reactive("",recompose=True)

    def __init__(self) -> None:
        super().__init__()
        self.default_location = os.getenv("HOME")

    def compose(self):
        yield Header(icon="⭕")
        yield Markdown(INSTRUCTIONS)
        yield Label("Download Location:")
        with VerticalScroll(can_focus=False):
            with HorizontalGroup():
                with RadioSet(id="radio_set"):
                    yield RadioButton("Default", id="default", value=self.default_selected)
                    yield RadioButton("Custom", value=not self.default_selected)
                if self.default_selected:
                    yield Label(self.default_location, classes="next_to_radio")
                else:
                    with HorizontalGroup(classes="next_to_radio"):
                        yield Input(value=str(self.path), id="custom_input")
                        yield Button("Choose",id="choose")
        yield BottomBar()
        yield Footer()

    @on(RadioSet.Changed)
    def handle_radio(self, event: RadioSet.Changed):
        radio = event.pressed
        self.default_selected = radio.id == "default"

    @on(Input.Blurred)
    def handle_input(self,event: Input.Blurred):
        self.path = event.value

    @on(Button.Pressed, "#continue")
    def select_add(self):
        if self.default_selected:
            self.dismiss(self.default_location)
        else:
            self.dismiss(self.path)

    @on(Button.Pressed,"#choose")
    def show_file_picker(self,_event):
        def set_path(value):
            self.path = value
        self.app.push_screen(FilePickerModal(), set_path)

    @on(Button.Pressed, "#back")
    def action_back(self):
        self.dismiss(BackSignal())


class FilePickerModal(ModalScreen):
    CSS_PATH = "modals.tcss"

    def __init__(self, *args, error_message="FATAL Error", **kwargs):
        super().__init__(*args, classes="modal_screen", **kwargs)
        self.error_message = error_message

    def compose(self):
        with Container(classes="modal_large file_picker"):
            yield FilteredDirectoryTree("/")
            yield RefreshableSelectedBar()
            yield Button("Select",variant="success",id="select_path")

    @on(DirectoryTree.DirectorySelected)
    def handle_file_selected(self,event:DirectoryTree.DirectorySelected):
        bar = self.query_one(RefreshableSelectedBar)
        bar.set_path(event.path)      

    @on(Button.Pressed, "#select_path")
    def handle_exit(self) -> None:
        bar = self.query_one(RefreshableSelectedBar)
        self.dismiss(bar.path)

class RefreshableSelectedBar(HorizontalGroup):
    path = reactive(Path("/"),recompose=True)
    def compose(self):
        yield Label(f"Selected: {str(self.path)}")

    def set_path(self,value):
        self.path = value
        self.mutate_reactive(RefreshableSelectedBar.path)
