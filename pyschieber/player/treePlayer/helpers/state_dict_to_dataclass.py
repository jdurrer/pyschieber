# ----------------------------
# Libraries
# ----------------------------


from typing import List, Literal  # Required for Python < 3.9
from dataclasses import dataclass
from pyschieber.game import StatusDict


# ----------------------------
# Classes
# ----------------------------

@dataclass(frozen=True, slots=True)
class PlayedCardsDataclass:
    """ PlayedCardsDict, but as a dataclass."""
    player_id: int | None
    card: str


@dataclass(frozen=True, slots=True)
class StichDataclass:
    """ StichDict, but as a dataclass."""
    player_id: int | None
    trumpf: Literal['ROSE', 'BELL', 'ACORN', 'SHIELD', 'OBE_ABE', 'UNDE_UFE', 'SCHIEBEN']
    played_cards: List[PlayedCardsDataclass]


@dataclass(frozen=True, slots=True)
class Teamscore:
    points: int


@dataclass(slots=True,frozen=True)
class Status:
    stiche: List[StichDataclass]
    trumpf: Literal['ROSE', 'BELL', 'ACORN', 'SHIELD', 'OBE_ABE', 'UNDE_UFE', 'SCHIEBEN']
    geschoben: bool
    point_limit: float
    table: list[PlayedCardsDataclass]
    teams: list[Teamscore]


# ----------------------------
# Functions
# ----------------------------


def translate_get_status_to_dataclass(state: StatusDict) -> Status: 
    """
    Converts a StatusDict representing the current game state into a Status dataclass.

    This function translates the nested dictionary structure of the game status into corresponding dataclass instances for easier access and type safety.

    Args:
        state (StatusDict): The current game state as a dictionary.

    Returns:
        Status: The game state represented as a Status dataclass.
    """

    # translate state['stiche']
    stiche: List[StichDataclass] = []
    for stich in state['stiche']:
        played_cards: List[PlayedCardsDataclass] = []
        played_cards.extend(
            PlayedCardsDataclass(
                player_id=played_cards_dict['player_id'],
                card=played_cards_dict['card'],
            )
            for played_cards_dict in stich['played_cards']
        )
        stiche.append(StichDataclass(
            player_id = stich['player_id'],
            trumpf = stich['trumpf'],
            played_cards = played_cards))

    # translate state['table']
    table: List[PlayedCardsDataclass] = []
    table.extend(
        PlayedCardsDataclass(
            player_id=tablecard['player_id'],
            card=tablecard['card'],
        )
        for tablecard in state['table']
    )

    # translate state['teams']
    teams: List[Teamscore] = []
    teams.extend(Teamscore(points=team['points']) for team in state['teams'])

    return Status(
        stiche = stiche,
        trumpf = state['trumpf'],
        geschoben = state['geschoben'],
        point_limit = state['point_limit'],
        table = table,
        teams = teams,
    )


def test_dict_translation(state: StatusDict) -> None:
    """
    Tests the translation of a StatusDict to a Status dataclass.

    This function asserts that all fields in the Status dataclass match the corresponding fields in the original StatusDict after translation.

    Args:
        state (StatusDict): The current game state as a dictionary.

    Returns:
        None
    """
    status = translate_get_status_to_dataclass(state)
    # print(f"{state=}")
    # print(f"{status=}")

    # print(f'{state['stiche']=}')
    # print(f'{status.stiche=}')
    for state_stich, status_stich in zip(state['stiche'], status.stiche):
        assert status_stich.player_id == state_stich['player_id']
        assert status_stich.trumpf == state_stich['trumpf']
        for played_cards_state, played_cards_status in zip(state_stich['played_cards'], status_stich.played_cards):
            assert played_cards_status.player_id == played_cards_state['player_id']
            assert played_cards_status.card == played_cards_state['card']

    # print(f'{state['trumpf']=}')
    # print(f'{status.trumpf=}')
    assert status.trumpf == state['trumpf']

    # print(f'{state['geschoben']=}')
    # print(f'{status.geschoben=}')
    assert status.geschoben == state['geschoben']

    # print(f'{state['point_limit']=}')
    # print(f'{status.point_limit=}')
    assert status.point_limit == state['point_limit']
    
    # print(f'{state['table']=}')
    # print(f'{status.table=}')
    for tablecard_status, tablecard_state in zip(status.table, state['table']):
        assert tablecard_status.player_id == tablecard_state['player_id']
        assert tablecard_status.card == tablecard_state['card']

    # print(f'{state['teams']=}')
    # print(f'{status.teams=}')
    for status_team, state_team in zip(status.teams, state['teams']):
        assert status_team.points == state_team['points']

    # print()
    # print(f"{'-':->15s}")
    # print()