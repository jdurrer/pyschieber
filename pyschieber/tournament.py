import logging

from typing import List, Callable, Any, Tuple, Dict  # Required for Python < 3.9
from pyschieber.helpers.typed_dict import TypedDictPlayer
from pyschieber.helpers.custom_wrappers import time_function

from pyschieber.game import Game
from pyschieber.team import Team
import pickle
import time

logger = logging.getLogger(__name__)


class PlayerLimitReachedError(Exception):
    """Raised when trying to register more than the allowed number of players."""
    pass


class Tournament:

    def __init__(self, point_limit: float = 1500):
        self.point_limit = point_limit
        self.players: List[TypedDictPlayer] = []
        self.teams: List[Team] = []
        self.games: List[Game] = []


    def check_players(self) -> None:
        player_numbers: List[int] = []
        for index, player in enumerate(self.players):
            player_numbers.append(index)
        if set(player_numbers) != {0, 1, 2, 3}:
            raise ValueError(
                f"Player registration failed: expected player numbers {{0, 1, 2, 3}}, got {set(player_numbers)}"
            )


    def register_player(self, player: TypedDictPlayer) -> None:
        number_of_players: int = len(self.players)
        # assert number_of_players < 4
        if number_of_players >= 4:
            raise PlayerLimitReachedError("Cannot register more than 4 players.")
        self.players.append(player)
        player.id = number_of_players


    def build_teams(self) -> None:
        self.check_players()
        team_1: Team = Team(players=[self.players[0], self.players[2]])
        team_2: Team = Team(players=[self.players[1], self.players[3]])
        self.teams = [team_1, team_2]


    @time_function
    def play(self, rounds: int = 0, use_counting_factor: bool = True, allow_weis: bool = False, benchmark_enabled: bool = False) -> None:
        self.build_teams()
        logger.info(f'Tournament starts, the point limit is {self.point_limit}.')
        end: bool = False
        whole_rounds: bool = rounds > 0
        round_counter: int = 0
        benchmark_seed = 0

        while not end:
            benchmark_seed = set_benchmark_enabled(benchmark_enabled, round_counter, benchmark_seed)
            game = Game(teams=self.teams, point_limit=self.point_limit, use_counting_factor=use_counting_factor)
            self.games.append(game)
            logger.info('-' * 200)
            logger.info(f'Round {len(self.games)} starts.')
            logger.info('-' * 200)
            end = game.play(start_player_index=((len(self.games) - 1) % 4), whole_rounds=whole_rounds, allow_weis=allow_weis, benchmark_enabled=benchmark_enabled, benchmark_seed=benchmark_seed)
            logger.info(f'Round {len(self.games)} is over.')
            logger.info('Points: Team 1: {0} , Team 2: {1}. \n'.format(self.teams[0].points, self.teams[1].points))
            round_counter += 1
            if whole_rounds and round_counter == rounds:
                end = True
        # winning_team: int = 0 if self.teams[0].won(point_limit=self.point_limit) else 1
        logger.info(f' Team 0: {self.teams[0].points} vs {self.teams[1].points} Team 1.\n')
        save_games(self.games)
        self.reset()


    def get_status(self) -> Dict:
        return {
            'games': [game.get_status() for game in self.games],
            'players': [player.get_dict() for player in self.players]
        }


    def reset(self) -> None:
        self.games = []
        for player in self.players:
            player.cards = []


def set_benchmark_enabled(benchmark_enabled: bool, round_counter: int, benchmark_seed: float) -> float:
    """_summary_

    Args:
        benchmark_enabled (bool): True: benchmark_enabled is being used
        round_counter (int): Which round we are in.
        benchmark_seed (float): The seed to recreate the same hands.

    Returns:
        float: seed
    """
    if benchmark_enabled:
        return benchmark_seed if (round_counter % 2) else time.time()*1000   
    else:
        return 0
    

def save_games(games: List[Game]):
    """Creates a pickle of the played games to be analyzed in the gui.

    Args:
        games (game): List of all games (class: game).
    """
    with open('games.pickle', 'wb') as file:
        pickle.dump(games, file)
    #should be saved under "example" folder.
    logger.info("tournament.py - Pickle with all games has been overwritten.")
