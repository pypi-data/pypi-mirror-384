from shoestring_assembler.model.schemas import MetaSchema, SchemaValidationError
from shoestring_assembler.interface.events.updates import FatalError
from shoestring_assembler.implementation.source import SourceImplementation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shoestring_assembler.model.solution import SolutionModel
    from shoestring_assembler.model.filesystem import SourceFilesystem

try:
    import tomllib as toml
except ImportError:
    import tomli as toml


class SourceModel:
    def __init__(self, name,*, spec, fs:'SourceFilesystem',root):
        self.__name = name

        self.__implementation = SourceImplementation(spec,root)

        # deferred loading
        self.__source_meta = None

        # File paths
        self.fs = fs

    @property
    def name(self):
        return self.__name

    @property
    def meta(self):
        if self.__source_meta is None:  # lazy loading
            self.__source_meta = self.__load_meta()
        return self.__source_meta

    def __load_meta(self):
        try:
            with open(
                self.fs.meta_file,
                "rb",
                # description="Loading meta...",
            ) as file:
                meta = toml.load(file)
            # validate
            MetaSchema.validate(meta)
            return meta
        except FileNotFoundError:
            raise FatalError(
                f"Unable to find meta file for {self.__name}. Expected to find it at: {self.fs.meta_file}"
            )
        except SchemaValidationError as v_err:
            raise FatalError(
                f"Error in meta file for source '{self.__name}' at {v_err.json_path}:\n\n{v_err.message}\n" + 
                f"Meta file for source '{self.__name}' is not valid -- unable to start the solution"
            )

    async def fetch(self):
        return await self.__implementation.fetch(self.fs.fetch_dir)
