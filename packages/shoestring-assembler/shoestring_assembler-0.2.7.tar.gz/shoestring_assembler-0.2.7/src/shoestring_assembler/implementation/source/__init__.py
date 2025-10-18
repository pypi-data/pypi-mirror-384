from shoestring_assembler.model.recipe import SourceSpec


class SourceABC:

    def __init__(self, source_spec, solution_root):
        self.source_spec = source_spec
        self.solution_root = solution_root

    async def fetch(self, dest_path) -> bool:
        raise NotImplementedError


class SourceImplementation:
    implementation_map = {}

    def __new__(cls, source_spec: SourceSpec,solution_root) -> SourceABC:
        impl_key = type(source_spec)
        if impl_key in cls.implementation_map:
            impl_cls = cls.implementation_map[impl_key]
            return impl_cls(source_spec, solution_root)
        raise ValueError(f"No implementation registered for source_type: {impl_key}")

    @classmethod
    def register(cls, key):
        def decorator(impl_cls):
            cls.implementation_map[key] = impl_cls
            return impl_cls

        return decorator


# slightly hacky way of making sure all contents are imported so they can be registered
from . import filesystem, git
