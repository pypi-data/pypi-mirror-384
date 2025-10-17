import os
from typing import Iterable
from types import ModuleType
from pathlib import Path
from importlib import import_module
from debby import checks
from debby.core import Check


class Collector:
    
    def iter_check_module_names(self) -> Iterable[str]:
        for fn in  os.listdir(Path(checks.__file__).parent):
            if fn in ('__init__.py', '__pycache__'):
                continue
            else:
                yield fn.replace('.py', '')

    def import_check_module(self, module_name: str) -> ModuleType:
        import_path = f"debby.checks.{module_name}"
        return import_module(import_path)
    
    def iter_checks(self) -> Iterable[Check]:
        for module_name in self.iter_check_module_names():
            module = self.import_check_module(module_name)
            yield Check(module=module)
