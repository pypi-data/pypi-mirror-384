import asyncio

class EventPipe:
    __instance = None

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    def __init__(self):
        self.__callback = None

    @classmethod
    def attach_callback(cls, callback):
        cls.get_instance().set_callback(callback)

    def set_callback(self, callback):
        self.__callback = callback

    @classmethod
    async def submit(cls, event):
        await cls.get_instance().__do_submit(event)

    async def __do_submit(self, event):
        await self.__call_callback(event)

    async def __call_callback(self, event):
        if self.__callback is not None:
            await self.__callback(event)
            await asyncio.sleep(0)  # yield
