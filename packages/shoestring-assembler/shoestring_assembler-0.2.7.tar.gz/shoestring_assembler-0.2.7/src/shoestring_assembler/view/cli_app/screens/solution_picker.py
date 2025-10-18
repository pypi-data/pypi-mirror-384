from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    OptionList,
    Label,
    Markdown,
    Button,
    Footer,
    Select
)
from textual.widgets._select import NoSelection
from textual.containers import HorizontalGroup, VerticalScroll, VerticalGroup
from textual.widgets.option_list import Option
from textual import on
from textual.reactive import reactive
from rich.text import Text


from shoestring_assembler.view.cli_app.components import BottomBar

import urllib.request
import yaml

INSTRUCTIONS = """
### Select which solution you want to download.
Use your mouse to click and scroll

or

Use `tab` and `shift + tab` to move between sections.
Use the `up` and `down` arrows to move up and down the list.
Use `Enter` to select the solution you want.
Press `esc` to go back.
"""


class SolutionList(OptionList):
    def __init__(
        self, *content, provider=None, solution_list={}, do_focus=False, **kwargs
    ):
        super().__init__(*content, **kwargs)
        self.solution_list = solution_list
        self.provider = provider
        self.do_focus = do_focus

    def on_mount(self):
        if self.do_focus:
            self.app.set_focus(self)
        for index, solution in enumerate(self.solution_list):
            self.add_option(Option(solution["name"], id=f"{self.provider}@{index}"))
        return super().on_mount()


class SolutionPicker(Screen):
    SUB_TITLE = "Select the Solution to Download"
    CSS_PATH = "solution_picker.tcss"

    def __init__(self, provider_list, **kwargs):
        super().__init__(**kwargs)
        self.provider_list = provider_list
        self.available_versions = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        is_first = True
        yield Header(icon="⭕")
        with VerticalScroll(can_focus=False):
            yield Markdown(INSTRUCTIONS)
            for tag, values in self.provider_list["providers"].items():
                yield Label(
                    Text.from_markup(f"Provider: [green]{values['name']}[/green]")
                )
                yield SolutionList(
                    provider=tag,
                    solution_list=values["solutions"],
                    do_focus=is_first,
                )
                is_first = False
        yield BottomBar(show_continue=False)
        yield Footer()

    @on(OptionList.OptionSelected)
    def handle_selected(self, event):
        id = event.option.id
        provider, index = id.split("@")
        result = self.provider_list["providers"][provider]["solutions"][int(index)]
        self.dismiss(result)



class SolutionVersionPicker(Screen):
    SUB_TITLE = "Select the Version to Download"
    CSS_PATH = "solution_picker.tcss"

    refresh_flag = reactive(bool, recompose=True)

    def __init__(self, available_versions, **kwargs):
        super().__init__(**kwargs)
        self.available_versions = available_versions
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

    @on(Button.Pressed,"#continue")
    def handle_selected(self, _event):
        self.dismiss(self.selected_version)

    @on(Select.Changed)
    def handle_option_select(self, message: Select.Changed):
        if self.selected_version != message.value:
            if isinstance(message.value,NoSelection):
                self.selected_version = self.available_versions[0]
            else:
                self.selected_version = message.value
            self.refresh_flag = not self.refresh_flag



# class VersionList(OptionList):

#     def __init__(self, *content, version_list=[], **kwargs):
#         super().__init__(*content, **kwargs)
#         self.version_list = version_list

#     def on_mount(self):
#         self.app.set_focus(self)
#         for index, version in enumerate(self.version_list):
#             self.add_option(Option(version, id=version))
#         return super().on_mount()


class VersionList(VerticalGroup):

    def __init__(self, *content, version_list=[], selected=None, **kwargs):
        super().__init__(*content, **kwargs)
        self.version_list = version_list
        self.selected = selected

    def compose(self):
        yield Label("Select which version to install:")

        list_entries = []
        for index, version in enumerate(self.version_list):
            if index == 0:
                list_entries.append((f"{version} (latest)", version))
            else:
                list_entries.append((version, version))

        yield Select(
            list_entries,
            value=self.selected,
        )
