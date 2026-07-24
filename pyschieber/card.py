# ----------------------------
# Libraries
# ----------------------------

from pyschieber.suit import Suit
from pyschieber.trumpf import Trumpf


class Card:
    names: dict[int, str] = {6: '6', 7: '7', 8: '8', 9: '9', 10: 'Banner', 11: 'Under', 12: 'Ober', 13: 'Koennig', 14: 'Ass'}
    values: dict[str, int] = {v: k for k, v in names.items()}
    trumpf_rank: dict[int, int] = {6: 6, 7: 7, 8: 8, 10: 10, 12: 12, 13: 13, 14: 14, 9: 15, 11: 16}
    format_string: str = '<{0}:{1}>'


    def __init__(self, suit: Suit, value: int) -> None:
        self.suit = suit
        self.value = value


    def __lt__(self, other: 'Card') -> bool:
        return self.value < other.value
    
    def __gt__(self, other: 'Card') -> bool:
        return self.value > other.value


    def __eq__(self, other: 'Card') -> bool: # type: ignore
        return self.suit == other.suit and self.value == other.value


    def __hash__(self) -> int:
        return hash(str(self))


    def __str__(self) -> str:
        """Returns a string representation of the card.
        Formats the card's suit and value into a human-readable string.

        Returns:
            str: The formatted string representing the card.
        """
        name = Card.names[self.value] if self.value > 9 else str(self.value)
        return self.format_string.format(self.suit.name, name)


    def __repr__(self) -> str:
        return str(self)


    def get_trumpf_rank(self) -> int:
        return self.trumpf_rank[self.value]


    def is_higher_trumpf_than(self, other: 'Card') -> bool:
        """Determines if this card has a higher trumpf rank than another card.
        Compares the trumpf ranks of two cards and returns True if this card's trumpf rank is greater.
        
        DOES NOT CHECK IF BOTH CARDS ARE TRUMPF!

        Args:
            other (Card): The card to compare against.

        Returns:
            bool: True if this card's trumpf rank is higher, False otherwise.
        """
        return self.get_trumpf_rank() > other.get_trumpf_rank()


    def is_higher_than(self, other: 'Card') -> bool:
        return self.suit == other.suit and self.value > other.value


    def get_score(self, trumpf: Trumpf) -> int:
        if trumpf.name == self.suit.name:
            return 50 + self.get_trumpf_rank()
        else:
            return self.value


def from_string_to_card(card_string: str) -> Card:
    """Takes a card string <{suit}:{value}> and converts it to a Card.

    Args:
        card_string (str): format_string

    Returns:
        Card: Card as Card-Class
    """

    # Remove surrounding "<" and ">"
    card_string = card_string[1:-1]

    # Split into suit and value part
    suit_name: str; value_name: str; suit_name, value_name= card_string.split(':')

    # Convert strings to actual types
    card_suit: Suit = Suit[suit_name]
    card_value: int = Card.values[value_name]

    return Card(suit=card_suit, value=card_value)