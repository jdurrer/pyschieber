"""Creates all transpositions with four cards and saves them inside a pickle
"""

import pickle
from tkinter import filedialog
import tkinter as tk
from pyschieber.player.challenge_player.challenge_player import ChallengePlayer
from pyschieber.player.treePlayer.treePlayer import TreePlayer
from pyschieber.benchmark.helper.tournament_benchmark import Tournament
import time
from tqdm import tqdm

# import logging
# logging.basicConfig()
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

def start_tournament(points, state):
    tournament = Tournament(point_limit=points)
    players = [ TreePlayer(name='A'),  TreePlayer(name='B'), 
                TreePlayer(name='C'),  TreePlayer(name='D')]
    [tournament.register_player(player) for player in players]
    tournament.play(state = state, use_counting_factor=False, allow_weis=False, rounds = 1)  

def create_four_card_states():
    # 1. select four unique cards from the deck
    # 2. hand unique cards to players in all possible variations
    # 3. decide how many cards are known / unknown and iterate.
    # 4. decide on who plays first card.
    # 5. decide trumpf
    # 6. run and repeat.
    # (7. keep track on how many states were explored and how many entries in table were made.)
    pass  

def save_pickle(state, filename, path = None):
    print('Choose a location to save.')
    if path == None:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory()
        root.destroy()
    save_path = path + '/' + filename + '.pickle'
    f = open(save_path, 'wb')
    pickle.dump(state, f)
    f.close()
    return path

def load_pickle():
    print('Choose a file to load.')
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename()
    f = open(path, 'rb')
    state = pickle.load(f)
    root.destroy()
    f.close()
    return state

if __name__ == "__main__":



    # load Benchmark
    states = load_pickle()

    start = time.time()
    for state in tqdm(states):
        start_tournament(points=0, state=state)
    end = time.time()
    avg_time = (end-start)/1000
    print('The Players were able to solve the benchmark in a time of {} seconds.'.format(avg_time))