import numpy as np
from pyschieber.card import Card
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
    # def __init__(self):
    #     #32-bits: (32768, 4294967295), 64-bits: (1, 18_446_744_073_709_551_615) Warning, numpy shift does not work with uint64.
    #     self.hashtable = np.random.randint(1, 4294967295, size=(4,9), dtype=np.uint32)
    #     self.suittable = np.random.randint(1, 4294967295, size=(4,1), dtype=np.uint32)
    #     self.trumpftable = np.random.randint(1, 4294967295, size=(6,1), dtype=np.uint32)
    #     self.INT_BITS = 32
    #     self.transpositions = {}
    #     self.transpositions_size = np.uint16(65535)

    def __init__(self) -> None:
        """load Transposition table from file to always have same random values!
        """
        self.tableState, self.handState, self.mode, seed = load_keys()
        self.INT_BITS = 64
        self.transpositions = {}
        self.transpositions_size = np.uint64(18_446_744_073_709_551_557) #largest prime in 64-bit
    
    def getZobristHash(self, player_cards: dict, table_cards: list, trumpf: Trumpf) -> int:
        """_summary_

        Args:
            player_cards (dict): Remaining cards of players (handcards)
            table_cards (list): NOT from state['table'], but is list of Cards. Already includes action taken by latest player!

        Returns:
            int: key
        """
        
        # rewrite hand cards of players with zobrist hash.
        zobrist_playerCards = np.uint32(0)
        for player_id, cards in player_cards.items():
            temp = np.uint32(0)
            product = np.multiply(cardToBitwise(cards), self.hashtable)
            for val in np.nditer(product):
                if val != 0:
                    temp ^= np.uint32(val)
            temp = self.leftRotate(temp, player_id)
            zobrist_playerCards = np.bitwise_xor(zobrist_playerCards, temp)

        # get zobrist of played suit:
        if table_cards:
            suit = table_cards[0].card.suit.value-1
            suit = self.suittable[suit,0]
        else:
            suit = 0

        # get zobrist for table_cards
        zobrist = 0
        for player_id, card in enumerate(table_cards):
            temp = np.uint32(0)
            # print( table_cards, card)
            product = np.multiply(cardToBitwise(card.card), self.hashtable)
            for val in np.nditer(product):
                if val != 0:
                    temp  ^= np.uint32(val)
            temp = self.leftRotate(temp, player_id)
            zobrist ^= temp            
        table_cards = self.leftRotate(zobrist, 4)

        # get zobrist for trumpf
        trumpfhash = self.trumpftable[trumpf_to_value(trumpf),0]

        # generate unique key.
        key = table_cards ^ suit
        key ^= zobrist_playerCards
        key ^= trumpfhash
        return np.uint32(key)

    def leftRotate(self, number, distance):
        return np.uint32(np.left_shift(number, distance) | np.right_shift(number, (self.INT_BITS - distance)))

    def rightRotate(self, number, distance):
        return np.uint32(np.right_shift(number, distance)| np.left_shift(number, (self.INT_BITS - distance)))

    def add_zobristHash(self, key, value):
        assert isinstance(key, np.uint32)
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
        for _ in range(4):
            hash = self.getZobristHash(player_cards, table_cards, trumpf)
            value = self.lookup_zobristHash(hash)
            if value != None:
                return value
            
            for index, playerCards in player_cards.items():
                temp = rotate_cards(cardToBitwise(playerCards))
                player_cards[index] = BitwiseToCards(temp)
            for index, tableCards in enumerate(table_cards):
                temp = rotate_cards(cardToBitwise(tableCards.card))
                card = BitwiseToCards(temp)[0]
                player = tableCards[0]
                table_cards[index] = PlayedCard(player, card)
            trumpf = rotate_trumpf(trumpf)
        return None


if __name__ == '__main__':
    print('This code is not executable!')