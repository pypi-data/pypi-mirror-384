from shoestring_assembler.model.recipe import Recipe, SolutionSpec, NoRecipeError
from shoestring_assembler.model.service_module import ServiceModuleModel
from shoestring_assembler.model.infrastructure_module import InfrastructureModule
from shoestring_assembler.model.source import SourceModel
from shoestring_assembler.implementation.vc.git import SolutionGitVC
from shoestring_assembler.interface.events.updates import FatalError
from pathlib import Path
from .common import ModelMap
from itertools import chain
from enum import Enum, unique
import yaml
from shoestring_assembler.model.filesystem import SolutionFilesystem

"""
ShoestringCommunityModel
provider_list
selected solution
available solution versions
selected version

available updates
selected version
"""


class SolutionModel:

    def __init__(self, name="", *, root_dir=Path.cwd()):

        self.__provided_root = root_dir
        self.fs = SolutionFilesystem(root=root_dir)
        self.user_given_name = name
        self.status = SolutionModel.Status.UNKNOWN

        # Saturated from recipe
        self.__sources = None
        self.__service_modules = None
        self.__infrastructure = None

        self.__solution_details = None
        self.__recipe_details = None
        self.saturated = False

        # deffered loading
        self.__version_control = None
        self.__compose_spec = None

    async def saturate(self):
        if not self.saturated:
            if not self.fs.root_valid:
                raise NoRecipeError(
                    f"Solution does not have a valid root directory.",
                    expected_location=self.__provided_root,
                )
            recipe = await Recipe.load(self.fs.recipe_file)

            sources_definition = {
                name: {
                    "spec": spec,
                    "fs": self.fs.get_source_fs(name),
                    "root": self.fs.root,
                }
                for name, spec in recipe.sources.items()
            }
            self.__sources = ModelMap.generate(SourceModel, sources_definition)
            sm_definitions = {
                name: {
                    "spec": spec,
                    "fs": self.fs.get_module_fs(name),
                    "source": self.__sources[spec["source"]],
                }
                for name, spec in recipe.service_modules.items()
            }
            self.__service_modules = ModelMap.generate(
                ServiceModuleModel, sm_definitions
            )
            inf_definitions = {
                name: {
                    "spec": spec,
                    "fs": self.fs.get_module_fs(name),
                    "source": self.__sources[spec["source"]],
                }
                for name, spec in recipe.infrastructure.items()
            }
            self.__infrastructure = ModelMap.generate(
                InfrastructureModule, inf_definitions
            )

            self.__solution_details = recipe.solution
            self.__recipe_details = recipe
            self.saturated = True

    @property
    def sources(self):
        return self.__sources

    @property
    def service_modules(self):
        return self.__service_modules

    @property
    def infrastructure(self):
        return self.__infrastructure

    @property
    def solution_details(self) -> SolutionSpec:
        return self.__solution_details

    @property
    def recipe_details(self) -> SolutionSpec:
        return self.__recipe_details

    @property
    def version_control(self) -> "VersionControl":
        if self.__version_control is None:
            self.__version_control = VersionControl(self)
        return self.__version_control

    @property
    def available_updates(self) -> list:
        return self.version_control.available_updates

    @property
    def current_version(self):
        return self.version_control.current_version

    def module_iterator(self):
        return chain(iter(self.service_modules), iter(self.infrastructure))

    @property
    def compose_spec(self):
        if self.__compose_spec is None:
            self.__load_compose_spec()
        return self.__compose_spec

    def __load_compose_spec(self):
        try:
            with self.fs.compose_file.open("r") as f:
                self.__compose_spec = yaml.safe_load(f)
        except FileNotFoundError:
            self.__compose_spec = None

    def save_compose_spec(self, compose_definition):
        self.__compose_spec = compose_definition
        with self.fs.compose_file.open("w") as f:
            yaml.safe_dump(
                compose_definition, f, default_flow_style=False, sort_keys=False
            )
    
    @unique
    class Status(Enum):
        STOPPED = "stopped"
        RUNNING = "running"
        UNKNOWN = "unknown"


class VersionControl:
    def __init__(self, solution):
        self.__solution = solution
        self.__implementation = SolutionGitVC
        self.__current_version = None
        self.__available_updates = None  # list with latest update at index 0

        self.__target_version = None

        self.__version_data_loaded = False

    async def get_version_data(self):
        await self.__get_version_data()
        self.__version_data_loaded = True

    @property
    def available_updates(self):
        if not self.__version_data_loaded:
            raise VersionControl.NotLoadedException("Version Data not loaded")
        return self.__available_updates

    @property
    def current_version(self):
        if not self.__version_data_loaded:
            raise VersionControl.NotLoadedException("Version Data not loaded")
        return self.__current_version

    @property
    def target_version(self):
        return self.__target_version
    
    @property
    def is_loaded(self):
        return self.__version_data_loaded

    @target_version.setter
    def target_version(self, new_value):
        if new_value in self.available_updates:
            self.__target_version = new_value
        else:
            raise FatalError(
                f"Requested solution version of {new_value} is not one of the available updates: {self.available_updates}"
            )

    def can_update(self):
        return (
            len(self.available_updates) > 0
            and self.available_updates[0] != self.current_version
        )

    async def __get_version_data(self):
        self.__current_version, self.__available_updates = (
            await self.__implementation.fetch_version_details(self.__solution)
        )

    async def update(self):
        updated = await self.__implementation.do_update(self.__solution,self.target_version)
        if updated:
            self.__current_version = self.target_version

    class NotLoadedException(Exception):
        pass
