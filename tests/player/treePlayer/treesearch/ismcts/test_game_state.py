import pytest

from pyschieber.card import Card
from pyschieber.player.treePlayer.treesearch.ismcts.game_state import (
    DummyTreePlayer,
    GameState,
)
from pyschieber.stich import PlayedCard, Stich
from pyschieber.suit import Suit
from pyschieber.team import Team
from pyschieber.trumpf import Trumpf


def _build_game_state(player_id: int = 0) -> GameState:
    players = [DummyTreePlayer(name=str(index)) for index in range(4)]

    for index, player in enumerate(players):
        player.id = index

    teams = [
        Team(players=[players[0], players[2]]),
        Team(players=[players[1], players[3]]),
    ]
    return GameState(teams=teams, id=player_id)


def test_current_player_raises_without_trick_or_table_cards() -> None:
    state = _build_game_state()

    with pytest.raises(IndexError):
        state.current_player()


def test_current_player_uses_table_position() -> None:
    state = _build_game_state()
    state.cards_on_table.append(
        PlayedCard(
            player=state.players[1],
            card=Card(Suit.BELL, 6),
        )
    )

    assert state.current_player() == 2


def test_information_state_string_includes_hand_separator() -> None:
    state = _build_game_state(player_id=3)
    state.current_player = lambda: 3

    assert state.information_state_string() == hash("-")


def test_apply_action_completes_a_trick() -> None:
    state = _build_game_state()
    state.trumpf = Trumpf.BELL

    # current_player() expects the latest completed trick to exist.
    state.stiche.append(
        Stich(
            player=state.players[0],
            played_cards=[PlayedCard(player=state.players[0], card=Card(Suit.BELL, 6))],
            trumpf=Trumpf.BELL,
        )
    )

    cards = [
        Card(Suit.BELL, 7),
        Card(Suit.BELL, 8),
        Card(Suit.BELL, 9),
        Card(Suit.BELL, 10),
    ]

    for card in cards:
        state.apply_action(card)

    assert state.cards_on_table == []
    assert len(state.stiche) == 2


def test_clone_is_independent() -> None:
    state = _build_game_state()
    clone = state.clone()

    clone.cards_on_table.append(
        PlayedCard(
            player=state.players[2],
            card=Card(Suit.ROSE, 8),
        )
    )

    assert state.cards_on_table == []
    assert len(clone.cards_on_table) == 1


def test_clone_copies_state_graph_without_sharing_mutable_objects() -> None:
    state = _build_game_state()
    state.trumpf = Trumpf.BELL
    state.point_limit = 42
    state.geschoben = True
    state.teams[0].points = 12
    state.players[0].cards = [Card(Suit.BELL, 6)]
    played_card = PlayedCard(
        player=state.players[1],
        card=Card(Suit.ROSE, 7),
    )
    state.cards_on_table = [played_card]
    state.stiche = [
        Stich(
            player=state.players[0],
            played_cards=[played_card],
            trumpf=Trumpf.BELL,
        )
    ]

    clone = state.clone()

    assert clone is not state
    assert clone.players[0] is not state.players[0]
    assert clone.teams[0] is not state.teams[0]
    assert clone.teams[0].players[0] is clone.players[0]
    assert clone.cards_on_table[0].player is clone.players[1]
    assert clone.stiche[0].player is clone.players[0]
    assert clone.stiche[0].played_cards[0].player is clone.players[1]
    assert clone.point_limit == state.point_limit
    assert clone.geschoben == state.geschoben
    assert clone.trumpf == state.trumpf
    assert clone.teams[0].points == state.teams[0].points

    clone.players[0].cards.clear()
    clone.teams[0].points = 99

    assert state.players[0].cards == [Card(Suit.BELL, 6)]
    assert state.teams[0].points == 12


def test_is_terminal_after_nine_tricks() -> None:
    state = _build_game_state()
    state.stiche = [object()] * 9

    assert state.is_terminal()


def test_is_not_terminal_before_nine_tricks() -> None:
    state = _build_game_state()
    state.stiche = [object()] * 8

    assert not state.is_terminal()
