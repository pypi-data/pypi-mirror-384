from astroid import nodes
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

from kognitos.bdk.docstring import DocstringParseError, DocstringParser
from kognitos.bdk.klang.parser import KlangParser
from kognitos.bdk.linter.connect.connect_rule_factory import (
    ConnectRuleFactory, DefaultConnectRuleFactory)

from .. import util


class ConnectChecker(BaseChecker):
    """
    ConnectChecker

    This class is responsible for checking the documentation and type annotations of connect methods.
    """

    name = "kognitos-connect-checker"
    msgs = {
        "C7501": (  # message id
            # template of displayed message
            "Connect %s is missing description",
            # message symbol
            "connect-missing-description",
            # message description
            "All connect methods must have a description",
        ),
        "C7503": (  # message id
            # template of displayed message
            "Connect %s is missing documentation",
            # message symbol
            "connect-missing-documentation",
            # message description
            "All connect methods must have a documentation block attached to them",
        ),
        "C7504": (  # message id
            # template of displayed message
            "Unable to parse documentation block for function %s: %s",
            # message symbol
            "connect-bad-documentation",
            # message description
            "All connect methods must have a correct documentation string attached to them",
        ),
        "C7505": (  # message id
            # template of displayed message
            "Missing type annotations for arg %s",
            # message symbol
            "connect-argument-missing-type-annotation",
            # message description
            "All connect methods must have all of their arguments annotated with type",
        ),
        "C7506": (  # message id
            # template of displayed message
            "Unsupported type for arg %s",
            # message symbol
            "connect-argument-unsupported-type",
            # message description
            "BCI supports a limited set of types",
        ),
        "C7507": (  # message id
            # template of displayed message
            "Unable to infer type for arg %s",
            # message symbol
            "connect-argument-cannot-infer-type",
            # message description
            "Internal Error. Unable to infer the type for the argument.",
        ),
        "C7508": (  # message id
            # template of displayed message
            "Missing description for arg %s",
            # message symbol
            "connect-missing-argument-description",
            # message description
            "All arguments must have a description",
        ),
        "C7509": (  # message id
            # template of displayed message
            "Missing label for arg %s",
            # message symbol
            "connect-missing-argument-label",
            # message description
            "All arguments must have a label",
        ),
        "C7510": (  # message id
            # template of displayed message
            "Connect has a bad noun phrase",
            # message symbol
            "connect-bad-noun-phrase",
            # message description
            "All connects should have a single noun phrase as their noun phrase",
        ),
        "C7511": (  # message id
            # template of displayed message
            "Connect label has a bad noun phrase",
            # message symbol
            "connect-label-bad-noun-phrase",
            # message description
            "All connects label should have a proper noun phrase",
        ),
        "C7512": (  # message id
            # template of displayed message
            "Connect's noun phrase '%s' is present as an argument '%s' in the method signature",
            # message symbol
            "connect-incompatible-noun-phrase",
            # message description
            "The connect's noun phrase should not be present as an argument in the method signature",
        ),
        "C7513": (  # message id
            # template of displayed message
            "Connect method '%s' noun phrase is missing",
            # message symbol
            "connect-missing-noun-phrase",
            # message description
            "All connects decorators should have a proper noun phrase",
        ),
        "C7514": (  # message id
            # template of displayed message
            "Connect method '%s' name is missing",
            # message symbol
            "connect-missing-name",
            # message description
            "All connects decorators should have a proper name",
        ),
        "C7515": (  # message id
            # template of displayed message
            "Connect method '%s' has a bad name - Should be capitalized",
            # message symbol
            "connect-bad-name",
            # message description
            "All connects decorators names should be non-empty and capitalized",
        ),
    }

    def __init__(self, linter: PyLinter, connect_rule_factory: ConnectRuleFactory = DefaultConnectRuleFactory()) -> None:
        super().__init__(linter)
        self.rules = connect_rule_factory.get_rules()

    @classmethod
    def is_connect(cls, node: nodes.FunctionDef):
        return bool(util.get_decorator_by_name(node, "kognitos.bdk.decorators.connect_decorator.connect"))

    def visit_functiondef(self, node: nodes.FunctionDef) -> None:
        if ConnectChecker.is_connect(node):
            for rule in self.rules:
                rule.check_rule(linter=self.linter, node=node)

            # check that it has a doc block
            if not node.doc_node:
                self.add_message("connect-missing-documentation", node=node)
            else:
                docstring = node.doc_node.value
                try:
                    parser = DocstringParser()
                    parsed_docstring = parser.parse(docstring)

                    # check short description
                    if parsed_docstring.short_description:
                        short_description = parsed_docstring.short_description.strip()
                        if not short_description:
                            self.add_message(
                                "connect-missing-description",
                                args=node.repr_name(),
                                node=node.doc_node,
                            )
                    else:
                        self.add_message(
                            "connect-missing-description",
                            args=node.repr_name(),
                            node=node.doc_node,
                        )

                    for idx, argument in enumerate(node.args.arguments):
                        if argument.repr_name() == "self":
                            continue

                        param = parsed_docstring.param_by_name(argument.name)
                        if not param or not param.description:
                            self.add_message(
                                "connect-missing-argument-description",
                                args=argument.name,
                                node=argument,
                            )

                        if not param or not param.label:
                            self.add_message(
                                "connect-missing-argument-label",
                                args=argument.name,
                                node=argument,
                            )
                        if param and param.label:
                            try:
                                noun_phrases, _ = KlangParser.parse_noun_phrases(param.label)
                                if len(noun_phrases) > 1:
                                    self.add_message("connect-label-bad-noun-phrase", args=param.label, node=argument)
                            except SyntaxError:
                                self.add_message("connect-label-bad-noun-phrase", args=param.label, node=argument)

                except DocstringParseError as ex:
                    self.add_message(
                        "connect-bad-documentation",
                        args=[node.repr_name(), str(ex)],
                        node=node.doc_node,
                    )

            for idx, argument in enumerate(node.args.arguments):
                if argument.repr_name() == "self":
                    continue

                annotation = node.args.annotations[idx]
                if annotation is None:
                    self.add_message(
                        "connect-argument-missing-type-annotation",
                        args=argument.repr_name(),
                        node=argument,
                    )
                else:
                    if not util.type_check_connect(annotation):
                        self.add_message(
                            "connect-argument-unsupported-type",
                            args=argument.repr_name(),
                            node=argument,
                        )
