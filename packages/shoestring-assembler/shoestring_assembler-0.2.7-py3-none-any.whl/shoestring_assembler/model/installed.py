from shoestring_assembler.constants import Constants
from shoestring_assembler.model.common import ModelMap
from shoestring_assembler.model.solution import SolutionModel
from shoestring_assembler.model.recipe import NoRecipeError
from shoestring_assembler.interface.events import FatalError, Update
import json
from pathlib import Path
from shoestring_assembler.engine.action.docker import Docker


class InstalledSolutionsModel:
    def __init__(self):
        self.__solutions = None
        self.__file = Path(Constants.INSTALLED_SOLUTIONS_LIST)
        if not self.__file.parent.exists():
            self.__file.parent.mkdir()

    @property
    def solutions(self):
        return self.__solutions

    async def saturate_solutions(self):
        try:
            with self.__file.open() as f:
                contents = f.read()
                if contents != "":
                    install_dirs = json.loads(contents)
                else:
                    install_dirs = {}
        except FileNotFoundError:
            install_dirs = {}

        definition = {name: {"root_dir": path} for name, path in install_dirs.items()}
        self.__solutions = ModelMap.generate(SolutionModel, definition)
        for solution in self.__solutions:
            try:
                await solution.saturate()
            except NoRecipeError:
                pass

    async def check_running(self):
        running_list = await Docker.get_running_list()
        await Update.DebugLog(f"running_list: {running_list}")
        if running_list is None:
            for solution in self.solutions:
                solution.status = SolutionModel.Status.UNKNOWN
        else:
            compose_file_list = [Path(entry["ConfigFiles"]) for entry in running_list]
            await Update.DebugLog(f"compose_file_list: {compose_file_list}")
            for solution in self.solutions:
                if solution.fs.compose_file in compose_file_list:
                    solution.status = SolutionModel.Status.RUNNING
                else:
                    solution.status = SolutionModel.Status.STOPPED

    async def add_solution(self, path, base_name):
        solution = SolutionModel(root_dir=path)

        for existing_solution in self.__solutions:
            if solution.fs.root == existing_solution.fs.root: 
                await Update.NotifyMsg(
                    f"Solution has already been added as {existing_solution.user_given_name}"
                )
                return existing_solution

        if base_name == None:
            await solution.saturate()  # should be error free as base_name should only be None when this is triggered by a Find
            base_name = solution.solution_details.name

        try:
            with self.__file.open() as f:
                contents = f.read()
                if contents != "":
                    install_dirs = json.loads(contents)
                else:
                    install_dirs = {}
        except FileNotFoundError:
            install_dirs = {}

        try:
            with self.__file.open("w") as f:
                name = base_name
                counter = 1
                while name in install_dirs.keys():
                    name = f"{base_name}_{counter}"
                    counter += 1

                try:
                    json.dump({**install_dirs, name: str(path)}, f)
                    self.__solutions[name] = solution
                    solution.user_given_name = name
                except:
                    json.dump(install_dirs, f)
                    raise
        except FileNotFoundError:
            raise

        try:
            await solution.saturate()
        except NoRecipeError as err:
            await Update.ErrorMsg(f"No recipe found for solution at {path}")
            return err
        return solution

    async def remove_solution(self, solution: SolutionModel):
        del self.__solutions[solution.user_given_name]
        await self.__overwrite_installed_list()
        await Update.NotifyMsg(
            f"Solution {solution.user_given_name} removed"
        )

    async def rename_solution(self, solution: SolutionModel, new_name):
        solution.user_given_name = new_name
        await self.__overwrite_installed_list()
        await Update.NotifyMsg(f"Solution name changed to {solution.user_given_name}")

    async def __overwrite_installed_list(self):
        try:
            with self.__file.open("w") as f:
                json.dump(
                    {
                        solution.user_given_name: str(solution.fs.root)
                        for solution in self.__solutions
                    },
                    f,
                )
        except:
            # TODO as needed
            raise
