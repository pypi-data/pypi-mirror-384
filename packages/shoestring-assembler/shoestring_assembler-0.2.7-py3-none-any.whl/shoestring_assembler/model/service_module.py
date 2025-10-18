from pathlib import Path
from .base_module import BaseModule


class ServiceModuleModel(BaseModule):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.type = "service_module"
