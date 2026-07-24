# Type Annotation
from pyschieber.trumpf import Trumpf
from pyschieber.card import Card
from pyschieber.suit import Suit
from typing import List, Tuple, Literal
from pyschieber.player.base_player import BasePlayer

# Code
from pyschieber.player.treePlayer.strategy.mode.mode import Mode
from pyschieber.player.treePlayer.strategy.mode.trumpf_color_mode import TrumpfColorMode
from pyschieber.player.treePlayer.strategy.mode.top_down_mode import TopDownMode
from pyschieber.player.treePlayer.strategy.mode.bottom_up_mode import BottomUpMode
from pyschieber.player.treePlayer.strategy.card_counter import CardCounter
from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import translate_get_status_to_dataclass, StatusDict, Status


class JassStrategy:

    def __init__(self, player: BasePlayer) -> None:
        self.player = player
        self.card_counter: CardCounter = CardCounter(player)


    def chose_trumpf(self, cards: List[Card], geschoben: bool) -> str:
        """Choose best possible suit to make trumpf.

        Args:
            cards (Cards, list): Handcards
            geschoben (bool): if partner has geschoben.

        Returns:
            Trumpf: chosen Trumpf
        """
        scores: List[Tuple[str, int]] = []

        if not geschoben:
            scores.append((Trumpf.SCHIEBEN, 54))

        topdownmode = TopDownMode(self.card_counter)
        scores.append((Trumpf.OBE_ABE, topdownmode.calculate_mode_score(cards, geschoben)))

        bottomupmode = BottomUpMode(self.card_counter)
        scores.append((Trumpf.UNDE_UFE, bottomupmode.calculate_mode_score(cards, geschoben)))

        for suit in Suit:
            trumpfcolormode = TrumpfColorMode(suit, self.card_counter)
            scores.append((Trumpf[suit.name], trumpfcolormode.calculate_mode_score(cards, geschoben)))

        return max(scores, key=lambda x: x[1])[0]
    

    def get_mode(self, trumpf: Literal['ROSE', 'BELL', 'ACORN', 'SHIELD', 'OBE_ABE', 'UNDE_UFE', 'SCHIEBEN']) -> TopDownMode | BottomUpMode | TrumpfColorMode:
        """Returns the mode strategy object corresponding to the given trumpf.

        This function maps the trumpf value to its respective mode strategy class instance.
        
        Args:
            trumpf: The trumpf value indicating the current game mode.

        Returns:
            An instance of the mode strategy class corresponding to the trumpf.
        """
        return {
            'OBE_ABE': TopDownMode(self.card_counter),
            'UNDE_UFE': BottomUpMode(self.card_counter),
            'ROSE': TrumpfColorMode(Suit['ROSE'], self.card_counter),
            'BELL': TrumpfColorMode(Suit['BELL'], self.card_counter),
            'ACORN': TrumpfColorMode(Suit['ACORN'], self.card_counter),
            'SHIELD': TrumpfColorMode(Suit['SHIELD'], self.card_counter),
        }[trumpf]


    def choose_card(self, allowed_cards: List[Card], state: StatusDict) -> Card:
        """Choose a card to be played

        Args:
            allowed_cards (list, Cards): list of allowed cards to play
            state (dict): gamestate
            role (str): what role player plays.

        Returns:
            Card: best card to play.
        """
        status: Status = translate_get_status_to_dataclass(state)

        if len(allowed_cards) == 1:
            return allowed_cards[0]
        
        mode: Mode = self.get_mode(status.trumpf)
        return mode.get_card_to_play(allowed_cards, status, self.player.role)


    def move_made(self, player_id: int, card: Card, status: Status) -> None:
        """Keeps track of who did what (Players and played Cards).

        Args:
            player_id (int): ID of the player that took action.
            card (Card): The card they played.
            status(Status): current gamestate
        """
        mode: Mode = self.get_mode(status.trumpf)
        mode.card_played(player_id, card, status)


def main() -> None:
    print('This File cannot run on its own.')


if __name__ == '__main__':
    main()