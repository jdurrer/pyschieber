import numpy as np
from pyschieber.card import Card#, from_string_to_card_value
from pyschieber.player.treePlayer.treesearch.helper import cardToBitwise, BitwiseToCards, trumpf_to_value, rotate_cards, rotate_trumpf
from pyschieber.stich import PlayedCard
from pyschieber.deck import Deck
from random import shuffle
from pyschieber.trumpf import Trumpf
import pickle


def createUniqueKeys():
    """Creates unique keys for the transposition table. Do only run this code one and save state seed.

    seed: is contained in pickle as last entry (4).
    np.random.set_state(seed)

    tableState:
        Shows the actual state of the table. 3d-matrix. [suit,value,position_on_table]
            suit: Trumpf, 1, 2, 3, 4. First suit on table is 1 unless it is trumpf. Then the following suits come in fixed order. decreases number of transpositions.
            value: 0-9 or 6-14 for value of the cards? #!!!
            position_on_table: 1,2. 1 for first card, 2 for all other cards.

    handState:
        Shows the possible cards on a players hand at this point in time. 3d-matrix. [suit, value, PlayerID]
            suit: siehe oben
            value: siehe oben
            PlayerID: Id of the player? Normalized ID of the player? #!!!
    
    Mode: 1d array. [obeabe,uneufe] obeabe oder uneufe. Trumpf is special variant of obeabe where trumpf was not played.

    Returns:
        pickle: saves transposition table keys as file.
    """

    #get and save state.
    np.random.seed(None)
    prng = np.random.RandomState()
    seed = prng.get_state()

    #size = [suit, value, position_on_table]
    tableState = np.random.randint(1,18_446_744_073_709_551_615,size=(5,9,2),dtype='uint64')

    #size = [suit, value, PlayerID]
    handState = np.random.randint(1,18_446_744_073_709_551_615,size=(5,9,4),dtype='uint64')

    #size = [2]
    mode = np.random.randint(1,18_446_744_073_709_551_615,size=(2),dtype='uint64')

    keys = {1:tableState,2:handState,3:mode,4:seed}
    file = open('keys.pickle', 'wb')
    pickle.dump(keys, file)
    #should be saved under "example" folder.
    file.close()


def load_keys():
    file = open('keys.pickle', 'rb')
    keys = pickle.load(file)
    file.close()
    return keys[1], keys[2], keys[3], keys[4]


class TranspositionTable:

    def __init__(self) -> None:
        """load Transposition table from file to always have same random values!
        """
        self.tableState, self.handState, self.mode, seed = load_keys()
        self.INT_BITS = 64
        self.transpositions = {}
        self.transpositions_size = np.uint64(18_446_744_073_709_551_557) #largest prime in 64-bit


    def get_suit_order_cards(self, cards: list, trumpf: Trumpf) -> dict:
        """_summary_

        Args:
            cards (list): i.e. table_cards from getZobristHash
            trumpf (Trumpf): trumpf

        Raises:
            Exception: cards must not be empty! Probably error somewhere in the code?

        Returns:
            suit_order (dict): suit order for tt representation
        """
        #simplify suit order in regard of first card on table to minimize table size.
        suit_order = {} #placeholder. index = card suit, value = zobrist suit
        # get zobrist index of played suit: ['ROSE', 'BELL', 'ACORN', 'SHIELD', Trumpf] = 0 1 2 3 4
        if cards:
            suit_value = cards[0].card.suit.value-1
            trumpf_suit_value = trumpf_to_value(trumpf)-2
        else:
            print('Warning! No cards on table! This should not happen as the state gets checked after a card was already played! transpositionTable.py')
            raise Exception()
            return {0:0, 1:1, 2:2, 3:3}

        if trumpf_suit_value < 0:
            # suit values stay the same (0,1,2,3) because trumpf has no influence. Only order changes so start color is first. 4 gets ignored.
            suit_order = {suit_value:0, (suit_value+1)%4:1, (suit_value+2)%4:2, (suit_value+3)%4:3}

        elif trumpf_suit_value == suit_value:
            #trumpf suit becomes 4, the following suits become 1,2,3. 0 gets ignored because normally it stands for "suit of first card and not trumpf". 
            suit_order = {suit_value:4, (suit_value+1)%4:1, (suit_value+2)%4:2, (suit_value+3)%4:3}

        else:
            # trumpf_suit_value != suit_value. Trumpf suit becomes 4, suit of first card becomes 0, remaining become 1,2. Tricky!
            suit_order = {trumpf_suit_value:4, suit_value:0}
            j = 1
            for i in range(4):
                if i != (trumpf_suit_value) and (i != suit_value):
                    suit_order[i] = j
                    j += 1

        return suit_order
    

    def getZobristHash(self, player_cards: dict, table_cards: list, trumpf: Trumpf) -> int:
        """_summary_

        Args:
            player_cards (dict): Remaining (possible) cards of players (handcards)
            table_cards (list): Cards on the table. Already includes action taken by latest player!

        Returns:
            int: Zobrist
        """

        # Zobrist starts at zero.
        zobrist = np.uint64(0)
        suit_order = self.get_suit_order_cards(table_cards, trumpf)

        # Zobrist for Mode ------------------------------------------------------------------------------------------------------------
        if trumpf_to_value(trumpf) == 1:
            #uneufe
            zobrist ^= self.mode[1]
        else:
            #trumpf or obeabe. obeabe is treated as special trumpf mode.
            zobrist ^= self.mode[0]

        # Zobrist of Table Cards ------------------------------------------------------------------------------------------------------
        for i, (_, card) in zip(range(len(table_cards)), enumerate(table_cards)):
            # print( table_cards, card)
            suit, value = from_string_to_card_value(card.card)
            zobrist ^= self.tableState[suit_order[suit], value, min(i,1)]

        # Zobrist of Hand Cards ----------------------------------------------------------------------------------------------------
        for player_id, cards in player_cards.items():
            if not isinstance(cards, list):
                cards = [cards]
            for single_card in cards:
                suit, value = from_string_to_card_value(single_card)
                zobrist ^= self.handState[suit_order[suit], value, player_id]

        return np.uint64(zobrist)


    # def leftRotate(self, number, distance):
    #     return np.uint32(np.left_shift(number, distance) | np.right_shift(number, (self.INT_BITS - distance)))


    # def rightRotate(self, number, distance):
    #     return np.uint32(np.right_shift(number, distance)| np.left_shift(number, (self.INT_BITS - distance)))


    def add_zobristHash(self, key, value):
        assert isinstance(key, np.uint64)
        if len(self.transpositions) >= self.transpositions_size:
            print('Transposition table is full.')
            first_key = next(iter(self.transpositions))
            self.transpositions.pop(first_key)
        self.transpositions[key] = np.uint16(value)      


    def lookup_zobristHash(self, zobrist):
        return self.transpositions.get(zobrist)


    def lookup_table(self, player_cards: dict, table_cards: list, trumpf: Trumpf):
        """Checks if gamestate is in zobrist table.
        If hash is in table, returns [value, alpha, beta]
        If hash is NOT in table, returns None.

        Args:
            hash (int): hash key to look up in table

        Returns:
            list, None: see description above.
        """
        hash = self.getZobristHash(player_cards, table_cards, trumpf)
        return self.lookup_zobristHash(hash)


if __name__ == '__main__':
    print('This code is not executable!')