from textual import on
from textual.screen import Screen
from textual.widgets import (
    Button,
    Markdown,
    Header,
    OptionList,
    Input,
    Label,
    TabbedContent,
    TabPane,
    Footer,
    Select,
)
from textual.containers import (
    Container,
    HorizontalGroup,
    VerticalScroll,
    Middle,
    VerticalGroup,
)
from textual.reactive import reactive
from shoestring_assembler.model.prompts import Question
from shoestring_assembler.model.solution import SolutionModel
from shoestring_assembler.model.base_module import BaseModule
from shoestring_assembler.interface.signals import Action, ActionSignal, BackSignal
from shoestring_assembler.model.user_config import UserConfig
from textual.message import Message
from textual.events import Blur, DescendantBlur
from shoestring_assembler.display import Display
from shoestring_assembler.interface.events.audit import Audit
from shoestring_assembler.interface.events.updates import FatalError


INSTRUCTIONS = """
## Configure the solution
* Configure the solution by filling in the questions in each tab below
* Click continue when you're finished
"""


class SolutionAction(Message):
    """Action selected message."""

    def __init__(self, signal: ActionSignal) -> None:
        self.signal = signal
        super().__init__()


class ConfigInputs(Screen):
    CSS_PATH = "config.tcss"
    SUB_TITLE = "Configure Solution"
    AUTO_FOCUS = ""

    def __init__(self, solution_model: SolutionModel) -> None:
        super().__init__()
        self.solution_model = solution_model

    def compose(self):
        yield Header(icon="⭕")
        with HorizontalGroup():
            yield Markdown(INSTRUCTIONS, id="instructions")
            with Container(id="button_container"):
                yield Button("Cancel", id="back")
                yield Button("Continue", variant="success", id="continue")
        with TabbedContent():
            for service_module in self.solution_model.service_modules:
                with TabPane(id=service_module.name, title=service_module.name):
                    yield ServiceModuleEntry(
                        service_module, classes="module_entry", can_focus=False
                    )
        yield Footer()

    @on(Button.Pressed, "#continue")
    def select_download(self):
        self.dismiss("continue")

    @on(Button.Pressed, "#back")
    def select_find(self):
        self.dismiss(BackSignal())


