from shoestring_assembler.interface import signals
from pathlib import Path


class ProcessStep:
    class NotResolvedException(Exception):
        pass

    def __init__(self):
        self.__resolved = False
        self.__next = None

    @property
    def is_resolved(self):
        return self.__resolved

    def resolve(self, next_step):
        self.__resolved = True
        self.__next = next_step

    def reset(self):
        self.__resolved = False

    @property
    def next_step(self):
        if not self.__resolved:
            raise ProcessStep.NotResolvedException()
        return self.__next


class UIStep(ProcessStep):
    pass


class EngineStep(ProcessStep):
    pass


class Terminate(ProcessStep):
    pass


class PauseStep(UIStep):
    def __init__(self, next):
        super().__init__()
        self.next = next

    def resolve(self, signal):
        return super().resolve(self.next)


class PresentCommands(UIStep):
    def resolve(self, signal: signals.ActionSignal):
        match signal.action:
            case signals.Action.DOWNLOAD:
                return super().resolve(FetchProvidedSolutionsList())
            case signals.Action.FIND:
                return super().resolve(FindInstalledSolution())
            case signals.Action.ASSEMBLE:
                return super().resolve(
                    SetSolutionContext(signal.solution, AssembleSolution())
                )
            case signals.Action.UPDATE:
                return super().resolve(
                    SetSolutionContext(signal.solution, InitiateUpdate())
                )
            case signals.Action.RECONFIGURE:
                return super().resolve(
                    SetSolutionContext(signal.solution, GetConfigurationInputs())
                )
            case signals.Action.BUILD:
                return super().resolve(
                    SetSolutionContext(signal.solution, BuildSolution())
                )
            case signals.Action.SETUP:
                return super().resolve(
                    SetSolutionContext(signal.solution, SetupSolution())
                )
            case signals.Action.START:
                return super().resolve(
                    SetSolutionContext(signal.solution, StartSolution())
                )

            case signals.Action.RESTART:
                return super().resolve(
                    SetSolutionContext(signal.solution, RestartSolution())
                )
            case signals.Action.STOP:
                return super().resolve(
                    SetSolutionContext(signal.solution, StopSolution())
                )
            case signals.Action.REMOVE:
                return super().resolve(
                    SetSolutionContext(signal.solution, RemoveSolution())
                )
            case signals.Action.EDIT:
                return super().resolve(SetSolutionContext(signal.solution, NewName()))
            case _:
                raise Exception(signal.action)


class FindInstalledSolution(UIStep):
    def resolve(self, return_value):
        match return_value:
            case Path():
                return super().resolve(AddInstalledSolution(return_value,None))
            case signals.BackSignal():
                return super().resolve(PresentCommands())


class AddInstalledSolution(EngineStep):
    def __init__(self, path, base_name):
        super().__init__()
        self.path = path
        self.base_name = base_name

    def resolve(self, solution_or_err):
        if isinstance(solution_or_err, NoRecipeError):
            return super().resolve(PromptNoRecipe(solution_or_err))
        else:
            return super().resolve(
                SetSolutionContext(solution_or_err, PromptToAssemble())
            )


from shoestring_assembler.model.recipe import NoRecipeError


class SetSolutionContext(EngineStep):
    def __init__(self, solution, next):
        super().__init__()
        self.solution = solution
        self.next = next

    def resolve(self, outcome):
        if isinstance(outcome, NoRecipeError):
            return super().resolve(PromptNoRecipe(outcome))
        else:
            return super().resolve(self.next)


class PromptNoRecipe(UIStep):
    def __init__(self, err_obj):
        super().__init__()
        self.err = err_obj

    def resolve(self, signal):
        super().resolve(PresentCommands())


class FetchProvidedSolutionsList(EngineStep):
    def __init__(self):
        super().__init__()

    def resolve(self, provider_list):
        if provider_list:
            super().resolve(ChooseSolution(provider_list))


class ChooseSolution(UIStep):
    def __init__(self, provider_list):
        super().__init__()
        self.provider_list = provider_list

    def resolve(self, selected_solution_details):
        if isinstance(selected_solution_details, signals.BackSignal):
            super().resolve(PresentCommands())
        else:
            super().resolve(FetchAvailableSolutionVersions(selected_solution_details))


class FetchAvailableSolutionVersions(EngineStep):
    def __init__(self, solution_details):
        super().__init__()
        self.solution_details = solution_details

    def resolve(self, available_versions_list):
        if available_versions_list:
            super().resolve(
                ChooseSolutionVersion(self.solution_details, available_versions_list)
            )
        else:
            super().resolve(PresentCommands())


