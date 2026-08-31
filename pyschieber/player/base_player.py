# ----------------------------
# Libraries
# ----------------------------

from __future__ import annotations

import inspect
from abc import abstractmethod
from collections.abc import Generator
from typing import TYPE_CHECKING  # Required for Python < 3.9

from pyschieber.card import Card, from_string_to_card
from pyschieber.rules.stich_rules import allowed_cards
from pyschieber.trumpf import Trumpf

if TYPE_CHECKING:
    from pyschieber.game import StatusDict


class BasePlayer:
    def __init__(self, name: str = "unknown") -> None:
        self.name = name
        self.cards: list[Card] = []
        self.trumpf_list: list[Trumpf] = list(Trumpf)
        self.id: int | None = None
        self.role: str | None = None

    def get_dict(self) -> dict[str, str]:
        return {"name": self.name, "type": type(self).__name__}

    def set_card(self, card: Card) -> None:
        self.cards.append(card)

    @abstractmethod
    def choose_trumpf(self, geschoben: bool) -> Generator[str | None, None, None]:
        raise NotImplementedError(str(inspect.stack()[1][3]))

    @abstractmethod
    def choose_card(
        self, state: dict | None = None
    ) -> Generator[Card | None, None, None]:
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

    def allowed_cards(self, state: StatusDict) -> list[Card]:
        table_cards: list[Card] = [
            from_string_to_card(entry["card"])  # type: ignore
            for entry in state["table"]
        ]
        trumpf: Trumpf = Trumpf[state["trumpf"]]
        return allowed_cards(
            hand_cards=self.cards, table_cards=table_cards, trumpf=trumpf
        )

    def __str__(self) -> str:
        return f"<Player:{self.name}>"
