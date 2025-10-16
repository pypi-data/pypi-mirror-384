from types import ModuleType


class Check:
    def __init__(self, module: ModuleType):
        self.module = module

    @property
    def name(self):
        return self.module.__name__.split('.')[-1]