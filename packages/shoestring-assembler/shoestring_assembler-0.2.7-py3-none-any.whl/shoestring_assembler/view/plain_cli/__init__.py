from rich.prompt import Prompt
from rich.progress import Progress as RichProgress
from shoestring_assembler.display import (
    Display,
    OptionPrompt,
    TailoredConfirm,
    PathPrompt,
)
from shoestring_assembler.interface.state_machine import steps
from shoestring_assembler.interface.events.audit import Audit, AuditEvent
from shoestring_assembler.interface.events.progress import ProgressEvent, SectionEvent

from shoestring_assembler.interface.events import Update, FatalError, Input
from shoestring_assembler.engine.engine import Engine
from shoestring_assembler.interface.pipe import pipe
from pathlib import Path


from shoestring_assembler.model import SolutionModel, UserConfig
from shoestring_assembler.model.prompts import Question

from .audit_events import audit_event_to_string

import sys
from shoestring_assembler.interface.signals import ActionSignal
import asyncio
import traceback


class PlainCLI:

    def __init__(self, action):
        self.ui_pipe, engine_pipe = pipe.duplex()
        self.update_receiver, update_sender = pipe.simplex()
        self.engine = Engine(engine_pipe, update_sender)
        self.do_prompt_for_next_phase = True
        self.action = action

        self.progress_manager = None
        self.progress_task_map = {}

    def diplay_audit_msg(self, audit_event: AuditEvent):
        content = audit_event_to_string(audit_event)
        match audit_event.type:
            case Audit.Type.Expected:
                Display.print_log(content)
            case Audit.Type.Unexpected:
                Display.print_error(content)
            case Audit.Type.Log:
                Display.print_debug(content)

    def handle_input_request(self, request: Input.Request):
        match request.variant:
            case Input.Request.Variant.CONTINUE:
                result = Prompt.ask(f"{request.prompt} \[press enter to continue]")
                Display.print_debug(f"\[continued]")
            case Input.Request.Variant.CONFIRM:
                result = Prompt.ask(
                   request.prompt, choices=["y", "n"], default="y"
                )
                Display.print_debug(f"\[confirmed] {result}")
            case Input.Request.Variant.SELECT:
                selected = OptionPrompt.ask(request.prompt, choices=list(request.options.values()))
                result = list(request.options.keys())[selected - 1]
                Display.print_debug(f"\[selected] {result}")
            case _:
                result = Prompt.ask(request.prompt)
                Display.print_debug(f"\[answered] {result}")
        request.resolve(result)

    def create_progress_section(self, msg: SectionEvent):
        if msg.entered:
            self.progress_manager = (
                RichProgress()
            )  # TODO presentation - can use fields to include a label rather than a 0/3
            self.progress_manager.start()
            Display.alt_console = self.progress_manager.console
        else:
            self.progress_manager.stop()
            Display.alt_console = None
            self.progress_manager = None

    def diplay_progress_update(self, progress_event: ProgressEvent):
        if self.progress_manager is not None:
            if (
                self.progress_task_map.get(progress_event.key)
                not in self.progress_manager.task_ids
            ):
                task_id = self.progress_manager.add_task(
                    progress_event.label,
                    total=progress_event.total,
                    completed=progress_event.value,
                )
                self.progress_task_map[progress_event.key] = task_id

            task_id = self.progress_task_map[progress_event.key]
            self.progress_manager.update(task_id, completed=progress_event.value)

        # if progress_event.value == progress_event.total:
        # self.progress_manager.stop_task(task_id)
        # self.progress_manager.remove_task(task_id)
        else:
            Display.print_warning("Progress update without a progress section running")

    def notify_fn(self, msg: Update.Event):
        match (msg.type):
            case Update.Type.STAGE:
                Display.print_top_header(msg.content)

            case Update.Type.STEP:
                Display.print_header(msg.content)

            case Update.Type.INFO:
                Display.print_log(msg.content, log_level=msg.lod)

            case Update.Type.WARNING:
                Display.print_warning(msg.content)

            case Update.Type.ERROR:
                Display.print_error(msg.content)

            case Update.Type.SUCCESS:
                Display.print_complete(msg.content)

            case Update.Type.NOTIFY:
                Display.print_complete(msg.content)

            case Update.Type.DEBUG:
                Display.print_debug(msg.content)

            case Update.Type.ATTENTION:
                Display.print_notification(msg.content)

            case _:
                Display.print_log(msg)

    def handle(self, step):
        match (step):
            case steps.ChooseSolution():
                if len(step.provider_list) > 1:
                    key_list = []
                    name_list = []
                    for provider_key, provider_details in step.provider_list[
                        "providers"
                    ].items():
                        key_list.append(provider_key)
                        name_list.append(provider_details["name"])

                    provider_index = OptionPrompt.ask(
                        "select a provider", choices=name_list
                    )
                    provider = key_list[provider_index - 1]
                else:
                    provider = list(step.provider_list["providers"].keys())[0]

                solution_list = step.provider_list["providers"][provider]["solutions"]
                solution_index = OptionPrompt.ask(
                    "Select a solution",
                    choices=[solution["name"] for solution in solution_list],
                )
                solution = solution_list[solution_index - 1]
                return solution
            case steps.ChooseSolutionVersion():
                version_index = OptionPrompt.ask(
                    "Select a version", choices=step.version_list, default=1
                )
                return step.version_list[version_index - 1]
            case steps.ChooseDownloadLocation():
                location = PathPrompt.ask(
                    "Where do you want to download the solution to?",
                    default=str(Path.cwd()),
                )
                return location
            case steps.SelectUpdateVersion():
                Display.print_log("Which version do you want to update to?")
                version_index = OptionPrompt.ask(
                    "Select a version",
                    choices=self.engine.solution_model.available_updates,
                    default=1,
                )
                self.engine.solution_model.version_control.target_version = (
                    self.engine.solution_model.available_updates[version_index - 1]
                )
                return "continue"
            case steps.GetConfigurationInputs():
                reconfiguring = step.ignore_existing_setup or True

                for service_module in self.engine.solution_model.service_modules:
                    Display.print_header(
                        f"Setting up user config for {service_module.name}"
                    )

                    user_config = service_module.user_config
                    status = user_config.status

                    def log_status(outcome, colour="green"):
                        Display.print_log(
                            f"[{colour}]\[{outcome}][/{colour}] [white]{service_module.name}"
                        )

                    if status == UserConfig.Status.NO_TEMPLATE:
                        log_status(status)
                        continue

                    if not reconfiguring:
                        match (status):
                            case UserConfig.Status.WARN_FUTURE:
                                log_status("warning", "yellow")
                                Display.print_warning(
                                    f"Current user config version is {user_config.version} which is newer than the template version of {user_config.template.version}.\n"
                                    + f"[red]This might be ok! [/red] - but it should be checked!\n"
                                    + f"You can find the current user config files at [purple]./{user_config.rel_path}[/purple] and the template files at [purple]./{user_config.template.rel_path}[/purple]"
                                )
                                continue
                            case UserConfig.Status.MINOR_UPDATE:
                                log_status(status)
                                continue  # minor updates don't need reconfiguration
                            case UserConfig.Status.UP_TO_DATE:
                                log_status(status)
                                continue  # up to date - no config to be done
                            case _:
                                log_status(status)
                    else:
                        log_status("reconfigure")

                    user_config.requires_configuration = True
                    prompt_list = user_config.template.prompts

                    if prompt_list is None:
                        pass
                    else:
                        prompt_list.start("", user_config.answer_context)
                        while question := prompt_list.next(user_config.answer_context):
                            match question:
                                case Question.Select():
                                    default_value = user_config.prompt_defaults.get(
                                        question.key
                                    )

                                    choice_keys = list(question.choices.keys())
                                    choice_values = list(question.choices.values())

                                    default_index = (
                                        choice_keys.index(default_value) + 1
                                        if default_value in choice_keys
                                        else None
                                    )

                                    selected_index = OptionPrompt.ask(
                                        question.prompt,
                                        choices=choice_values,
                                        default=default_index,
                                    )
                                    Display.print_log(
                                        f"\[selected] {selected_index}", log_level=5
                                    )
                                    user_config.answers[question.key] = choice_keys[
                                        selected_index - 1
                                    ]
                                case Question.Text():
                                    result = Prompt.ask(
                                        question.prompt,
                                        default=user_config.prompt_defaults.get(
                                            question.key
                                        ),
                                    )
                                    Display.print_log(
                                        f"\[answered] {result}", log_level=5
                                    )
                                    user_config.answers[question.key] = result
                                case Question.Bool():
                                    result = Prompt.ask(
                                        question.prompt,
                                        choices=["y", "n"],
                                        default="y" if user_config.prompt_defaults.get(
                                            question.key
                                        ) else "n"
                                    )
                                    Display.print_log(
                                        f"\[answered] {result}", log_level=5
                                    )
                                    user_config.answers[question.key] = result
                return "continue"

            case steps.PromptNoRecipe():
                Display.print_error(
                    "This solution does not have a recipe - unable to continue. \n"
                    + "This may be because the installed version is from before the assembler existed.\n"
                    + f"Expected to find the recipe file at: {step.err.expected_location}"
                )
            case steps.PromptToAssemble():
                if self.do_prompt_for_next_phase:
                    answer = TailoredConfirm.ask(
                        "? Do you want to assemble the solution now?", default=True
                    )
                else:
                    answer = True
                return answer
            case steps.PromptToBuild():
                if self.do_prompt_for_next_phase:
                    answer = TailoredConfirm.ask(
                        "? Do you want to build the solution now?", default=True
                    )
                else:
                    answer = True

                return answer
            case steps.PromptToStart():
                if self.do_prompt_for_next_phase:
                    answer = TailoredConfirm.ask(
                        "? Do you want to start the solution now?", default=True
                    )
                else:
                    answer = True
                return answer
            case _:
                raise Exception(f"{step} not implementent")

        return "continue"

    async def listen_for_updates(self):
        while True:
            msg = await self.update_receiver.recv()
            # print(msg)
            match msg:
                case AuditEvent():
                    self.diplay_audit_msg(msg)
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

    async def run(self):
        engine_t = asyncio.create_task(self.engine.run())
        engine_t.add_done_callback(task_callback)
        update_t = asyncio.create_task(self.listen_for_updates())
        update_t.add_done_callback(task_callback)

        initial_action_flag = True
        try:
            outcome = None
            while True:
                next_ui_step = await Engine.next(self.ui_pipe, outcome)
                match (next_ui_step):
                    case steps.PresentCommands():
                        if initial_action_flag:  # set initial action
                            outcome = ActionSignal(
                                action=self.action, solution=SolutionModel()
                            )
                            initial_action_flag = False
                        else:
                            break  # exit
                    case steps.PauseStep():
                        outcome = "continue"
                    case _:  # normal case
                        outcome = self.handle(next_ui_step)

        except FatalError as fatal_error:
            Display.print_error(fatal_error)
            sys.exit(255)

        await asyncio.sleep(0)  # give other tasks a chance for any cleanup

        engine_t.cancel()
        update_t.cancel()


def task_callback(task: asyncio.Task):
    try:
        exception = task.exception()
    except asyncio.CancelledError:
        return  # Ingnore
    if exception:
        if isinstance(exception, FatalError):
            Display.print_error(exception)
        else:
            try:
                raise exception
            except:
                print(traceback.format_exc())

        loop = asyncio.get_running_loop()

        pending = asyncio.all_tasks(loop=loop)
        for task in pending:
            task.cancel()
        group = asyncio.gather(*pending, return_exceptions=True)
        try:
            loop.run_until_complete(group)
        except:
            pass