class ServiceModuleEntry(VerticalScroll):
    refresh_flag = reactive(bool, recompose=True)

    def __init__(self, service_module: BaseModule, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_module = service_module
        self.last_changed = None

    def compose(self):
        name = self.service_module.name
        user_config = self.service_module.user_config
        status = user_config.status

        if status == UserConfig.Status.WARN_FUTURE:
            # TODO
            # Display.print_warning(
            #     f"Current user config version is {user_config.version} which is newer than the template version of {user_config.template.version}.\n"
            #     + f"[red]This might be ok! [/red] - but it should be checked!\n"
            #     + f"You can find the current user config files at [purple]./{user_config.rel_path}[/purple] and the template files at [purple]./{user_config.template.rel_path}[/purple]"
            # )
            pass

        self.border_title = f"\[{status}]"
        if status == UserConfig.Status.NO_TEMPLATE:
            yield Label("No user config for this service module")
            return

        user_config.requires_configuration = True
        prompts = user_config.template.prompts

        if not prompts.exists():
            yield Label("No user config prompts for this service module")
            return

        prompts.start(name, user_config.answer_context)
        Display.print_debug(f"Initialising Prompts: {prompts}")
        while question := prompts.next():
            Display.print_debug(
                f"question: {question}\n"
                + f"prompts_queue: {prompts}\n"
                + f"answers: {user_config.answers}"
            )
            match question:
                case Question.Select():
                    default = user_config.prompt_defaults.get(question.key)
                    answer = user_config.answers.get(question.key)
                    current_value = answer if answer else default if default else None

                    yield SelectQuestion(
                        question_id=question.id,
                        question_prompt=question.prompt,
                        choices=question.choices,
                        selected=current_value,
                    )
                case Question.Text():
                    default_value = user_config.prompt_defaults.get(question.key)
                    answer_value = user_config.answers.get(question.key)
                    real_value = (
                        answer_value
                        if answer_value
                        else default_value if default_value else None
                    )

                    yield TextQuestion(
                        question_id=question.id,
                        question_prompt=question.prompt,
                        value=str(real_value),
                    )
                case Question.Bool():
                    default_value = user_config.prompt_defaults.get(question.key)
                    answer_value = user_config.answers.get(question.key)
                    real_value = (
                        answer_value
                        if answer_value is not None
                        else default_value if default_value is not None else False
                    )

                    yield BoolQuestion(
                        question_id=question.id,
                        question_prompt=question.prompt,
                        value=real_value,
                    )

    def fix_focus(self):
        if self.last_changed:
            should_have_focus = self.query_one(f"#{self.last_changed}")
            should_have_focus.focus()

    @on(Button.Pressed, "#assemble")
    def select_download(self, message):
        self.post_message(SolutionAction(ActionSignal(Action.ASSEMBLE, self.solution)))

    @on(Select.Changed)
    def handle_option_select(self, message: Select.Changed):
        prompt_id = message.select.id
        value = message.value
        prompt = self.service_module.user_config.template.prompts.get(prompt_id)

        existing_answer = self.service_module.user_config.answers.get(prompt.key)
        if value != existing_answer:
            Display.print_debug(
                f"handle_option_select: {prompt_id}({prompt}) -> {value}"
            )
            self.service_module.user_config.answers[prompt.key] = value

            # Audit.submit(
            #     "select_option", Audit.Type.Expected, key=prompt.answer_key, value=value
            # )
            self.last_changed = prompt_id
            self.refresh_flag = not self.refresh_flag
            self.call_after_refresh(self.fix_focus)

    @on(Input.Blurred)
    def handle_text_input(self, message: Input.Blurred):
        prompt_id = message.input.id
        value = message.value
        prompt = self.service_module.user_config.template.prompts.get(prompt_id)
        self.service_module.user_config.answers[prompt.key] = value

        # Audit.submit("text_input", Audit.Type.Expected, key=prompt_id, value=value)
        self.last_changed = prompt_id

    @on(Button.Pressed)
    def handle_button_press(self, message: Button.Pressed):
        prompt_id = message.button.id
        value = message.button.variant == "error"

        prompt = self.service_module.user_config.template.prompts.get(prompt_id)
        self.service_module.user_config.answers[prompt.key] = value

        self.last_changed = prompt_id
        self.refresh_flag = not self.refresh_flag
        self.call_after_refresh(self.fix_focus)


class SelectQuestion(VerticalGroup):

    refresh_flag = reactive(bool, recompose=True)

    def __init__(
        self,
        *children,
        question_prompt="",
        choices=[],
        selected=None,
        question_id=None,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        markup=True,
    ):
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.prompt_text = question_prompt
        self.choices = choices
        self.selected = selected
        self.prompt_id = question_id

    def compose(self):
        yield Label(self.prompt_text)
        choice_list = [(prompt, key) for key, prompt in self.choices.items()]
        value = self.selected if self.selected is not None else choice_list[0][1]
        allowed_values = [key for _prompt, key in choice_list]
        if value not in allowed_values:
            raise FatalError(
                f"Select prompt {self.prompt_id} has invalid default value: {value}. Valid options are: {allowed_values}"
            )

        yield Select(
            choice_list,
            id=self.prompt_id,
            value=value,
        )


class TextQuestion(VerticalGroup):

    def __init__(
        self,
        *children,
        question_prompt="",
        value=None,
        question_id=None,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        markup=True,
    ):
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.question_prompt = question_prompt
        self.value = value
        self.question_id = question_id

    def compose(self):
        yield Label(self.question_prompt)
        yield Input(value=self.value, id=self.question_id)


class BoolQuestion(VerticalGroup):

    def __init__(
        self,
        *children,
        question_prompt="",
        value=None,
        question_id=None,
        name=None,
        id=None,
        classes=None,
        disabled=False,
        markup=True,
    ):
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.question_prompt = question_prompt
        self.value = value
        self.question_id = question_id

    def compose(self):
        yield Label(self.question_prompt)
        text = "Yes" if self.value == True else "No"
        variant = "success" if self.value == True else "error"

        yield Button(text, variant=variant, id=self.question_id)
