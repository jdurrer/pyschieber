from __future__ import annotations

from pyschieber.card import Card
from pyschieber.game import StatusDict
from pyschieber.player.rulebased_player.helpers.state_dict_to_dataclass import (
    Status,
    translate_get_status_to_dataclass,
)
from pyschieber.player.rulebased_player.rulebased_player import RuleBasedPlayer


class SearchPlayer(RuleBasedPlayer):
    def choose_card(self, state: StatusDict) -> list[Card]:  # type: ignore
        """Yields possible card choices until an allowed card is selected.

        This generator produces card options based on the current game state and player's role, continuing until an allowed card is confirmed.

        Args:
            state (StatusDict, optional): The current game state.

        Returns:
            Generator[Card | None, None, None]: Yields card choices and None when an allowed card is selected.
        """
        assert state
        # Which role do we play this round?
        status: Status = translate_get_status_to_dataclass(state)
        if self.role_setting_required(status):
            self.set_player_role_by_state(status)

        # Get the Handcards, that we are allowed to play.
        cards = self.allowed_cards(state=state)

        card = self.strategy.choose_card(cards, state)
        return [card] if isinstance(card, Card) else cards


if __name__ == "__main__":
    print("This script cannot be executed by itself...")
