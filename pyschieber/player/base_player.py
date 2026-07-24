# ----------------------------
# Libraries
# ----------------------------

from pyschieber.card import Card
from typing import List, NoReturn, Optional  # Required for Python < 3.9

import inspect
from abc import ABC, abstractmethod

from pyschieber.card import from_string_to_card
from pyschieber.trumpf import Trumpf
from pyschieber.rules.stich_rules import allowed_cards


class BasePlayer:

    def __init__(self, name: str = 'unknown') -> None:
        self.name = name
        self.cards: List[Card] = []
        self.trumpf_list: List[Trumpf] = list(Trumpf)
        self.id: int | None = None
        self.role: Optional[str] = None


    def get_dict(self) -> dict[str, str]:
        return dict(name=self.name, type=type(self).__name__)


    def set_card(self, card: Card) -> None:
        self.cards.append(card)


    @abstractmethod
    def choose_trumpf(self, geschoben: bool) -> NoReturn:
        raise NotImplementedError(str(inspect.stack()[1][3]))


    @abstractmethod
    def choose_card(self, state: dict | None = None) -> NoReturn:
        raise NotImplementedError(str(inspect.stack()[1][3]))


    @abstractmethod
    def move_made(self, player_id: int, card: Card, state: dict) -> None:
        pass


    @abstractmethod
    def stich_over(self, state: dict | None = None) -> None:
        pass


    @abstractmethod
    def game_started(self) -> None:
        pass


    def allowed_cards(self, state: dict) -> List[Card]:
        table_cards: List[Card] = [from_string_to_card(entry['card']) for entry in state['table']]
        trumpf: Trumpf = Trumpf[state['trumpf']]
        return allowed_cards(hand_cards=self.cards, table_cards=table_cards, trumpf=trumpf)


    def __str__(self) -> str:
        return f'<Player:{self.name}>'