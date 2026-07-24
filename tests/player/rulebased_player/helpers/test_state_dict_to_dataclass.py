from typing import List

import pytest

from pyschieber.player.treePlayer.helpers.state_dict_to_dataclass import (
    PlayedCardsDataclass,
    StichDataclass,
    Teamscore,
    Status,
    translate_get_status_to_dataclass,
    test_dict_translation,
)
from pyschieber.game import StatusDict


@pytest.fixture
def state() -> StatusDict:
    return {
        "stiche": [
            {
                "player_id": 0,
                "trumpf": "ROSE",
                "played_cards": [
                    {"player_id": 0, "card": "6ROSE"},
                    {"player_id": 1, "card": "7ROSE"},
                ],
            },
            {
                "player_id": 2,
                "trumpf": "BELL",
                "played_cards": [
                    {"player_id": 2, "card": "8BELL"},
                    {"player_id": 3, "card": "9BELL"},
                ],
            },
        ],
        "trumpf": "ACORN",
        "geschoben": True,
        "point_limit": 1000.0,
        "table": [
            {"player_id": 0, "card": "JACKROSE"},
            {"player_id": 3, "card": "KINGBELL"},
        ],
        "teams": [
            {"points": 250},
            {"points": 300},
        ],
    }


def test_translate_get_status_to_dataclass_structure_and_types(state: StatusDict) -> None:
    status = translate_get_status_to_dataclass(state)

    assert isinstance(status, Status)
    assert isinstance(status.stiche, list)
    assert isinstance(status.table, list)
    assert isinstance(status.teams, list)

    for stich in status.stiche:
        assert isinstance(stich, StichDataclass)
        assert isinstance(stich.played_cards, list)
        for pc in stich.played_cards:
            assert isinstance(pc, PlayedCardsDataclass)

    for tablecard in status.table:
        assert isinstance(tablecard, PlayedCardsDataclass)

    for team in status.teams:
        assert isinstance(team, Teamscore)


def test_translate_get_status_to_dataclass_values_match(state: StatusDict) -> None:
    status = translate_get_status_to_dataclass(state)

    # stiche
    assert len(status.stiche) == len(state["stiche"])
    for stich_state, stich_status in zip(state["stiche"], status.stiche):
        assert stich_status.player_id == stich_state["player_id"]
        assert stich_status.trumpf == stich_state["trumpf"]
        assert len(stich_status.played_cards) == len(stich_state["played_cards"])
        for pc_state, pc_status in zip(stich_state["played_cards"], stich_status.played_cards):
            assert pc_status.player_id == pc_state["player_id"]
            assert pc_status.card == pc_state["card"]

    # scalar fields
    assert status.trumpf == state["trumpf"]
    assert status.geschoben == state["geschoben"]
    assert status.point_limit == state["point_limit"]

    # table
    assert len(status.table) == len(state["table"])
    for table_state, table_status in zip(state["table"], status.table):
        assert table_status.player_id == table_state["player_id"]
        assert table_status.card == table_state["card"]

    # teams
    assert len(status.teams) == len(state["teams"])
    for team_state, team_status in zip(state["teams"], status.teams):
        assert team_status.points == team_state["points"]


def test_translate_get_status_to_dataclass_empty_lists() -> None:
    empty_state: StatusDict = {
        "stiche": [],
        "trumpf": "SCHIEBEN",
        "geschoben": False,
        "point_limit": 0.0,
        "table": [],
        "teams": [],
    }

    status = translate_get_status_to_dataclass(empty_state)

    assert status.stiche == []
    assert status.table == []
    assert status.teams == []
    assert status.trumpf == "SCHIEBEN"
    assert status.geschoben is False
    assert status.point_limit == 0.0


def test_test_dict_translation_helper_passes_for_valid_state(state: StatusDict) -> None:
    # This function uses assertions internally; if they all pass, no exception is raised.
    test_dict_translation(state)
