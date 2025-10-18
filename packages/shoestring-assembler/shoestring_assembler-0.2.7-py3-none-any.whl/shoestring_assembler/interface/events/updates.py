from enum import IntEnum, Enum, unique

from dataclasses import dataclass

from ._events import EventPipe


class Update:
    @dataclass
    class Event:
        type: "Update.Type"
        lod: "Update.LevelOfDetail"
        content: str

    @unique
    class Type(Enum):
        STAGE = 0
        STEP = 1
        INFO = 2
        WARNING = 3
        ERROR = 4
        SUCCESS = 5
        DEBUG = 6
        ATTENTION = 7
        NOTIFY = 8

    @unique
    class LevelOfDetail(IntEnum):
        ALWAYS = 0
        ALWAYS_CLI_ONLY = 1
        FEEDBACK = 2
        DEBUG = 5

    @staticmethod
    async def StageHeading(stage):
        await EventPipe.submit(
            Update.Event(Update.Type.STAGE, Update.LevelOfDetail.ALWAYS, content=stage)
        )

    @staticmethod
    async def StepHeading(section):
        await EventPipe.submit(
            Update.Event(Update.Type.STEP, Update.LevelOfDetail.ALWAYS, content=section)
        )

    @staticmethod
    async def InfoMsg(content, detail_level=None):
        if detail_level is None:
            detail_level = Update.LevelOfDetail.ALWAYS
        await EventPipe.submit(
            Update.Event(Update.Type.INFO, detail_level, content=content)
        )

    @staticmethod
    async def WarningMsg(content):
        await EventPipe.submit(
            Update.Event(
                Update.Type.WARNING, Update.LevelOfDetail.ALWAYS, content=content
            )
        )

    @staticmethod
    async def ErrorMsg(content):
        await EventPipe.submit(
            Update.Event(
                Update.Type.ERROR, Update.LevelOfDetail.ALWAYS, content=content
            )
        )

    @staticmethod
    async def SuccessMsg(content):
        await EventPipe.submit(
            Update.Event(
                Update.Type.SUCCESS, Update.LevelOfDetail.ALWAYS, content=content
            )
        )

    @staticmethod
    async def DebugLog(content):
        await EventPipe.submit(
            Update.Event(
                Update.Type.DEBUG, Update.LevelOfDetail.ALWAYS, content=content
            )
        )

    @staticmethod
    async def AttentionMsg(content):
        await EventPipe.submit(
            Update.Event(
                Update.Type.ATTENTION, Update.LevelOfDetail.ALWAYS, content=content
            )
        )

    @staticmethod
    async def NotifyMsg(content):
        await EventPipe.submit(
            Update.Event(
                Update.Type.NOTIFY, Update.LevelOfDetail.ALWAYS, content=content
            )
        )


class FatalError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
