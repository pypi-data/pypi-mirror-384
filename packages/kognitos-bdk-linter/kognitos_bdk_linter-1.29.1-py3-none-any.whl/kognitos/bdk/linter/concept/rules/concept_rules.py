from abc import ABC, abstractmethod

from astroid import ClassDef
from pylint.lint import PyLinter

from kognitos.bdk.linter import util


class ConceptRule(ABC):
    @abstractmethod
    def check_rule(self, linter: PyLinter, node: ClassDef) -> None:
        pass


class ValidIsAConcept(ConceptRule):

    def check_rule(self, linter: PyLinter, node: ClassDef) -> None:

        concept_is_a = util.concept_is_a(node)
        book_names = util.find_book_names_in_project(node)
        if book_names:
            for is_a in concept_is_a:
                if not any(not util.validate_is_a_includes_book_name([is_a], book_name) for book_name in book_names):
                    noun = util.extract_noun_from_is_a(is_a, book_names[0])
                    linter.add_message(
                        "concept-missing-book-name-in-is-a",
                        args=(node.repr_name(), is_a, book_names[0], noun),
                        node=node,
                    )
