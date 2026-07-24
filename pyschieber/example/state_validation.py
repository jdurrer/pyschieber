from pyschieber.player.challenge_player.challenge_player import ChallengePlayer
# from pyschieber.player.greedy_player.greedy_player import GreedyPlayer
from pyschieber.player.random_player import RandomPlayer
from pyschieber.player.cfr.cfr_trainer import CFRtrainer
from pyschieber.tournament import Tournament
import random
import time
import h5py
import os.path

import logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# # increase recurions limit
# import sys
# sys.setrecursionlimit(5000)



def start_tournament(points):
    tournament = Tournament(point_limit=points)

    players = [ CFRtrainer(name='CFR_A'),  CFRtrainer(name='CFR_B'), 
                CFRtrainer(name='CFR_C'),  CFRtrainer(name='CFR_D')]
    
    # players = [ ChallengePlayer(name='AAA'), ChallengePlayer(name='BBB'), 
    #             ChallengePlayer(name='CCC'), ChallengePlayer(name='DDD')]

    randomplayer = []
    seed = random.choices(range(0,len(players)), k=1)[0]
    while len(randomplayer) < 4:
        randomplayer.append(players[seed])
        seed = (seed + 1) % 4
    [tournament.register_player(player) for player in randomplayer]

    print('start:',time.asctime(time.localtime(time.time())))
    tournament.play(use_counting_factor=False, allow_weis=False, rounds = 1)
    print('end:',time.asctime(time.localtime(time.time())))
    
    # # check if team with bot won
    # if (seed+1)%2 == 0:
    #     team = 2
    # else:
    #     team = 1
    # print('CFR was team', team)
    
    
    return None

if __name__ == "__main__":
    points=257/2
    self_play = 1
    for play in range(self_play):
        print(' ')
        print('******************** starting game',play+1,'...')
        print(' ')
        start_tournament(points)




'''
-------------------- ToDo LIST ------------------------------------------------

Save ALL cfr positions for training plus rot invariant (suits combinations)
train
'''