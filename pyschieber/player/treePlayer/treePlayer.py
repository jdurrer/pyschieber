from __future__ import annotations

import random
from collections.abc import Generator
from operator import itemgetter

from pyschieber.card import Card
from pyschieber.game import StatusDict
from pyschieber.player.rulebased_player.helpers.state_dict_to_dataclass import (
    Status,
    translate_get_status_to_dataclass,
)
from pyschieber.player.rulebased_player.rulebased_player import RuleBasedPlayer
from pyschieber.player.treePlayer.treesearch.ismcts.evaluator import (
    RandomRolloutEvaluator,
)
from pyschieber.player.treePlayer.treesearch.ismcts.game_state import (
    rebuild_game,
)
from pyschieber.player.treePlayer.treesearch.ismcts.informationset import (
    initialize_card_distribution,
)
from pyschieber.player.treePlayer.treesearch.ismcts.ismcts import ISMCTSBot


class TreePlayer(RuleBasedPlayer):
    def choose_card(  # type: ignore
        self,
        state: StatusDict = None,  # type: ignore
    ) -> Generator[Card | None, None, None]:
        """Yields possible card choices until an allowed card is selected.

        This generator produces card options based on the current game state and player's role, continuing until an allowed card is confirmed.

        Args:
            state (StatusDict, optional): The current game state.

        Returns:
            Generator[Card | None, None, None]: Yields card choices and None when an allowed card is selected.
        """
        # Which role do we play this round?
        status: Status = translate_get_status_to_dataclass(state)
        if self.role_setting_required(status):
            self.set_player_role_by_state(status)

        # Get the Handcards, that we are allowed to play.
        cards = self.allowed_cards(state=state)

        # Choose the best card to play.
        allowed = False
        while not allowed:
            card = self.strategy.choose_card(cards, state)

            if not isinstance(card, Card) and len(self.cards) <= 3:
                evaluator = RandomRolloutEvaluator()
                informationset = initialize_card_distribution(self)
                ismcts = ISMCTSBot(
                    evaluator, 100, informationset
                )  # TODO  change the max_simulations of ISMCTSBot. make it dynamic based on how many cards are left?
                game_state = rebuild_game(self, status)
                policy = ismcts.get_policy(game_state)
                card = max(policy, key=itemgetter(1))[0]

            if not isinstance(card, Card):
                card = random.choice(cards)
            allowed = yield card
            if allowed:
                yield None


if __name__ == "__main__":
    print("This script cannot be executed by itself...")
