from shoestring_assembler.interface.events.updates import FatalError
import typing
from shoestring_assembler.utilities import path


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shoestring_assembler.model.base_module import BaseModule


class Container:

    def __init__(self, name: str,*, spec, module: "BaseModule"):
        self.__name = name
        self.__spec = spec
        self._module = module

        # deferred loading
        self.__compose_partial = None

        self.identifier = spec["identifier"]
        self.__alias = spec["alias"] if spec["alias"] is not None else self.identifier

        self.volumes = VolumeMap(self.identifier, self.__spec["volumes"], module.fs.data_dir,module.fs.user_config.dir)

    @property
    def name(self):
        return self.__name

    @property
    def meta(self):
        try:
            return self._module.source.meta[self.__name]
        except KeyError:
            raise FatalError(
                f"Could not find entry for container {self.__name} in meta file - available containers: {list(self._module.source.meta.keys())}"
            )

    @property
    def alias(self):
        return self.__alias

    @property
    def host_ports(self):
        return self.__spec["ports"]

    @property
    def partial_compose_snippet(self):
        if self.__compose_partial is None:
            self.__compose_partial = self.__load_partial_compose_snippet()
        return self.__compose_partial

    def __load_partial_compose_snippet(self):
        if "compose_partial" not in self.meta:
            return None

        try:
            compose_partial_file_path = (
                self._module.source.fs.fetch_dir
                / self.meta["compose_partial"]
            )

            with compose_partial_file_path.open("r") as file:
                return file.read()
        except FileNotFoundError:
            raise FatalError(
                f"Unable to find compose partial file for {self.__name}. Expected to find it at: {compose_partial_file_path}"
            )


class Volume:
    def __init__(
        self,
        container_identifier,
        name,
        *,
        host_path=None,
        container_path=None,
        mode=None,
    ):
        self.name = name
        self.__container_identifier = container_identifier
        self.__host_path = host_path
        self.__container_path = container_path
        self.__mode = mode
        self.ignored = False

    def check_valid(self):
        if self.__host_path is not None and self.__container_path is not None:
            return True
        elif self.__container_path is None:
            # no container entry to map to
            raise FatalError(
                f"No corresponding container entry for volume {self.name} of {self.__container_identifier}."
            )
        elif self.__host_path is None:
            # no host entry to map to
            raise FatalError(
                f"No corresponding host entry for volume {self.name} of {self.__container_identifier}."
            )

    @classmethod
    def from_container_spec(cls, container_id, name, spec):
        inst = cls(container_id, name)
        inst.apply_container_spec(spec)
        return inst

    def apply_container_spec(self, spec):
        self.ignored = spec.get("ignore", False)
        if not self.ignored:
            self.__container_path = spec["path"]
            self.__mode = spec.get("mode")

    def formatted(self):
        base = f"{self.__host_path}:{self.__container_path}"
        if self.__mode:
            return f"{base}:{self.__mode}"
        else:
            return base


class VolumeMap(typing.MutableMapping[str, Volume]):

    def __init__(self, container_id, host_volumes: dict, data_dir, uc_dir):
        self.__dict = {}
        self.__container_id = container_id

        self["data"] = Volume(
            container_id,
            "data",
            host_path=path.as_string(data_dir),
        )

        self["user_config"] = Volume(
            container_id,
            "user_config",
            host_path=path.as_string(uc_dir),
        )

        for name, value in host_volumes.items():
            self[name] = Volume(container_id, name, host_path=value)

    def __getitem__(self, key: str) -> Volume:
        return self.__dict.__getitem__(key)

    def __setitem__(self, key: str, value: Volume):
        self.__dict.__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        return self.__dict.__delitem__(key)

    def __len__(self) -> int:
        return self.__dict.__len__()

    def __contains__(self, key: str) -> bool:
        return self.__dict.__contains__(key)

    def __iter__(
        self,
    ) -> typing.Iterable[Volume]:
        return self.__dict.__iter__()

    def apply_container_spec(self, spec):
        for name, vol_spec in spec.items():
            if name in self:
                self[name].apply_container_spec(vol_spec)
            else:
                self[name] = Volume.from_container_spec(
                    self.__container_id, name, vol_spec
                )
