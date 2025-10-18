from textual import on
from textual.screen import Screen
from textual.widgets import (
    Button,
    Markdown,
    Header,
    Collapsible,
    Static,
    Label,
    DirectoryTree,
    Footer
)
from textual.containers import Container, Horizontal, VerticalScroll
from shoestring_assembler.model.installed import InstalledSolutionsModel
from textual.reactive import reactive
from pathlib import Path
from typing import Iterable
from shoestring_assembler.interface.signals import BackSignal

INSTRUCTIONS = """
## Find an already installed solution
Navigate through the file system and select the `recipe.toml` file for the solution you want to add.
"""


class FilteredDirectoryTree(DirectoryTree):
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        def meets_criteria(path):
            if path.name.startswith("."):
                return False    # ignore hidden files and folders
            return True
            # if path.is_dir():
            #     return True     # show all remaining folders
            # return path.name == "recipe.toml"   # only show recipe.toml
        return [
            path
            for path in paths
            if meets_criteria(path)
        ]


class SelectBar(Container):
    selected = reactive(None, recompose=True)

    def compose(self):
        with Horizontal():
            yield Label("" if self.selected is None else str(self.selected))
            yield Button("Add", disabled=self.selected == None, id="add")
            yield Button("Back", id="back")


class Find(Screen):
    # CSS_PATH = "select_action.tcss"
    SUB_TITLE = "Find an installed solution"

    def __init__(self) -> None:
        super().__init__()
        self.selected = None

    def compose(self):
        yield Header(icon="⭕")
        yield Markdown(INSTRUCTIONS)
        yield FilteredDirectoryTree("/")
        yield SelectBar(id="selected")
        yield Footer()

    @on(DirectoryTree.FileSelected)
    def handle_file_selected(self,event:DirectoryTree.FileSelected):
        if event.path.name == "recipe.toml":
            self.query_one("#selected").selected = event.path
            self.selected = event.path

    @on(Button.Pressed, "#add")
    def select_add(self):
        self.dismiss(self.selected)

    @on(Button.Pressed,"#back")
    def action_back(self):
        self.dismiss(BackSignal())
