from shoestring_assembler.engine.action.assemble import Assembler
from shoestring_assembler.engine.action.user_config import UserConfig
from shoestring_assembler.engine.action.git import GetSolutionUsingGit
from shoestring_assembler.engine.action.filesystem import SolutionFilesystem
from shoestring_assembler.engine.action.docker import Docker
from shoestring_assembler.interface.events import (
    EventPipe,
    Audit,
    Progress,
    Update,
    FatalError,
    ProgressSection,    
)

from shoestring_assembler.model.solution import SolutionModel
from shoestring_assembler.model.recipe import NoRecipeError
from shoestring_assembler.model.installed import InstalledSolutionsModel

from pathlib import Path
import time
import os
import urllib
import yaml
import asyncio


from shoestring_assembler.interface.state_machine import steps
from shoestring_assembler.interface.signals import ActionSignal
from shoestring_assembler.interface.pipe import pipe


class Engine:

    def __init__(self, engine_pipe: pipe.Duplex, update_sender: pipe.Sender):
        self.__internal = EngineInternal(engine_pipe, update_sender)

    @property
    def solution_model(self):
        return self.__internal.solution_model

    @property
    def installed_solutions(self):
        return self.__internal.installed_solutions

    @staticmethod
    async def next(pipe: pipe.Duplex, outcome=None):
        await pipe.send(outcome)
        return await pipe.recv()

    async def run(self):
        return await self.__internal.run()


