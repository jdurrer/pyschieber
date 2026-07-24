# Type Annotation
from pyschieber.player.base_player import BasePlayer
from pyschieber.card import Card
from pyschieber.suit import Suit
from pyschieber.player.challenge_player.strategy.mode.mode import Mode
from typing import List, Tuple, Dict

# Code
from pyschieber.player.challenge_player.strategy.mode.trumpf_color_mode import TrumpfColorMode
from pyschieber.player.challenge_player.strategy.mode.top_down_mode import TopDownMode
from pyschieber.player.challenge_player.strategy.mode.bottom_up_mode import BottomUpMode
from pyschieber.player.challenge_player.strategy.card_counter import CardCounter, get_mode
from pyschieber.trumpf import Trumpf


class JassStrategy:

    def __init__(self, player: BasePlayer):
        self.me = player
        self.card_counter = CardCounter(player)


    def chose_trumpf(self, cards: Card, geschoben: bool) -> Trumpf:
        scores: List[Tuple[str, int]] = []

        if not geschoben:
            scores.append((Trumpf.SCHIEBEN, 54))

        tdm:TopDownMode = TopDownMode()
        scores.append((Trumpf.OBE_ABE, tdm.calculate_mode_score(cards, geschoben)))

        bum:BottomUpMode = BottomUpMode()
        scores.append((Trumpf.UNDE_UFE, bum.calculate_mode_score(cards, geschoben)))

        for suit in Suit:
            tcm:TrumpfColorMode = TrumpfColorMode(suit)
            scores.append((Trumpf[suit.name], tcm.calculate_mode_score(cards, geschoben)))

        return max(scores, key=lambda x: x[1])[0]


    def choose_card(self, allowed_cards: List[Card], state: Dict, role: str) -> Mode:
        mode: Mode = get_mode(state['trumpf'])
        return mode.get_card_to_play(allowed_cards, self.card_counter, state, role)


    def move_made(self, player_id: int, card: Card, state: Dict) -> None:
        self.card_counter.card_played(player_id, card, state)