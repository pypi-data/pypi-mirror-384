from astroid import FunctionDef, Name, nodes
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter

from kognitos.bdk.docstring import DocstringParseError, DocstringParser
from kognitos.bdk.klang.parser import KlangParser
from kognitos.bdk.linter.concept.concept_rule_factory import (
    ConceptRuleFactory, DefaultConceptRuleFactory)

from .. import util


class ConceptChecker(BaseChecker):
    """
    ConceptChecker class checks if a class is a concept by looking for a specific decorator. It also
    checks if the concept has the required documentation block, and the necessary serialization methods.
    """

    name = "kognitos-concept-checker"
    msgs = {
        "C7901": (  # message id
            # template of displayed message
            "Concept %s is missing description",
            # message symbol
            "concept-missing-description",
            # message description
            "All concepts must have a description",
        ),
        "C7903": (  # message id
            # template of displayed message
            "Concept %s is missing documentation",
            # message symbol
            "concept-missing-documentation",
            # message description
            "All concepts must have a documentation block attached to them",
        ),
        "C7904": (  # message id
            # template of displayed message
            "Unable to parse documentation block for book %s",
            # message symbol
            "concept-bad-documentation",
            # message description
            "All concepts must have a correct documentation string attached to them",
        ),
        "C7905": (  # message id
            # template of displayed message
            "The concept %s is missing method from_bytes",
            # message symbol
            "concept-missing-from-bytes",
            # message description
            "All concepts must have a method called from_bytes that allows to serialize it",
        ),
        "C7906": (  # message id
            # template of displayed message
            "The concept %s is missing method to_bytes",
            # message symbol
            "concept-missing-to-bytes",
            # message description
            "All concepts must have a method called to_bytes that allows to deserialize it",
        ),
        "C7907": (  # message id
            # template of displayed message
            "The concept %s function from_bytes is not a classmethod",
            # message symbol
            "concept-from-bytes-not-class-method",
            # message description
            "The `from_bytes` function must be a classmethod.",
        ),
        "C7908": (  # message id
            # template of displayed message
            "The concept %s function to_bytes is not a method",
            # message symbol
            "concept-to-bytes-not-method",
            # message description
            "The `to_bytes` function must be a method.",
        ),
        "C7909": (  # message id
            # template of displayed message
            "The concept %s function from_bytes has a bad signature",
            # message symbol
            "concept-from-bytes-bad-signature",
            # message description
            "The `from_bytes` function must be a from_bytes(cls, data: bytes) -> Self.",
        ),
        "C7910": (  # message id
            # template of displayed message
            "The concept %s function to_bytes has a bad signature",
            # message symbol
            "concept-to-bytes-bad-signature",
            # message description
            "The `to_bytes` function must be a to_bytes(self) -> bytes.",
        ),
        "C7911": (  # message id
            # template of displayed message
            "The concept %s is missing is_a",
            # message symbol
            "concept-missing-is-a",
            # message description
            "All concepts must have an is_a value",
        ),
        "C7912": (  # message id
            # template of displayed message
            "Cannot parse name for concept %s. '%s' is not a valid noun phrase",
            # message symbol
            "concept-cannot-parse-english",
            # message description
            "All concepts must have a well formed noun phrase as their name",
        ),
        "C7913": (  # message id
            # template of displayed message
            "The concept %s is a partial dataclass or attrs. It inherits from %s that is not a dataclass or attrs",
            # message symbol
            "concept-invalid-class",
            # message description
            "All dataclass or attrs concepts must inherit from dataclasses or attrs and be a dataclass or attrs themselves. Make sure you're not missing a @dataclass or @define decorator",
        ),
        "C7914": (  # message id
            # template of displayed message
            "The concept %s is missing attribute %s in the docstring",
            # message symbol
            "concept-missing-attribute-docstring",
            # message description
            "All dataclass concepts must have all their attributes documented in the docstring",
        ),
        "C7915": (  # message id
            # template of displayed message
            "The concept '%s' has an invalid type '%s' on field '%s' on class '%s'",
            # message symbol
            "concept-invalid-type",
            # message description
            "All dataclass concepts must have valid types for their attributes",
        ),
        "C7916": (  # message id
            # template of displayed message
            "The concept '%s' cannot have an `unset` field assignment",
            # message symbol
            "concept-wrong-unset-field-usage",
            # message description
            "Opaque concepts are not allowed to define an `unset` value. It should be used on dataclasses and attrs concepts.",
        ),
        "C7917": (  # message id
            # template of displayed message
            "The concept '%s' is_a field '%s' does not follow the pattern '%s %s'",
            # message symbol
            "concept-missing-book-name-in-is-a",
            # message description
            "All concepts must follow the pattern '{book_name} {noun}' in their is_a field.",
        ),
    }

    def __init__(
        self,
        linter: PyLinter,
        concept_rule_factory: ConceptRuleFactory = DefaultConceptRuleFactory(),
    ) -> None:
        super().__init__(linter)
        self.rules = concept_rule_factory.get_rules()

    @classmethod
    def is_concept(cls, node: nodes.ClassDef):
        return util.is_concept(node)

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        if ConceptChecker.is_concept(node):
            concept_is_a = util.concept_is_a(node)
            if not concept_is_a:
                self.add_message("concept-missing-is-a", node=node, args=node.name)
                return

            for is_a in concept_is_a:
                try:
                    KlangParser.parse_noun_phrases(is_a)
                except SyntaxError:
                    self.add_message("concept-cannot-parse-english", node=node, args=(node.name, is_a))

            for rule in self.rules:
                rule.check_rule(linter=self.linter, node=node)

            # check that it has a doc block
            if not node.doc_node:
                self.add_message("concept-missing-documentation", args=node.repr_name(), node=node)
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
                                "concept-missing-description",
                                args=node.repr_name(),
                                node=node.doc_node,
                            )
                    else:
                        self.add_message(
                            "concept-missing-description",
                            args=node.repr_name(),
                            node=node.doc_node,
                        )

                except DocstringParseError:
                    self.add_message(
                        "concept-bad-documentation",
                        args=node.repr_name(),
                        node=node.doc_node,
                    )

            is_from_bytes_present = False
            is_to_bytes_present = False

            if util.concept_unset_instance(node) and not util.is_dataclass_or_attrs(node):
                self.add_message("concept-wrong-unset-field-usage", args=(node.repr_name(),), node=node)

            if util.is_dataclass_or_attrs(node):
                fields = util.get_dataclass_field_names_recursive(node)

                # check all fields are documented in the @concept
                if node.doc_node:
                    try:
                        missing_attributes = util.get_missing_attributes_in_docstring(fields, node.doc_node.value)
                        for ma in missing_attributes:
                            self.add_message(
                                "concept-missing-attribute-docstring",
                                args=(node.repr_name(), ma),
                                node=node,
                            )
                    except DocstringParseError:
                        pass

                # check all fields have valid types
                nodes_with_invalid_types = util.get_invalid_type_nodes(node)
                for invalid_node in nodes_with_invalid_types:
                    concept_name = node.repr_name()
                    invalid_type_name = invalid_node.repr_name()

                    if not isinstance(invalid_node, (nodes.AnnAssign, nodes.Assign)):
                        assign_node = util.get_first_assign_parent(invalid_node)
                    else:
                        assign_node = invalid_node

                    if assign_node:
                        field_name, class_name = util.get_field_and_class_name(assign_node)
                    else:
                        # NOTE: We should never reach this code. We're just covering ourselves in
                        # case we find a scenario we're not accounting for.
                        field_name = "unknown"
                        class_name = "unknown"

                    self.add_message(
                        "concept-invalid-type",
                        args=(concept_name, invalid_type_name, field_name, class_name),
                        node=invalid_node,
                    )
            elif util.is_partial_dataclass_or_attrs(node):
                partial_classes = util.get_partial_dataclass_or_attrs(node)
                self.add_message(
                    "concept-invalid-class",
                    args=(node.repr_name(), ", ".join(partial_classes)),
                    node=node,
                )
            else:
                for child_node in node.body:
                    if isinstance(child_node, FunctionDef):
                        if child_node.name == "from_bytes":
                            is_from_bytes_present = True

                            if child_node.type != "classmethod":
                                self.add_message(
                                    "concept-from-bytes-not-class-method",
                                    args=node.repr_name(),
                                    node=child_node,
                                )

                            if (
                                not child_node.args
                                or not child_node.args.args
                                or len(child_node.args.args) != 2
                                or not child_node.args.annotations
                                or len(child_node.args.annotations) != 2
                                or not isinstance(child_node.args.annotations[1], Name)
                                or not child_node.args.annotations[1].name == "bytes"
                                or not child_node.returns
                                or not isinstance(child_node.returns, Name)
                                or not child_node.returns.name == "Self"
                            ):
                                self.add_message(
                                    "concept-from-bytes-bad-signature",
                                    args=node.repr_name(),
                                    node=child_node,
                                )

                            continue

                        if child_node.name == "to_bytes":
                            is_to_bytes_present = True

                            if child_node.type != "method":
                                self.add_message(
                                    "concept-to-bytes-not-method",
                                    args=node.repr_name(),
                                    node=child_node,
                                )

                            if (
                                not child_node.args.args
                                or len(child_node.args.args) != 1
                                or not child_node.args.annotations
                                or len(child_node.args.annotations) != 1
                                or not child_node.returns
                                or not isinstance(child_node.returns, Name)
                                or not child_node.returns.name == "bytes"
                            ):
                                self.add_message(
                                    "concept-to-bytes-bad-signature",
                                    args=node.repr_name(),
                                    node=child_node,
                                )

                            continue

                if not is_from_bytes_present:
                    self.add_message(
                        "concept-missing-from-bytes",
                        args=node.repr_name(),
                        node=node,
                    )

                if not is_to_bytes_present:
                    self.add_message(
                        "concept-missing-to-bytes",
                        args=node.repr_name(),
                        node=node,
                    )
