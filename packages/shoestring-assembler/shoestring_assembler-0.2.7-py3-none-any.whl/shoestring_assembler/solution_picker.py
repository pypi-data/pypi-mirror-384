from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, OptionList, Label, Markdown, Button
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets.option_list import Option
from textual import on
from textual.reactive import reactive

import urllib.request
import yaml

from .git import GetSolutionUsingGit

INSTRUCTIONS = """
### Select which solution you want to download.
Use your mouse to click and scroll

or

Use `tab` and `shift + tab` to move between sections.
Use the `up` and `down` arrows to move up and down the list.
Use `Enter` to select the solution you want.
Press `q` to exit.
"""


class SolutionList(OptionList):
    def __init__(self, *content, provider=None, solution_list={},do_focus=False, **kwargs):
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

class VersionList(OptionList):

    def __init__(self, *content,version_list=[], **kwargs):
        super().__init__(*content, **kwargs)
        self.version_list = version_list

    def on_mount(self):
        self.app.set_focus(self)
        for index, version in enumerate(self.version_list):
            self.add_option(Option(version,id=version))
        return super().on_mount()


class SolutionPickerApp(App):
    CSS_PATH = "layout.tcss"
    stage = reactive(1, recompose=True)

    def __init__(self, provider_list, **kwargs):
        super().__init__(**kwargs)
        self.provider_list = provider_list
        self.available_versions = []

    BINDINGS = [("q", "exit", "Exit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        is_first = True
        yield Header(icon="⭕")
        with VerticalScroll():
            if self.stage == 1:
                yield Markdown(INSTRUCTIONS)
                for tag, values in self.provider_list["providers"].items():
                    yield Label(values["name"])
                    yield SolutionList(
                        provider=tag,
                        solution_list=values["solutions"],
                        do_focus=is_first,
                    )
                    is_first = False
            elif self.stage == 2:
                yield Markdown(INSTRUCTIONS)
                yield VersionList(version_list=self.available_versions)
        with Vertical(classes="bottom_bar"):
            yield Button.error("Exit",id="exit")

    def on_mount(self):
        self.title = "Select a Shoestring Solution"

    @on(Button.Pressed)
    def handle_buttons(self,button):
        self.exit()

    def action_exit(self) -> None:
        self.exit()

    @on(OptionList.OptionSelected)
    def handle_selected(self, event):
        if isinstance(event.option_list,SolutionList): 
            id = event.option.id
            provider, index = id.split("@")
            result = self.provider_list["providers"][provider]["solutions"][int(index)]
            self.selected_solution = result
            self.available_versions = GetSolutionUsingGit.available_versions(result["url"], result.get("minimum_version"))
            self.stage = 2
        elif isinstance(event.option_list,VersionList):
            self.exit({**self.selected_solution, "version": event.option.id})


if __name__ == "__main__":
    # fetch solution list
    with urllib.request.urlopen(
        "https://github.com/DigitalShoestringSolutions/solution_list/raw/refs/heads/main/list.yaml"
    ) as web_in:
        content = web_in.read()
        provider_list = yaml.safe_load(content)
    result = SolutionPickerApp(provider_list).run()
    print(result)
