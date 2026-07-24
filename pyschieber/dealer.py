
# ----------------------------
# Libraries
# ----------------------------
from typing import List
from pyschieber.helpers.typed_dict import TypedDictPlayer
from random import shuffle
from pyschieber.deck import Deck


class Dealer:

    def __init__(self, players: List[TypedDictPlayer]):
        self.players = players
        self.deck: Deck = Deck()

    
    def shuffle_cards(self) -> None:
        """
        Order Deck randomly
        """
        shuffle(self.deck.cards)


    def deal_cards_rotated(self) -> None:
        """Distributes cards to players after rotating the deck by one position.
        Ensures each player receives cards in a shifted order compared to the original deck sequence.

        Returns:
            None
        """
        self.deck.cards = self.deck.cards[-1:] + self.deck.cards[:-1]
        for i, card in enumerate(self.deck.cards):
            self.players[i % 4].set_card(card=card)


    def deal_cards(self) -> None:
        """Go through deck and give each player a card based on the deck's order.
        """
        for i, card in enumerate(self.deck.cards):
            self.players[i % 4].set_card(card=card)
        

    def show_deck(self) -> None:
        """Displays all cards currently in the deck.
        Prints each card in the deck to the standard output for inspection.

        Returns:
            None
        """    
        for card in enumerate(self.deck.cards):
            print(card)


def main() -> None:
    print('This file cannot be run by itself.')


if __name__ == '__main__':
    main()