import functools
import asyncio
from dataclasses import dataclass
from .updates import Update

from ._events import EventPipe


@dataclass
class ProgressEvent:
    key: str
    label: str
    value: int
    total: int
    detail_level: Update.LevelOfDetail


@dataclass
class SectionEvent:
    key: str
    entered: bool


class Progress:
    __instance = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        self.bars: dict[str:ProgressBar] = {}

    # @classmethod
    # async def start_section(cls,key):
    #     inst = cls.get_instance()
    #     await inst.create_section(key)

    # async def create_section(self,key):
    #     await EventPipe.submit(ProgressSection(key=key))

    @classmethod
    async def new_tracker(cls, key, label, total, initial_value=0, detail_level=Update.LevelOfDetail.ALWAYS):
        inst = cls.get_instance()

        bar = ProgressBar(
            label,
            total,
            initial_value,
            functools.partial(inst.on_bar_update_callback, key),
            detail_level = detail_level
        )
        inst.bars[key] = bar
        await inst.on_bar_update_callback(key)
        return bar

    async def on_bar_update_callback(self, key):
        bar = self.bars[key]
        event = ProgressEvent(key, **bar.details)
        await EventPipe.submit(event)


class ProgressSection:
    def __init__(self, key):
        self.key = key

    async def __aenter__(self):
        await EventPipe.submit(SectionEvent(key=self.key, entered=True))
        await asyncio.sleep(0.2)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await EventPipe.submit(SectionEvent(key=self.key, entered=False))


class ProgressBar:
    def __init__(self, label, total, current, callback, detail_level):
        self.total = total
        self.current = current
        self.label = label
        self.callback = callback
        self.detail_level = detail_level

    async def update(self, value):
        self.current = value
        await self.callback()

    @property
    def details(self):
        return {"label": self.label, "value": self.current, "total": self.total, "detail_level":self.detail_level}
