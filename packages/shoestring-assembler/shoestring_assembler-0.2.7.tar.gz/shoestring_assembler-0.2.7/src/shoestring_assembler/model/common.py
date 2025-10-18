from typing import TypeVar, Type, List, Iterable

T = TypeVar("T")


class ModelMap:
    def __init__(self):
        self.__dict = {}

    @classmethod
    def generate(
        cls, ModelCls: Type[T], child_definitions
    ) -> List[T]:
        inst = cls()
        for name, kwargs in child_definitions.items():
            inst[name] = ModelCls(name, **kwargs)
        return inst

    def __getitem__(self, key: str) -> T:
        return self.__dict.__getitem__(key)

    def __setitem__(self, key: str, value: T):
        self.__dict.__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        return self.__dict.__delitem__(key)

    def __len__(self) -> int:
        return self.__dict.__len__()

    def __contains__(self, key: str) -> bool:
        return self.__dict.__contains__(key)

    def __iter__(
        self,
    ) -> Iterable[T]:  # iterate over objects rather than keys
        return iter(self.__dict.values())
