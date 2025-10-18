from enum import Enum, unique

class Signal:
    pass


class BackSignal(Signal):
    pass


@unique
class Action(Enum):
    DOWNLOAD = "download"
    FIND = "find"
    UPDATE = "update"
    ASSEMBLE = "assemble"
    RECONFIGURE = "reconfigure"
    BUILD = "build"
    SETUP = "setup"
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    EDIT = "edit"
    REMOVE = "remove"


class ActionSignal(Signal):
    def __init__(
        self,
        action: Action,
        solution = None
    ):
        super().__init__()
        self.action = action
        self.solution = solution
