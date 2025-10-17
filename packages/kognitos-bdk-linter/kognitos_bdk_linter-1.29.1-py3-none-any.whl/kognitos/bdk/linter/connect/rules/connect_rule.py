from abc import ABC, abstractmethod

from astroid import FunctionDef
from pylint.lint import PyLinter


class ConnectRule(ABC):
    @abstractmethod
    def check_rule(self, linter: PyLinter, node: FunctionDef) -> None:
        pass
