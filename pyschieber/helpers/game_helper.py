from pyschieber.suit import Suit
from pyschieber.card import Card

from typing import List, Tuple


def split_card_values_by_suit(cards: List[Card]) -> List[Tuple[Suit, List[int]]]:
    """Splits a list of cards into groups of card values by suit.
    
    Returns a list of tuples, each containing a suit and a list of card values for that suit.

    Args:
        cards: List of Card objects to be grouped by suit.

    Returns:
        List of tuples, where each tuple contains a Suit and a list of integers representing card values.
    """
    suit_card_values: List[Tuple[Suit, List[int]]] = []
    for suit in Suit:
        suit_cards: List[int] = [card.value for card in cards if card.suit.name == suit.name]
        suit_card_values.append((suit, suit_cards))
    return suit_card_values


def split_cards_by_suit(cards: List[Card]) -> List[Tuple[Suit, List[Card]]]:
    """Splits a list of cards into groups by suit.

    Returns a list of tuples, each containing a suit and a list of cards for that suit.

    Args:
        cards: List of Card objects to be grouped by suit.

    Returns:
        List of tuples, where each tuple contains a Suit and a list of Card objects.
    """
    suit_cards: List[Tuple[Suit, List[Card]]] = []
    for suit in Suit:
        cards_per_suit: List[Card] = [card for card in cards if card.suit.name == suit.name]
        suit_cards.append((suit, cards_per_suit))
    return suit_cards