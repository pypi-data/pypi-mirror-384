from pathlib import Path

import json
import hashlib
from pathlib import Path
from shoestring_assembler.model.schemas import RecipeSchema, SchemaValidationError
from shoestring_assembler.interface.events import FatalError, Update

from enum import Enum, unique

try:
    import tomllib as toml
except ImportError:
    import tomli as toml

import yaml

MAX_RECIPE_VSN = (1,0,0)
MIN_RECIPE_VSN = (1,0,0)

class NoRecipeError(Exception):
    def __init__(self, message, expected_location):
        super().__init__(message)
        self.message = message
        self.expected_location = expected_location


class Recipe:
    def __init__(self, recipe_filepath, recipe, hash):
        self.filepath_provided = recipe_filepath
        self.__recipe = recipe
        self.hash = hash

    #
    # Methods for loading and validation
    #

    @classmethod
    async def load(cls, recipe_filepath):
        recipe_location = Path.resolve(Path(recipe_filepath))
        await Update.StepHeading("Get Recipe")
        try:
            # check file type is supported and find parser
            ext = recipe_location.suffix

            if ext == ".yml" or ext == ".yaml":
                parser = cls._parse_yaml
            elif ext == ".toml":
                parser = cls._parse_toml
            elif ext == ".json":
                parser = cls._parse_json
            else:
                raise FatalError(
                    f"Recipe format unsupported - expects a json, yaml or toml file"
                )

            # parse file
            with open(recipe_location, "rb") as file:
                # , description="Loading Recipe..."
                recipe_content = parser(file)
                file.seek(0)  # reset file
                hash_fn = hashlib.sha256()
                hash_fn.update(file.read())
                recipe_hash = hash_fn.hexdigest()

            recipe_obj = cls(recipe_filepath, recipe_content, recipe_hash)

            await Update.InfoMsg("Validating Recipe")
            await recipe_obj.validate()
            await Update.InfoMsg("Recipe valid")

        except FileNotFoundError:
            raise NoRecipeError(
                f"Unable to find recipe file. Expected to find it at: {recipe_location}", recipe_location
            )

        await Update.SuccessMsg("Recipe loaded")
        return recipe_obj

    @classmethod
    def _parse_json(self, file):
        return json.load(file)

    @classmethod
    def _parse_yaml(self, file):
        return yaml.safe_load(file)

    @classmethod
    def _parse_toml(self, file):
        return toml.load(file)

    async def validate(self):
        try:
            RecipeSchema.validate(self.__recipe)
            recipe_version = tuple([int(digit) for digit in self.__recipe.get("recipe_vsn","0.0.0").split(".")])
            if recipe_version < MIN_RECIPE_VSN or recipe_version > MAX_RECIPE_VSN:
                raise FatalError(
                    f"This version of the assembler only supports recipes between {MIN_RECIPE_VSN} and {MAX_RECIPE_VSN} please update to an assembler version that supports {recipe_version}"
                )
        except SchemaValidationError as v_err:
            raise FatalError(
                f"Recipe error at {v_err.json_path}:\n\n{v_err.message} \n"
                + "Recipe is not valid -- unable to start the solution -- please correct the issues flagged above and try again."
            )

    #
    # Methods for recipe access
    #

    @property
    def sources(self) -> dict[str:"SourceSpec"]:
        return {
            source_name: SourceSpec(source_content)
            for source_name, source_content in self.__recipe["source"].items()
        }

    @property
    def service_modules(self) -> dict:
        return self.__recipe.get("service_module", {})

    @property
    def infrastructure(self) -> dict:
        return self.__recipe.get("infrastructure", {})

    @property
    def solution(self) -> dict:
        return SolutionSpec(self.__recipe["solution"])


class SolutionSpec:
    def __init__(self, recipe_dict: dict):
        self.name = recipe_dict["name"]
        self.slug = recipe_dict["slug"]
        self.version = recipe_dict["version"]
        self.description = recipe_dict.get("description", "")


class SourceSpec:
    def __new__(cls, recipe_dict: dict):
        if "file" in recipe_dict:
            return FileSourceSpec(recipe_dict)
        elif "git" in recipe_dict:
            return GitSourceSpec(recipe_dict)
        else:
            return UnknownSourceSpec(recipe_dict)


class GitSourceSpec:
    def __init__(self, recipe_dict):
        base = recipe_dict["git"]
        path = base["path"]  # could throw error but shouldn't due to validation

        num_slashes = path.count("/")
        if num_slashes == 0:
            url = f"https://github.com/DigitalShoestringSolutions/{path}"
        elif num_slashes == 1:
            url = f"https://github.com/{path}"
        else:
            url = path

        self.url = url

        tag = base.get("tag")
        branch = base.get("branch")
        self.target = tag if tag else branch


class FileSourceSpec:

    def __init__(self, recipe_dict):
        base = recipe_dict["file"]
        self.mode = base.get("mode", "copy")
        self.filepath = base["path"]


class UnknownSourceSpec(SourceSpec):
    pass


class ModuleSegment:

    def __init__(self, recipe_dict: dict):
        pass
