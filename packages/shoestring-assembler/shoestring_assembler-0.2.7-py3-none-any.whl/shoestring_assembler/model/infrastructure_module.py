from .base_module import BaseModule


class InfrastructureModule(BaseModule):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.type = "infrastructure"
