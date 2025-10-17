from astroid import FunctionDef
from pylint.lint import PyLinter

from kognitos.bdk.api import NounPhrase
from kognitos.bdk.klang.parser import KlangParser
from kognitos.bdk.linter.connect.rules.connect_rule import ConnectRule
from kognitos.bdk.linter.util import get_decorator_by_name


class NounPhraseRule(ConnectRule):
    def check_rule(self, linter: PyLinter, node: FunctionDef) -> None:
        noun_phrase = self.connect_noun_phrase(node)

        if noun_phrase:
            try:
                noun_phrases, _ = KlangParser.parse_noun_phrases(noun_phrase)
                if len(noun_phrases) > 1:
                    linter.add_message("connect-bad-noun-phrase", node=node)
            except SyntaxError:
                linter.add_message("connect-bad-noun-phrase", node=node)
        else:
            linter.add_message("connect-missing-noun-phrase", node=node, args=node.repr_name())

        for _, argument in enumerate(node.args.arguments):
            if noun_phrase and argument.repr_name() == NounPhrase.from_str(noun_phrase).to_snake_case():
                linter.add_message(
                    "connect-incompatible-noun-phrase",
                    args=(noun_phrase, argument.repr_name()),
                    node=argument,
                )

    def connect_noun_phrase(self, node: FunctionDef):
        decorator = get_decorator_by_name(node, "kognitos.bdk.decorators.connect_decorator.connect")

        if decorator and hasattr(decorator, "keywords") and len(decorator.keywords) > 0:
            name_keyword = next(filter(lambda x: x.arg == "noun_phrase", decorator.keywords), None)

            if name_keyword:
                return next(name_keyword.value.infer()).value

        return None
