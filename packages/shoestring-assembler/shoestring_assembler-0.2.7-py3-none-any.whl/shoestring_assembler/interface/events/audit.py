from enum import Enum, unique
from dataclasses import dataclass

from ._events import EventPipe

@dataclass
class AuditEvent:
    context: list[str]
    type: 'Audit.Type'
    extra: dict


class Audit:
    __instance = None

    @unique
    class Type(Enum):
        Log = 0
        Expected = 1
        Unexpected = 2

        @classmethod
        def from_boolean(cls,value):
            if value:
                return cls.Expected
            else:
                return cls.Unexpected

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        self.context = {}
        self.id_counter = 1

    @classmethod
    async def submit(cls, source, event_type: Type, *_, **kwargs):
        await cls.get_instance().__do_submit(source, event_type, **kwargs)

    async def __do_submit(self, source, event_type: Type, **kwargs):
        context = self.context.values()
        full_context = ("::".join([*context, source])).split("::")

        await EventPipe.submit(AuditEvent(full_context, event_type, kwargs))

    def push_context(self, context_label):
        """
        returns context_id for use in pop
        expected to be used by
        with Context("<label>"):
            Audit.sumbit(...)
        """
        id = self.id_counter
        self.id_counter += 1
        self.context[id] = context_label
        return id

    def pop_context(self, context_id):
        del self.context[context_id]

    class Context:
        def __init__(self, context_label):
            self.context_label = context_label
            self.context_id = None

        def __enter__(self):
            self.context_id = Audit.get_instance().push_context(self.context_label)

        def __exit__(self, exc_type, exc_val, exc_tb):
            Audit.get_instance().pop_context(self.context_id)
