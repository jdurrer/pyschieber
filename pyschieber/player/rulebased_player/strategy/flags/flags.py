# Combines all Flag Classes in one file.
from typing import Union
from pyschieber.card import Card
from pyschieber.suit import Suit
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SuitVerworfenFlag:
    """Represents a flag indicating that a specific suit has been discarded.

    This class is used to mark that a player has thrown away cards of a particular suit, which can be used for inference in game strategy.

    Attributes:
        color (Suit): The suit that has been discarded.
    """
    color: Suit


@dataclass(slots=True, frozen=True)
class DoesntHaveCardFlag:
    """Represents a flag indicating that a specific card is not held by a player.

    This class is used to mark that a player does not possess a particular card, which can be used for inference in game strategy.

    Attributes:
        card (Card): The card that the player does not have.
    """
    card: Card


@dataclass(slots=True, frozen=True)
class FailedToServeSuitFlag:
    """Represents a flag indicating that a player failed to serve a specific suit.

    This class is used to mark that a player was unable to follow suit during play, which can be used for inference in game strategy.

    Attributes:
        color (Suit): The suit that was not served.
    """
    color: Suit


@dataclass(slots=True, frozen=True)
class SuitAngezogenFlag:
    """Represents a flag indicating that a specific suit has been drawn or is being held.

    This class is used to mark that a player is expected to hold or has drawn a particular suit, which can be used for inference in game strategy.

    Attributes:
        color (Suit): The suit that is being held or has been drawn.
    """
    color: Suit


@dataclass(slots=True, frozen=True)
class PreviouslyHadStichFlag:
    """Represents a flag indicating that a player has previously won a stich (trick).

    This class is used to mark that a player has already taken at least one stich, which can be used for inference in game strategy.
    """
    pass


@dataclass(slots=True)
class NumberOfTrumpfFlag:
    max: int
    min: int


Flag = Union[
    SuitVerworfenFlag,
    DoesntHaveCardFlag,
    FailedToServeSuitFlag,
    SuitAngezogenFlag,
    PreviouslyHadStichFlag,
    NumberOfTrumpfFlag
]