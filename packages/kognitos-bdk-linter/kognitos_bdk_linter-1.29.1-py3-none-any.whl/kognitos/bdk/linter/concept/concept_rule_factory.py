from abc import ABC, abstractmethod
from typing import List

from kognitos.bdk.linter.concept.rules.concept_rules import (ConceptRule,
                                                             ValidIsAConcept)


class ConceptRuleFactory(ABC):
    @abstractmethod
    def get_rules(self) -> List[ConceptRule]:
        pass


class DefaultConceptRuleFactory(ConceptRuleFactory):
    def get_rules(self) -> List[ConceptRule]:
        return [ValidIsAConcept()]
