from pyschieber.card import Card
from pyschieber.suit import Suit


def split_card_values_by_suit(cards: list[Card]) -> list[tuple[Suit, list[int]]]:
    """Splits a list of cards into groups of card values by suit.

    Returns a list of tuples, each containing a suit and a list of card values for that suit.

    Args:
        cards: List of Card objects to be grouped by suit.

    Returns:
        List of tuples, where each tuple contains a Suit and a list of integers representing card values.
    """
    suit_card_values: list[tuple[Suit, list[int]]] = []
    for suit in Suit:
        suit_cards: list[int] = [
            card.value for card in cards if card.suit.name == suit.name
        ]
        suit_card_values.append((suit, suit_cards))
    return suit_card_values


def split_cards_by_suit(cards: list[Card]) -> list[tuple[Suit, list[Card]]]:
    """Splits a list of cards into groups by suit.

    Returns a list of tuples, each containing a suit and a list of cards for that suit.

    Args:
        cards: List of Card objects to be grouped by suit.

    Returns:
        List of tuples, where each tuple contains a Suit and a list of Card objects.
    """
    suit_cards: list[tuple[Suit, list[Card]]] = []
    for suit in Suit:
        cards_per_suit: list[Card] = [
            card for card in cards if card.suit.name == suit.name
        ]
        suit_cards.append((suit, cards_per_suit))
    return suit_cards
