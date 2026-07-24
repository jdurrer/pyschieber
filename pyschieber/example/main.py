#########################################
##                                     ##
##               SETTINGS              ##
##                                     ##
#########################################


Spielrunden = 1000
benchmark_bool = True
weisen_bool = False
counting_factor_bool = False


#########################################
##                                     ##
##               LIBRARY               ##
##                                     ##
#########################################

from pyschieber.player.challenge_player.challenge_player import ChallengePlayer
from pyschieber.player.treePlayer.treePlayer import TreePlayer
from pyschieber.player.greedy_player.greedy_player import GreedyPlayer
from pyschieber.tournament import Tournament
from typing import List


#########################################
##                                     ##
##               LOGGING               ##
##                                     ##
#########################################

import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# logger.propagate = False


#########################################
##                                     ##
##              FUNCTIONS              ##
##                                     ##
#########################################


def start_tournament(points: float) -> None:
    """Starts a tournament with the specified point limit. 
    Registers players and initiates the tournament with the configured settings.

    Args:
        points (int): The point limit for the tournament.

    Returns:
        None
    """
    tournament: Tournament = Tournament(point_limit=points)
    players = get_players()
    [tournament.register_player(player) for player in players]
    tournament.play(use_counting_factor = counting_factor_bool, allow_weis=weisen_bool, rounds = Spielrunden, benchmark_enabled = benchmark_bool)


def get_players() -> List:
        # Testing code
    players1 = [ TreePlayer(name='A'),  TreePlayer(name='B'), 
                TreePlayer(name='C'),  TreePlayer(name='D')]

    # Basic validity Test
    # Team 1 = Challenge, Team 2 = Tree
    players2 = [ GreedyPlayer(name='GreedyA'),  TreePlayer(name='TreeA'), 
                GreedyPlayer(name='GreedyB'),  TreePlayer(name='TreeB')]

    '''Performance test against strong opponent'''
    # # Team 1 = Challenge, Team 2 = Tree
    players3 = [ ChallengePlayer(name='ChallengeA'),  TreePlayer(name='TreeA'), 
                ChallengePlayer(name='ChallengeB'),  TreePlayer(name='TreeB')]

    # Team 1 = Tree, Team 2 = Challenge
    players4 = [ TreePlayer(name='TreeA'),  ChallengePlayer(name='ChallengeA'), 
                TreePlayer(name='TreeB'),  ChallengePlayer(name='ChallengeB')]
    
    ''' strong opponents only'''
    players5 = [ ChallengePlayer(name='AAA'), ChallengePlayer(name='BBB'), 
                ChallengePlayer(name='CCC'), ChallengePlayer(name='DDD')]

    '''Plausability Test'''
    players6 = [ ChallengePlayer(name='AAA'), GreedyPlayer(name='BBB'), 
                ChallengePlayer(name='CCC'), GreedyPlayer(name='DDD')] 
    
    return players3


def main() -> None:
    print('starting...')
    points = float('inf') # To be used with rounds = #someNumberNotZero
    start_tournament(points)
    

if __name__ == '__main__':
    main()