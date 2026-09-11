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
from pyschieber.player.treePlayer.treesearch.ismcts.cpmpy_csp import (
    calculate_upper_world_boundary,
)
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
    def get_card_by_treesearch(self, status: Status) -> Card:
        evaluator = RandomRolloutEvaluator()
        informationset = initialize_card_distribution(self)
        upper_bound_informationset = min(
            200, calculate_upper_world_boundary(informationset)
        )
        informationset.set_hamming_distance(int(200 / upper_bound_informationset))
        ismcts = ISMCTSBot(
            evaluator,
            3500,
            informationset,
            max_world_samples=upper_bound_informationset,
        )
        game_state = rebuild_game(self, status)
        policy = ismcts.get_policy(game_state)
        return max(policy, key=itemgetter(1))[0]

    def choose_card(  # type: ignore
        self,
        state: StatusDict = None,  # type: ignore,
        max_remaining_handcards: int = 2,
    ) -> Generator[Card | None, None, None]:
        """Yields possible card choices until an allowed card is selected.

        This generator produces card options based on the current game state and player's role, continuing until an allowed card is confirmed.

        Args:
            state (StatusDict, optional): The current game state.
            max_remaining_handcards (int, optional): The maximum number of hand cards allowed before starting the treesearch. Defaults to 2.

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

            if (
                not isinstance(card, Card)
                and len(self.cards) <= max_remaining_handcards
            ):
                card = self.get_card_by_treesearch(status)

            if not isinstance(card, Card):
                card = random.choice(cards)
            allowed = yield card
            if allowed:
                yield None


if __name__ == "__main__":
    print("This script cannot be executed by itself...")
