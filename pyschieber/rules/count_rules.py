from typing import List, Dict
from pyschieber.trumpf import Trumpf
from pyschieber.card import Card


counting_factor: dict[Trumpf, int] = {
    Trumpf.ROSE: 1,
    Trumpf.ACORN: 1,
    Trumpf.BELL: 2,
    Trumpf.SHIELD: 2,
    Trumpf.OBE_ABE: 3,
    Trumpf.UNDE_UFE: 3
    }


points_obe_abe: dict[int, int] = {6: 0, 7: 0, 8: 8, 9: 0, 10: 10, 11: 2, 12: 3, 13: 4, 14: 11}
points_unde_ufe: dict[int, int] = {6: 11, 7: 0, 8: 8, 9: 0, 10: 10, 11: 2, 12: 3, 13: 4, 14: 0}
points_trumpf_color: dict[int, int] = {6: 0, 7: 0, 8: 0, 9: 14, 10: 10, 11: 20, 12: 3, 13: 4, 14: 11}
points_non_trumpf_color: dict[int, int] = {6: 0, 7: 0, 8: 0, 9: 0, 10: 10, 11: 2, 12: 3, 13: 4, 14: 11}


card_points: dict[Trumpf, dict[int, int]] = {Trumpf.OBE_ABE: points_obe_abe, Trumpf.UNDE_UFE: points_unde_ufe}


for trumpf in filter(lambda x: x not in [Trumpf.OBE_ABE, Trumpf.UNDE_UFE, Trumpf.SCHIEBEN], Trumpf):
    card_points[trumpf] = points_trumpf_color


def count_stich(cards: List[Card], trumpf: Trumpf, last: bool = False) -> int:
    """
    Calculates the total points for a stich (trick) based on the cards played and the current trumpf.

    Adds bonus points if the stich is the last one and sums the points for each card according to the trumpf rules.

    Args:
        cards (List[Card]): The list of cards played in the stich.
        trumpf (Trumpf): The current trumpf for the round.
        last (bool, optional): Whether this is the last stich of the round. Defaults to False.

    Returns:
        int: The total points scored in the stich.
    """
    return (5 if last else 0) + sum(
       (
            card_points[trumpf][card.value]
            if trumpf == Trumpf.OBE_ABE
            or trumpf == Trumpf.UNDE_UFE
            or card.suit.name == trumpf.name
            else points_non_trumpf_color[card.value]
        )
        for card in cards
    )
