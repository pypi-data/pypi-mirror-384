from ._events import EventPipe
import asyncio
from enum import IntEnum, Enum, unique


"""
Variants:
- "text" - free text entry
- "continue" - just an OK to continue
- "confirm" - yes/no
- "select" - choose from a list of options

"""


class Input:

    class Request:
        @unique
        class Variant(Enum):
            TEXT = "text"
            CONTINUE = "continue"
            CONFIRM = "confirm"
            SELECT = "select"

        def __init__(
            self, prompt: str, type: "Input.Request.Variant", options: dict = {}
        ):
            self.prompt = prompt

            try:
                self.variant = Input.Request.Variant(type)
            except ValueError:
                self.variant = Input.Request.Variant.TEXT

            if self.variant == Input.Request.Variant.SELECT:
                self.options = options

            loop = asyncio.get_event_loop()
            self.__response = loop.create_future()
            
            self.answer = None

        def resolve(self, response):
            self.answer = response
            self.__response.set_result(response)

        async def get_response(self):
            return await self.__response

        @property
        def resolved(self):
            return self.__response.done()

    @staticmethod
    async def make_request(payload):
        prompt = payload.get("prompt")
        variant = payload.get("variant", Input.Request.Variant.TEXT)
        options = payload.get("options", None)
        if not prompt:
            return None

        request = Input.Request(prompt, variant, options)
        await EventPipe.submit(request)
        return await request.get_response()
