from astroid import FunctionDef
from pylint.lint import PyLinter

from kognitos.bdk.linter.connect.rules.connect_rule import ConnectRule
from kognitos.bdk.linter.util import get_decorator_by_name


class NameRule(ConnectRule):
    def check_rule(self, linter: PyLinter, node: FunctionDef) -> None:
        name = self.find_connect_name(node)

        if name:
            is_empty_or_not_capitalized = isinstance(name, str) and (not name or not name[0].isupper())
            if is_empty_or_not_capitalized:
                linter.add_message("connect-bad-name", node=node, args=node.repr_name())
        else:
            linter.add_message("connect-missing-name", node=node, args=node.repr_name())

    def find_connect_name(self, node: FunctionDef):
        decorator = get_decorator_by_name(node, "kognitos.bdk.decorators.connect_decorator.connect")

        if decorator and hasattr(decorator, "keywords") and len(decorator.keywords) > 0:
            name_keyword = next(filter(lambda x: x.arg == "name", decorator.keywords), None)

            if name_keyword:
                return next(name_keyword.value.infer()).value

        return None
