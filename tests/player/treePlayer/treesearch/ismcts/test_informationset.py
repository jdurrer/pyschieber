import pytest

from pyschieber.card import Card
from pyschieber.player.rulebased_player.strategy.flags.flags import (
    FailedToServeSuitFlag,
)
from pyschieber.player.treePlayer.treePlayer import TreePlayer
from pyschieber.player.treePlayer.treesearch.ismcts.informationset import (
    Informationset,
    initialize_card_distribution,
)
from pyschieber.suit import Suit


class DummyCardCounter:
    def __init__(self) -> None:
        self.played_cards: list[list[Card]] = [[], [], [], []]
        self.flags: list[list[FailedToServeSuitFlag]] = [[] for _ in range(4)]
        self._remaining_by_suit: dict[Suit, list[Card]] = {}

    def cards_played(self) -> list[Card]:
        return [card for cards in self.played_cards for card in cards]

    def remaining_by_suit(self, color: Suit) -> list[Card]:
        return self._remaining_by_suit.get(color, [])

    def set_remaining_by_suit(self, color: Suit, cards: list[Card]) -> None:
        self._remaining_by_suit[color] = cards


class DummyStrategy:
    def __init__(self) -> None:
        self.card_counter = DummyCardCounter()


class DummyTreePlayer(TreePlayer):
    """Minimal TreePlayer stub for testing Informationset."""

    def __init__(self, player_id: int, cards: list[Card]) -> None:
        self.id = player_id
        self.cards = cards
        self.strategy = DummyStrategy()


def test_constrain_cards_zero_flag_disallows_player() -> None:
    """constrain_cards should set the player's possibility to 0 when flag is 0."""
    player = DummyTreePlayer(player_id=0, cards=[])
    infoset = Informationset(player)

    possible = [[1, 1, 1, 1] for _ in range(3)]
    cards_constraint = [0, 1, 0]

    updated = infoset.constrain_cards(possible, cards_constraint, player_id=2)

    # card 0 and 2: flag 0 => player 2 disallowed
    assert updated[0][2] == 0
    assert updated[2][2] == 0
    # card 1: flag 1 => unchanged
    assert updated[1][2] == 1


def test_constrain_cards_length_mismatch_raises() -> None:
    """constrain_cards should raise when constraint length does not match cards."""
    player = DummyTreePlayer(player_id=0, cards=[])
    infoset = Informationset(player)

    possible = [[1, 1, 1, 1] for _ in range(2)]
    cards_constraint = [0]  # wrong length

    with pytest.raises(ValueError):
        infoset.constrain_cards(possible, cards_constraint, player_id=1)


def test_restrict_cards_to_single_player_enforces_exclusive_holding() -> None:
    """restrict_cards_to_single_player should make one player exclusive holder of flagged cards."""
    player = DummyTreePlayer(player_id=1, cards=[])
    infoset = Informationset(player)

    possible = [[1, 1, 1, 1] for _ in range(3)]
    cards_flags = [1, 0, 1]  # cards 0 and 2 must be held by player 1

    updated = infoset.restrict_cards_to_single_player(
        possible, cards_flags, player_id=1
    )

    # For cards with flag 1, only player 1 may hold (others set to 0)
    for card_index in (0, 2):
        assert updated[card_index][1] == 1
        for pid in (0, 2, 3):
            assert updated[card_index][pid] == 0

    # For cards with flag 0, player 1 must not hold
    assert updated[1][1] == 0


def test_exclude_suits_by_player_collects_remaining_cards() -> None:
    """exclude_suits_by_player should collect remaining cards for failed suits."""
    player = DummyTreePlayer(player_id=0, cards=[])
    # Prepare flags and remaining cards
    flag_bell = FailedToServeSuitFlag(color=Suit.BELL)
    player.strategy.card_counter.flags[2].append(flag_bell)

    bell_cards = [Card(Suit.BELL, rank) for rank in range(3)]
    player.strategy.card_counter.set_remaining_by_suit(Suit.BELL, bell_cards)

    infoset = Informationset(player)

    excluded = infoset.exclude_suits_by_player(player_id=2)
    assert excluded == bell_cards


def test_build_initial_possibility_matrix_shape_and_values() -> None:
    """_build_initial_possibility_matrix should create a 36x4 matrix of ones."""
    player = DummyTreePlayer(player_id=0, cards=[])
    infoset = Informationset(player)

    matrix = infoset._build_initial_possibility_matrix()
    assert len(matrix) == 36
    assert all(len(row) == 4 for row in matrix)
    assert all(all(v == 1 for v in row) for row in matrix)


def test_compute_handcard_lengths_uses_played_cards_count() -> None:
    """_compute_handcard_lengths should return 9 - played_count per player."""
    player = DummyTreePlayer(player_id=0, cards=[])
    player.strategy.card_counter.played_cards[0] = [Card(Suit.BELL, 1)]
    player.strategy.card_counter.played_cards[1] = [
        Card(Suit.ROSE, 2),
        Card(Suit.ROSE, 3),
    ]
    player.strategy.card_counter.played_cards[2] = []
    player.strategy.card_counter.played_cards[3] = [Card(Suit.SHIELD, 4)]

    infoset = Informationset(player)
    lengths = infoset._compute_handcard_lengths()
    assert lengths == [8, 7, 9, 8]


def test_initialize_card_distribution_returns_solver() -> None:
    """initialize_card_distribution should create a CardDistributionSolver instance."""
    player_cards = [Card(Suit.BELL, 1), Card(Suit.ROSE, 2)]
    player = DummyTreePlayer(player_id=0, cards=player_cards)

    solver = initialize_card_distribution(player)

    # Basic sanity: solver has matching number_of_cards and number_of_players
    assert solver.number_of_cards == 36
    assert solver.number_of_players == 4
