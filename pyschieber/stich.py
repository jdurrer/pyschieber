# ----------------------------
# Libraries
# ----------------------------
# from collections import namedtuple
from pyschieber.card import Card
from typing import List, TypedDict, Literal  # Required for Python < 3.9
from pyschieber.helpers.typed_dict import TypedDictPlayer
from pyschieber.trumpf import Trumpf
from dataclasses import dataclass


# PlayedCard = namedtuple('PlayedCard', ['player', 'card'])             # uncommented because was exchanged with dataclasses
# Stich = namedtuple('Stich', ['player', 'played_cards', 'trumpf'])     # uncommented because was exchanged with dataclasses


@dataclass(slots=True, frozen=True)
class PlayedCard:
    player: TypedDictPlayer
    card: Card


@dataclass(slots=True, frozen=True)
class Stich:
    player: TypedDictPlayer
    played_cards: List[PlayedCard]
    trumpf: Trumpf


class PlayedCardsDict(TypedDict):
    """ Type Hint for played_cards_dict function return."""
    player_id: int | None
    card: str


class StichDict(TypedDict):
    """ Type Hint for played_cards_dict function return."""
    player_id: int | None
    trumpf: Literal['ROSE', 'BELL', 'ACORN', 'SHIELD', 'OBE_ABE', 'UNDE_UFE', 'SCHIEBEN']
    played_cards: List[PlayedCardsDict]


def played_cards_dict(played_card: PlayedCard) -> PlayedCardsDict:
    return {
        'player_id': played_card.player.id,
        'card': str(played_card.card)
    }


def stich_dict(stich: Stich) -> StichDict:
    return {
        'player_id': stich.player.id,
        'trumpf': stich.trumpf.name,
        'played_cards': [played_cards_dict(played_card) for played_card in stich.played_cards]
    }