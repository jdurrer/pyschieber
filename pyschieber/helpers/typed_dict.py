from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NoReturn  # Required for Python < 3.9

from pyschieber.card import Card
from pyschieber.trumpf import Trumpf

if TYPE_CHECKING:
    from pyschieber.game import StatusDict


def main() -> None:
    print("This file is a helper file for typehinting.")


if __name__ == "__main__":
    main()


@dataclass(slots=True)
class TypedDictPlayer:
    name: str
    cards: list[Card]
    trumpf_list: list[Trumpf]
    id: int | None

    def get_dict(self) -> dict[str, type]: ...

    def set_card(self, card: Card) -> None: ...

    def choose_trumpf(self, geschoben: bool) -> NoReturn: ...

    def choose_card(self, state: dict) -> Card: ...

    def move_made(self, player_id: int, card: Card, state: dict): ...

    def stich_over(self, state: dict): ...

    def game_started(self): ...

    def allowed_cards(self, state: dict) -> list[Card]: ...

    def choose_card_treesearch(self, state: StatusDict) -> list[Card]: ...
