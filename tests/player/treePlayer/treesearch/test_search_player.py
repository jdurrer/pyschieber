import pytest

from pyschieber.card import Card
from pyschieber.player.rulebased_player.helpers.state_dict_to_dataclass import (
    Status,
    StatusDict,
)
from pyschieber.player.treePlayer.treesearch.search_player import SearchPlayer
from pyschieber.suit import Suit


class DummyStrategy:
    """Minimal strategy stub for testing SearchPlayer."""

    def __init__(self, chosen_card: Card | None = None) -> None:
        self._chosen_card = chosen_card

    def choose_card(self, cards: list[Card], state: StatusDict) -> Card | list[Card]:
        # Return a specific card if configured, otherwise return the full list.
        return self._chosen_card or cards


class DummySearchPlayer(SearchPlayer):
    """SearchPlayer stub overriding role and allowed-cards logic."""

    def __init__(self, cards: list[Card], chosen_card: Card | None = None) -> None:
        super().__init__(name="dummy")
        self.cards = cards
        self.strategy = DummyStrategy(chosen_card)
        self.role_setting_required_called = False
        self.set_player_role_by_state_called = False

    def role_setting_required(self, status: Status) -> bool:  # type: ignore[override]
        self.role_setting_required_called = True
        # For tests, always require role setting
        return True

    def set_player_role_by_state(self, status: Status) -> None:  # type: ignore[override]
        self.set_player_role_by_state_called = True

    def allowed_cards(self, state: StatusDict | None = None) -> list[Card]:  # type: ignore[override]
        # For tests, return all cards in hand
        return list(self.cards)


def build_dummy_status_dict() -> StatusDict:
    """Build a minimal valid StatusDict for SearchPlayer tests."""
    status: StatusDict = {
        "stiche": [
            {
                "player_id": 0,
                "trumpf": "ROSE",
                "played_cards": [
                    {"player_id": 0, "card": "ROSE-6"},
                    {"player_id": 1, "card": "BELL-7"},
                    {"player_id": 2, "card": "ACORN-8"},
                    {"player_id": 3, "card": "SHIELD-9"},
                ],
            }
        ],
        "trumpf": "ROSE",
        "geschoben": False,
        "point_limit": 1500.0,
        "table": [
            {"player_id": 0, "card": "ROSE-10"},
            {"player_id": 1, "card": "BELL-11"},
        ],
        "teams": [
            {"points": 500},
            {"points": 450},
        ],
    }
    return status


def test_choose_card_wraps_single_card_in_list() -> None:
    """If strategy returns a Card, choose_card should return a single-element list."""
    hand = [
        Card(value=6, suit=Suit.ROSE),
        Card(value=7, suit=Suit.BELL),
    ]
    chosen = hand[0]
    player = DummySearchPlayer(cards=hand, chosen_card=chosen)

    state_dict = build_dummy_status_dict()
    result = player.choose_card(state=state_dict)

    assert isinstance(result, list)
    assert result == [chosen]
    assert player.role_setting_required_called is True
    assert player.set_player_role_by_state_called is True


def test_choose_card_returns_cards_list_when_strategy_returns_list() -> None:
    """If strategy returns a list, choose_card should return that list unchanged."""
    hand = [
        Card(value=6, suit=Suit.ROSE),
        Card(value=7, suit=Suit.BELL),
        Card(value=8, suit=Suit.ACORN),
    ]
    # Strategy configured to return None => it will return `cards` list
    player = DummySearchPlayer(cards=hand, chosen_card=None)

    state_dict = build_dummy_status_dict()
    result = player.choose_card(state=state_dict)

    assert isinstance(result, list)
    assert result == hand
    assert player.role_setting_required_called is True
    assert player.set_player_role_by_state_called is True


def test_choose_card_asserts_on_empty_state() -> None:
    """choose_card should assert if given an empty/falsey state."""
    hand = [Card(value=9, suit=Suit.SHIELD)]
    player = DummySearchPlayer(cards=hand, chosen_card=hand[0])

    with pytest.raises(AssertionError):
        player.choose_card(state={})
