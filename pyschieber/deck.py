# ----------------------------
# Libraries
# ----------------------------

from typing import List  # Required for Python < 3.9
from pyschieber.suit import Suit
from pyschieber.card import Card


class Deck:
    """
        Initializes a new deck containing all cards for each suit and value.

        The deck is populated with cards from all suits, with values ranging from 6 to 14.
        """
    def __init__(self) -> None:
        self.cards: List[Card] = []
        for suit in Suit:
            self.cards += [Card(suit=suit, value=i) for i in range(6, 15)]


    def __str__(self) -> str:
        """
        Returns a user-friendly string representation of the deck by joining card strings with a separator.

        Returns:
            str: A string of all cards in the deck, separated by commas.
        """
        return str([str(card) for card in self.cards])
    

def main() -> None:
    deck = Deck()
    print(deck)

    
if __name__ == '__main__':
    main()