class ChooseSolutionVersion(UIStep):
    def __init__(self, solution_details, version_list):
        super().__init__()
        self.solution_details = solution_details
        self.version_list = version_list

    def resolve(self, selected_version):
        if isinstance(selected_version, signals.BackSignal):
            super().resolve(PresentCommands())
        else:
            spec = {**self.solution_details, "selected_version": selected_version}
            super().resolve(ChooseDownloadLocation(spec))


class ChooseDownloadLocation(UIStep):
    def __init__(self, solution_spec):
        super().__init__()
        self.solution_spec = solution_spec

    def resolve(self, outcome):
        if isinstance(outcome, signals.BackSignal):
            super().resolve(PresentCommands())
        else:
            spec = {**self.solution_spec, "download_location": outcome}
            super().resolve(DownloadSolution(spec))


class DownloadSolution(EngineStep):
    def __init__(self, solution_spec):
        super().__init__()
        self.solution_spec = solution_spec

    def resolve(self, download_path):
        super().resolve(AddInstalledSolution(download_path,self.solution_spec["name"]))


class PromptToAssemble(UIStep):
    def resolve(self, do_assemble):
        if do_assemble:
            super().resolve(AssembleSolution())
        else:
            super().resolve(PresentCommands())


class AssembleSolution(EngineStep):
    def resolve(self):
        return super().resolve(PauseStep(GetConfigurationInputs()))


class GetConfigurationInputs(UIStep):
    def __init__(self, ignore_existing_setup=False):
        self.ignore_existing_setup = ignore_existing_setup
        super().__init__()

    def resolve(self, signal):
        match signal:
            case signals.BackSignal():
                super().resolve(PresentCommands())
            case _:
                super().resolve(ConfigureSolution())


class ConfigureSolution(EngineStep):
    def resolve(self):
        return super().resolve(PromptToBuild())


class PromptToBuild(UIStep):
    def resolve(self, do_build):
        if do_build:
            super().resolve(BuildSolution())
        else:
            super().resolve(PresentCommands())


class BuildSolution(EngineStep):
    def resolve(self):
        return super().resolve(CheckIfSetup())


class CheckIfSetup(EngineStep):
    def resolve(self, is_setup):
        if not is_setup:
            super().resolve(SetupSolution())
        else:
            super().resolve(PromptToStart())


class SetupSolution(EngineStep):
    def resolve(self):
        return super().resolve(PromptToStart())


class PromptToStart(UIStep):
    def resolve(self, do_start):
        if do_start:
            super().resolve(StartSolution())
        else:
            super().resolve(PresentCommands())


class RestartSolution(EngineStep):
    def resolve(self):
        return super().resolve(PauseStep(PresentCommands()))


class StartSolution(EngineStep):
    def resolve(self):
        return super().resolve(PauseStep(PresentCommands()))


class InitiateUpdate(EngineStep):
    def __init__(self, specified_version=None, no_prompt=False):
        self.specified_version = specified_version
        self.no_prompt = no_prompt
        super().__init__()

    def resolve(self, version_set):
        if version_set:
            return super().resolve(DownloadUpdate())
        else:
            return super().resolve(CheckForUpdates(no_prompt=self.no_prompt))


class CheckForUpdates(EngineStep):
    def __init__(self, no_prompt=False):
        self.no_prompt = no_prompt
        super().__init__()

    def resolve(self, new_version):
        if new_version == False or new_version == "":
            return super().resolve(PresentCommands())
        elif new_version and self.no_prompt:
            return super().resolve(DownloadUpdate())
        else:
            return super().resolve(SelectUpdateVersion())


class SelectUpdateVersion(UIStep):
    def resolve(self, signal):
        match signal:
            case signals.BackSignal():
                super().resolve(PresentCommands())
            case _:
                return super().resolve(DownloadUpdate())


class DownloadUpdate(EngineStep):
    def resolve(self):
        return super().resolve(PromptToAssemble())


class StopSolution(EngineStep):
    def resolve(self):
        return super().resolve(PauseStep(PresentCommands()))

class RemoveSolution(EngineStep):
    def resolve(self):
        return super().resolve(PresentCommands())

class NewName(UIStep):
    def resolve(self, back_or_new_name):
        match back_or_new_name:
            case signals.BackSignal():
                super().resolve(PresentCommands())
            case _:
                super().resolve(RenameSolution(back_or_new_name))

class RenameSolution(EngineStep):
    def __init__(self, new_name):
        super().__init__()
        self.new_name = new_name
        
    def resolve(self):
        return super().resolve(PresentCommands())
