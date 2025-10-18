from shoestring_assembler.model.source import SourceModel
from shoestring_assembler.model.container import Container
from .common import ModelMap

from .user_config import UserConfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shoestring_assembler.model.filesystem import ModuleFilesystem


class BaseModule:

    def __init__(self, name: str, *, spec, fs: "ModuleFilesystem", source: SourceModel):
        self.fs = fs

        self.__name = name
        self.__spec = spec
        self.__source = source

        self.__containers = None
        self.__user_config = None

        # self.data_dir_relpath = Path(f"./{Contants.DATA_DIR}/{self.__name}")

    @property
    def name(self) -> str:
        return self.__name

    @property
    def source(self) -> SourceModel:
        return self.__source

    @property
    def spec(self):
        return self.__spec

    @property
    def containers(self):
        if self.__containers is None:
            container_list = self.__spec.get("containers", [])
            container_map = {
                container_name: {
                    "spec": {
                        "ports": self.__spec.get("ports", {}).get(container_name, {}),
                        "alias": self.__spec.get("alias", {}).get(container_name, None),
                        "volumes": self.__spec.get("volume", {}).get(
                            container_name, {}
                        ),
                        "identifier": (
                            f"{self.name}-{container_name}"
                            if len(container_list) > 1
                            else self.name
                        ),
                    },
                    "module": self,
                }
                for container_name in container_list
            }

            self.__containers = ModelMap.generate(Container, container_map)
        return self.__containers

    @property
    def user_config(self) -> UserConfig:
        if self.__user_config is None:
            self.__user_config = UserConfig(
                self.fs.user_config, self.source.fs.user_config_template
            )
        return self.__user_config
