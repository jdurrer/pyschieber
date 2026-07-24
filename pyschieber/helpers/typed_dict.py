from typing import List, NoReturn  # Required for Python < 3.9
from dataclasses import dataclass
from pyschieber.card import Card
from pyschieber.trumpf import Trumpf


def main() -> None:
    print('This file is a helper file for typehinting.')
    
if __name__ == '__main__':
    main()


@dataclass(slots = True)
class TypedDictPlayer:
    name: str
    cards: List[Card]
    trumpf_list: List[Trumpf]
    id: int | None


    def get_dict(self) -> dict[str, type]:
        ...
        

    def set_card(self, card: Card) -> None:
        ...


    def choose_trumpf(self, geschoben: bool) -> NoReturn:
        ... 


    def choose_card(self, state: dict) -> Card:
        ...


    def move_made(self, player_id: int, card: Card, state: dict):
        ...


    def stich_over(self, state: dict):
        ...


    def game_started(self):
        ...


    def allowed_cards(self, state: dict) -> List[Card]:
        ...
