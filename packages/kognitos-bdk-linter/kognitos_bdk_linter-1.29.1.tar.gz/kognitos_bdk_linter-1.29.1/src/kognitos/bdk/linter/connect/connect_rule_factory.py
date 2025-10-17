from abc import ABC, abstractmethod
from typing import List

from kognitos.bdk.linter.connect.rules.connect_rule import ConnectRule
from kognitos.bdk.linter.connect.rules.name_rule import NameRule
from kognitos.bdk.linter.connect.rules.noun_phrase_rule import NounPhraseRule


class ConnectRuleFactory(ABC):
    @abstractmethod
    def get_rules(self) -> List[ConnectRule]:
        pass


class DefaultConnectRuleFactory(ConnectRuleFactory):
    def get_rules(self) -> List[ConnectRule]:
        return [NounPhraseRule(), NameRule()]
