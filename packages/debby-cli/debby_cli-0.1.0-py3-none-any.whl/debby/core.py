import inspect
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING
from types import ModuleType


if TYPE_CHECKING:
    from .runner import RunStatus



class CheckResultStatus(Enum):
    passing = "pass"
    failing = "fail"
    warning = "warn"
    error = "error"


@dataclass
class CheckResult:
    check_instance: "CheckInstance"
    status: CheckResultStatus


class Check:
    def __init__(self, module: ModuleType):
        self.module = module

    @property
    def name(self):
        return self.module.__name__.split('.')[-1]
    
    @property
    def docs(self):
        return self.module.__doc__

    @property
    def description(self):
        return self.module.description
    
    @property
    def parameters(self):
        return inspect.signature(self.runner()).parameters

    def runner(self) -> Callable[..., Any]:
        _runner = getattr(self.module, 'check')
        if not callable(_runner):
            raise ValueError(f"Unable to find valid 'check' method for {self.name}.")
        return _runner
    

class CheckInstance:
    def __init__(self, check: Check, node: dict[str, Any]):
        self.check = check
        self.node = node

    def run(self, run_status: "RunStatus") -> CheckResult:
        runner = self.check.runner()
        try:
            runner(self.node)
            status = CheckResultStatus.passing
            run_status.passing += 1
        except AssertionError:
            status = CheckResultStatus.failing
            run_status.failing += 1
        except Exception:
            status = CheckResultStatus.error
            run_status.errors += 1
        return CheckResult(check_instance=self, status=status)