class EngineInternal:

    def __init__(self, engine_pipe: pipe.Duplex, update_sender: pipe.Sender):
        self.do_load_sources = True
        self.installed_solutions = InstalledSolutionsModel()
        self.__solution_model = None

        self.__current_step: steps.ProcessStep = steps.PresentCommands()

        self.engine_pipe = engine_pipe
        self.update_sender = update_sender

        EventPipe.attach_callback(self.update_ui)

    async def update_ui(self, message):
        await self.update_sender.send(message)
        await asyncio.sleep(0)  # yield to allow ui tasks to process update message

    @property
    def solution_model(self) -> SolutionModel:
        if self.__solution_model is None:
            raise FatalError("Solution context not set")
        return self.__solution_model

    async def __next(self, outcome) -> steps.ProcessStep:
        next_ui_step = None
        if outcome is not None:
            self.__current_step.resolve(outcome)
        while next_ui_step is None:
            await Update.DebugLog(f"current step: {type(self.__current_step).__name__}")
            try:
                if self.__current_step.is_resolved:
                    self.__current_step = self.__current_step.next_step
            except steps.ProcessStep.NotResolvedException:
                await Update.WarningMsg(
                    f"Step {type(self.__current_step).__name__} didn't resolve the first time"
                )
            finally:
                await Update.DebugLog(
                    f"next step: {type(self.__current_step).__name__}"
                )
                if isinstance(self.__current_step, steps.EngineStep):
                    await self.__handle_engine_step(self.__current_step)
                elif isinstance(self.__current_step, steps.Terminate):
                    break
                else:
                    next_ui_step = self.__current_step

        return next_ui_step

    async def run(self):
        await Update.StageHeading("Initialising Engine")
        await self.installed_solutions.saturate_solutions()
        while True:
            outcome = await self.engine_pipe.recv()
            next_ui_step = await self.__next(outcome)
            await self.engine_pipe.send(next_ui_step)

    async def __handle_engine_step(self, step):
        # Note each step should be resolved when the end of this function is reached
        resolution_args = []
        match (step):
            case steps.FetchProvidedSolutionsList():
                provider_list = await self.fetch_available_solution_list()
                resolution_args = [provider_list]
            case steps.FetchAvailableSolutionVersions():
                available_versions = await self.fetch_available_solution_versions(
                    step.solution_details
                )
                if len(available_versions) == 0:
                    await Update.NotifyMsg("No versions available for this solution")
                resolution_args = [available_versions]
            case steps.DownloadSolution():
                download_path = await self.download_solution(step.solution_spec)
                resolution_args = [download_path]
            case steps.AddInstalledSolution():
                solution = await self.add_installed_solution(step.path, step.base_name)
                resolution_args = [solution]
            case steps.SetSolutionContext():
                outcome = await self.set_solution_context(step.solution)
                resolution_args = [outcome]
            case steps.AssembleSolution():
                await self.assemble_solution()
            case steps.ConfigureSolution():
                await self.configure()
            case steps.BuildSolution():
                await self.build()
            case steps.CheckIfSetup():
                is_setup = await self.check_setup()
                resolution_args = [is_setup]
            case steps.SetupSolution():
                await self.setup()
            case steps.StartSolution():
                await self.start()
            case steps.RestartSolution():
                await self.restart()
            case steps.InitiateUpdate():
                await Update.StageHeading("Update Solution")
                await self.solution_model.version_control.get_version_data()
                if step.specified_version != "" and step.specified_version != None:
                    self.solution_model.version_control.target_version = (
                        step.specified_version
                    )
                resolution_args = [
                    step.specified_version != "" and step.specified_version != None
                ]
            case steps.CheckForUpdates():
                new_version = await self.check_for_updates()
                if new_version and step.no_prompt:
                    self.solution_model.version_control.target_version = new_version
                resolution_args = [new_version]
            case steps.DownloadUpdate():
                await self.download_update()
            case steps.StopSolution():
                await self.stop()
            case steps.RemoveSolution():
                await self.remove_solution()
            case steps.RenameSolution():
                await self.rename_solution(step.new_name)

        step.resolve(*resolution_args)

    ### process steps
    async def fetch_available_solution_list(self):
        list_branch = os.getenv("SHOESTRING_LIST_BRANCH", "main")
        try:
            with urllib.request.urlopen(
                f"https://github.com/DigitalShoestringSolutions/solution_list/raw/refs/heads/{list_branch}/list.yaml"
            ) as web_in:
                content = web_in.read()
                provider_list = yaml.safe_load(content)
        except urllib.error.URLError:
            raise FatalError("Unable to fetch latest solution list")
        return provider_list

    async def fetch_available_solution_versions(self, solution_details):
        available_versions = GetSolutionUsingGit.available_versions(
            solution_details["url"], solution_details["minimum_version"]
        )
        return available_versions

    async def download_solution(self, spec):
        name = spec["name"]
        await Update.StepHeading(f"Downloading {name}")
        async with ProgressSection("download_solution"):
            success, location = await GetSolutionUsingGit.download(spec)
        if success:
            await Update.SuccessMsg("Downloaded")
            return location
        else:
            raise FatalError("Unable to download solution")

    async def add_installed_solution(self, path, base_name):
        return await self.installed_solutions.add_solution(path, base_name)

    async def set_solution_context(self, solution):
        self.__solution_model = solution
        try:
            await self.__solution_model.saturate()
            outcome = "continue"
        except NoRecipeError as err:
            outcome = err

    async def check_for_updates(self):
        await Update.StepHeading("Checking for updates")
        if self.solution_model.version_control.can_update():
            await Update.AttentionMsg("New Updates are available.")
            return self.solution_model.version_control.available_updates[0]
        else:
            await Update.NotifyMsg("Already using the latest update.")
            return False

    async def download_update(self):
        await Update.StepHeading(
            f"Downloading update {self.solution_model.version_control.target_version}"
        )
        await self.solution_model.version_control.update()

    async def assemble_solution(self):
        await Update.StageHeading("Assembling Solution")
        await SolutionFilesystem.verify(
            self.solution_model, check_source_download=not self.do_load_sources
        )
        await SolutionFilesystem.clean(
            self.solution_model, remove_downloaded_files=self.do_load_sources
        )
        await Assembler(self.solution_model).load_sources(
            do_gather=self.do_load_sources
        )
        await Assembler(self.solution_model).generate_compose_file()

    async def configure(self):
        await Update.StageHeading("Generating Config Files")
        await UserConfig.configure(self.solution_model)

    async def build(self):
        await Update.StageHeading("Building solution")
        await Update.InfoMsg("Building... (This may take several minutes)")
        built = await Docker.build(self.solution_model)
        if built:
            await Update.SuccessMsg("Solution Built")
        else:
            raise FatalError("Solution Building Failed")

    async def check_setup(self):
        return False

    async def setup(self):
        await Update.StageHeading("Setting up solution")
        await Docker.setup_containers(self.solution_model)
        await Update.SuccessMsg("Setup Complete")

    async def start(self):
        await Update.StageHeading("Starting solution")
        started = await Docker.start(self.solution_model)
        if started:
            await Update.SuccessMsg("Solution is now running in the background")

    async def restart(self):
        await Update.StageHeading("Restarting solution")
        await Update.StepHeading("Stopping solution")
        await Docker.stop(self.solution_model)

        await Update.StepHeading("Building solution")
        await Docker.build(self.solution_model)

        await Update.StepHeading("Starting solution")
        started = await Docker.start(self.solution_model)
        if started:
            await Update.SuccessMsg("Solution is now running in the background")

    async def stop(self):
        await Update.StageHeading("Stopping solution")
        stopped = await Docker.stop(self.solution_model)
        if stopped:
            await Update.SuccessMsg("Solution has now stopped")

    async def remove_solution(self):
        await Update.StageHeading("Removing Solution")
        await self.installed_solutions.remove_solution(self.solution_model)
        self.__solution_model = None

    async def rename_solution(self, new_name):
        await Update.StageHeading("Renaming Solution")
        await self.installed_solutions.rename_solution(self.solution_model,new_name)
