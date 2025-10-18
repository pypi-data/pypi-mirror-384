from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Label,
    Markdown,
    Button,
    Footer,
    Select,
)
from textual.widgets._select import NoSelection
from textual.containers import VerticalScroll, VerticalGroup
from textual import on
from textual.reactive import reactive


from shoestring_assembler.view.cli_app.components import BottomBar


INSTRUCTIONS = """
### Select which solution you want to update to.
Use your mouse to click and scroll

or

Use `tab` and `shift + tab` to move between sections.
Use the `up` and `down` arrows to move up and down the list.
Use `Enter` to select the solution you want.
Press `esc` to go back.
"""

class UpdateVersionPicker(Screen):
    SUB_TITLE = "Select the Version to Update to"
    CSS_PATH = "solution_picker.tcss"

    refresh_flag = reactive(bool, recompose=True)

    def __init__(self, solution_model, **kwargs):
        super().__init__(**kwargs)
        self.available_versions = solution_model.available_updates
        self.solution_model = solution_model
        self.selected_version = self.available_versions[0]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(icon="⭕")
        with VerticalScroll(can_focus=False):
            yield Markdown(INSTRUCTIONS)
            yield VersionList(
                version_list=self.available_versions, selected=self.selected_version
            )
        yield BottomBar()
        yield Footer()

    @on(Button.Pressed, "#continue")
    def handle_selected(self, _event):
        self.solution_model.version_control.target_version = (
            self.selected_version
        )
        self.dismiss(self.selected_version)

    @on(Select.Changed)
    def handle_option_select(self, message: Select.Changed):
        if self.selected_version != message.value:
            if isinstance(message.value, NoSelection):
                self.selected_version = self.available_versions[0]
            else:
                self.selected_version = message.value
            self.refresh_flag = not self.refresh_flag


class VersionList(VerticalGroup):

    def __init__(self, *content, version_list=[], selected=None, **kwargs):
        super().__init__(*content, **kwargs)
        self.version_list = version_list
        self.selected = selected

    def compose(self):
        yield Label("Select which version to install:")

        list_entries = []
        for index, version in enumerate(self.version_list):
            if version == None:
                continue
            if index == 0:
                list_entries.append((f"{version} (latest)", version))
            else:
                list_entries.append((version, version))

        yield Select(
            list_entries,
            value=self.selected,
        )
