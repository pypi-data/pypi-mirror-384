from textual import on
from textual.screen import Screen
from textual.widgets import Button, Markdown, Header, Collapsible, Static, Label, Footer
from textual.containers import Container, HorizontalGroup, VerticalScroll, Middle
from shoestring_assembler.model.installed import InstalledSolutionsModel
from shoestring_assembler.model.solution import SolutionModel, VersionControl
from shoestring_assembler.interface.signals import Action, ActionSignal
from textual.message import Message
from textual.reactive import reactive

INSTRUCTIONS = """
## Welcome to the Shoestring Assembler
"""


class SolutionAction(Message):
    """Action selected message."""

    def __init__(self, signal: ActionSignal) -> None:
        self.signal = signal
        super().__init__()


class Home(Screen):
    CSS_PATH = "home.tcss"
    SUB_TITLE = "Select an Action"

    refresh_flag = reactive(bool, recompose=True)

    def __init__(self, installed_solutions: InstalledSolutionsModel) -> None:
        super().__init__()
        self.installed_solutions = installed_solutions
        self.run_worker(self.fetch_solution_status)

    def compose(self):
        yield Header(icon="⭕")
        yield Markdown(INSTRUCTIONS)
        with HorizontalGroup(id="download_bar"):
            with Middle():
                yield Label("Add a new Solution:")
            yield Button("Download", variant="primary", id="download")
            yield Button(
                "Find", id="find", tooltip="Find a solution that is already installed"
            )
        with VerticalScroll(can_focus=False):
            for solution in self.installed_solutions.solutions:
                match solution.status:
                    case SolutionModel.Status.RUNNING:
                        status_string = "[green] \[Running][/green]"

                    case SolutionModel.Status.STOPPED:
                        status_string = "[red] \[Stopped][/red]"

                    case SolutionModel.Status.UNKNOWN:
                        status_string = "[yellow] \[Status Unknown][/yellow]"
                with Collapsible(title=f"{solution.user_given_name} {status_string}"):
                    yield SolutionEntry(solution, classes="solution_action_dropdown")
        yield Footer()

    async def fetch_solution_status(self):
        await self.installed_solutions.check_running()
        self.refresh_flag = not self.refresh_flag

    @on(Button.Pressed, "#download")
    def select_download(self):
        self.dismiss(ActionSignal(Action.DOWNLOAD))

    @on(Button.Pressed, "#find")
    def select_find(self):
        self.dismiss(ActionSignal(Action.FIND))

    @on(SolutionAction)
    def handle_solution_action(self, action: SolutionAction):
        self.dismiss(action.signal)


class SolutionEntry(Container):
    refresh_flag = reactive(bool, recompose=True)

    def __init__(self, solution: SolutionModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.solution = solution

    def compose(self):
        if self.solution.saturated:
            yield Label(
                f"version: {self.solution.solution_details.version}       location:{self.solution.fs.root}"
            )
            with HorizontalGroup():
                yield Button("Assemble", variant="primary", id="assemble")
                yield Button("Check for updates", variant="primary", id="update")
                yield Button("Reconfigure", variant="primary", id="reconfigure")
            with HorizontalGroup():
                yield Button("Build", variant="primary", id="build")
                yield Button("Setup", variant="primary", id="setup")
            with HorizontalGroup():
                if self.solution.status != SolutionModel.Status.RUNNING:
                    yield Button("Start", variant="primary", id="start")
                if self.solution.status != SolutionModel.Status.STOPPED:
                    yield Button("Restart", variant="primary", id="restart")
                    yield Button("Stop", variant="primary", id="stop")
            with HorizontalGroup():
                yield Button("Edit", variant="primary", id="edit")
                yield Button("Remove", variant="primary", id="remove")
        elif not self.solution.fs.root_valid:
            yield Label(f"Not a valid solution installation:", classes="emphasis")
            yield Label(f"{self.solution.fs.root}")
            yield Button("Remove", variant="primary", id="remove")
        else:
            try:
                if self.solution.version_control.current_version:
                    yield Label(
                        "Installed version is not supported by this tool",
                        classes="emphasis",
                    )
                    yield Label(
                        f"version: {self.solution.version_control.current_version}\nlocation:{self.solution.fs.root}"
                    )
                    with HorizontalGroup():
                        yield Button("Check for updates", variant="primary", id="update")
                        yield Button("Remove", variant="primary", id="remove")

            except VersionControl.NotLoadedException:
                yield Label(f"location:{self.solution.fs.root}")
                yield Label("Loading version information...")
                self.run_worker(self.load_version_control, exclusive=False)

    async def load_version_control(self):
        if not self.solution.version_control.is_loaded:
            await self.solution.version_control.get_version_data()
            self.refresh_flag = not self.refresh_flag

    @on(Button.Pressed)
    def handle_button_press(self, message: Button.Pressed):
        button_id = message.button.id
        match button_id:
            case "assemble":
                action = Action.ASSEMBLE
            case "update":
                action = Action.UPDATE
            case "reconfigure":
                action = Action.RECONFIGURE
            case "build":
                action = Action.BUILD
            case "setup":
                action = Action.SETUP
            case "start":
                action = Action.START
            case "restart":
                action = Action.RESTART
            case "stop":
                action = Action.STOP
            case "remove":
                action = Action.REMOVE
            case "edit":
                action = Action.EDIT

        self.post_message(SolutionAction(ActionSignal(action, self.solution)))
