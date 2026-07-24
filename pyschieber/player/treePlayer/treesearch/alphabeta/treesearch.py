'''
Alpha Beta Tree Search
'''


# from pyschieber.player.treePlayer.treesearch.helper import *
import copy
import numpy as np
from time import time
from itertools import combinations
import operator
import multiprocessing as mp # TODO: implement Multiprocessing !!!
from pyschieber.player.treePlayer.strategy.flags.flags import DoesntHaveCardFlag, PreviouslyHadStichFlag, FailedToServeSuitFlag, SuitAngezogenFlag, SuitVerworfenFlag
from pyschieber.card import Card, from_string_to_card
from pyschieber.stich import PlayedCard, stich_dict, played_cards_dict
from pyschieber.rules.stich_rules import stich_rules
from pyschieber.trumpf import get_trumpf
from pyschieber.rules.count_rules import count_stich
from pyschieber.player.base_player import BasePlayer
from pyschieber.player.treePlayer.treesearch.transpositionTable import TranspositionTable

class TreeSearch:
    """Uses tree search to find optimal card to play.

    To initiate in treePlayer use "self.tree = Root(copy.deepcopy(self), ...)"

    Returns:
        Card: Best card to play in this situation.
    """

    def __init__(self, deepcopy_of_player, deepcopy_of_state, depth = 36, time_s = 9999):
        """init Root
        
        Args:
            player (Class): Tree Player
            depth (int, optional): How many rounds shall be analyzed. Defaults to 4.
            time_s (int, optional): How much time is available to analyze state. Defaults to 5.
        """
        self.player = deepcopy_of_player
        self.initial_id = self.player.id # original ID of treeplayer
        self.depth = depth
        self.time_s = time_s*1000
        self.starttime = time()
        self.rootstate = deepcopy_of_state
        self.cc = self.player.strategy.card_counter
        self.roles = {}
        self.alpha = -float('inf')
        self.beta = float('inf')
        self.transpositionTable = TranspositionTable()

    def root(self):

        '''
            Needs the following to see if it has time to continue search. Smarter way to check?
            # check if still time
            if (time()-self.starttime_s) > self.time_s:
                break
        '''

        # some preparations
        self.get_roles()
        cards = self.player.allowed_cards(state=self.rootstate)
        cards = self.order_cards_by_strength(cards)
        score = { i : 0 for i in range(0, len(cards) ) }
        n_iterations = { i : 0 for i in range(0, len(cards) ) }
        NumberOfCardsPerPlayer, UnicatesPerPlayer, CardsToDistributeBitwise = self.get_Handsize_and_Unicates_Bitwise()

        # create a dict with bitwise 4*9 np.arrays that contains cards a player has. first, fill with unicates.
        npc_cards = {self.player.id: self.player.cards}
        npc_cards[self.cc.partner_id] = BitwiseToCards(UnicatesPerPlayer[self.cc.partner_id])
        npc_cards[self.cc.opponent_1_id] = BitwiseToCards(UnicatesPerPlayer[self.cc.opponent_1_id])
        npc_cards[self.cc.opponent_2_id] = BitwiseToCards(UnicatesPerPlayer[self.cc.opponent_2_id])

        #order cards to distribute by strength
        CardsToDistribute = {}
        for key, value in CardsToDistributeBitwise.items():
            CardsToDistribute[key] = BitwiseToCards(value)
            CardsToDistribute[key] = self.order_cards_by_strength(CardsToDistribute[key])
        if self.player.role == 'Off': # In this case, opponent is likely to have better cards.
            CardsToDistribute[self.cc.partner_id].reverse() # add a likelihood for each player to have a card !!!

        # Create Generator of Partner Handcards and iterate over them.
        PartnerCardsIterator = combinations(CardsToDistribute[self.cc.partner_id], int(NumberOfCardsPerPlayer[self.cc.partner_id]))
        skipPartner = 0
        for PartnerCards in PartnerCardsIterator:
            # to limit ressources, we only check 30% of all card combinations
            skipPartner += 1
            if skipPartner > 3:
                if skipPartner == 10:
                    skipPartner = 0
                continue
            npc_cards_deepcopy = copy.deepcopy(npc_cards)
            npc_cards_deepcopy[self.cc.partner_id].extend(PartnerCards)
            #remove cards from other players if they could hold said card.
            CardsToDistribute_deepcopy = copy.deepcopy(CardsToDistribute)
            for key, value in CardsToDistribute_deepcopy.items():
                if key == self.cc.partner_id or not value:
                    continue
                for card in npc_cards_deepcopy[self.cc.partner_id]:
                    if value.count(card):
                        CardsToDistribute_deepcopy[key].remove(card)
            # check if opponent 1 still has enough available cards to choose from.            
            if len(CardsToDistribute_deepcopy[self.cc.opponent_1_id]) < int(NumberOfCardsPerPlayer[self.cc.opponent_1_id]) or 0 > int(NumberOfCardsPerPlayer[self.cc.opponent_1_id]):
                continue
            # Create Generator of Opponent_1 Handcards and iterate over them. 
            Opponent1CardsIterator = combinations(CardsToDistribute_deepcopy[self.cc.opponent_1_id], int(NumberOfCardsPerPlayer[self.cc.opponent_1_id]))
            skipOpponent1 = 0
            for Opponent1Cards in Opponent1CardsIterator:
                # to limit ressources, we only check 30% of all card combinations
                skipOpponent1 += 1
                if skipOpponent1 > 3:
                    if skipOpponent1 == 10:
                        skipOpponent1 = 0
                    continue
                npc_cards_deep2copy = copy.deepcopy(npc_cards_deepcopy)
                CardsToDistribute_deep2copy = copy.deepcopy(CardsToDistribute_deepcopy)
                npc_cards_deep2copy[self.cc.opponent_1_id].extend(Opponent1Cards)
                for card in npc_cards_deep2copy[self.cc.opponent_1_id]:
                    if CardsToDistribute_deep2copy[self.cc.opponent_2_id].count(card):
                        CardsToDistribute_deep2copy[self.cc.opponent_2_id].remove(card)

                # check if opponent 2 still has enough available cards to choose from.            
                if len(CardsToDistribute_deep2copy[self.cc.opponent_2_id]) < int(NumberOfCardsPerPlayer[self.cc.opponent_2_id]) or 0 > int(NumberOfCardsPerPlayer[self.cc.opponent_2_id]):
                    continue
                npc_cards_deep2copy[self.cc.opponent_2_id] = CardsToDistribute_deep2copy[self.cc.opponent_2_id]

                self.alpha = -float('inf')
                for index, card in enumerate(cards):
                    self.npc_cards = npc_cards_deep2copy
                    branch = Node(copy.deepcopy(self), card, self.transpositionTable)
                    value = branch.alpha_beta_search()
                    if value > self.alpha:
                        self.alpha = value
                    score[index] += value
                    n_iterations[index] += 1

        # Divide score by times related card was explored and return card with highest score.
        for key, value in score.items():
            score[key] = value/max(1, n_iterations[key])
        return cards[max(score.items(), key=operator.itemgetter(1))[0]] # returns best card to play.    

    def get_roles(self):
        """
        Find the roles of all players.
        """
        if len(self.rootstate['stiche']) == 0:
            if len(self.rootstate['table']) == 0:
                self.roles[self.player.id] = 'Trumpf'
                self.roles[(self.player.id+1)%4] = 'Off'
                self.roles[(self.player.id+2)%4] = 'Partner'
                self.roles[(self.player.id+3)%4] = 'Off'

            else:
                first_player_id = self.rootstate['table'][0].get('player_id')
                self.roles[first_player_id] = 'Trumpf'
                self.roles[(first_player_id+1)%4] = 'Off'
                self.roles[(first_player_id+2)%4] = 'Partner'
                self.roles[(first_player_id+3)%4] = 'Off'

        else:
            roles = ['Trumpf', 'Off', 'Partner', 'Off']
            for player, role in zip(self.rootstate['stiche'][0]['played_cards'], roles):
                self.roles[player['player_id']] = role
        
        #swap roles if geschoben
        if self.rootstate['geschoben']:
            self.roles[0], self.roles[1], self.roles[2], self.roles[3] = self.roles[2], self.roles[3], self.roles[0], self.roles[1]

    def get_Handsize_and_Unicates_Bitwise(self):
        """Gets the Handsize of all players and the cards only they can have.

        Returns:
            dict: NumberOfCardsPerPlayer - Number of Cards of each player (with unicates), key = player_id, value = int.
            dict: UnicatesPerPlayer - Bitwise representation. 3*[4x9], key=player_id
            dict: CardsToDistributeBitwise - Bitwise representation of unknown remaining cards per possible owner, without unicates . 3*[4x9], key = player_id
        """
        # get id of other players and create a bitwise representation with a complete deck of cards.
        partner_id = self.cc.partner_id
        opponent_1_id = self.cc.opponent_1_id
        opponent_2_id = self.cc.opponent_2_id
        placeholder = np.ones((4, 9)) # one means player can still hold this card.
        # remove handcards of self
        placeholder = np.subtract(placeholder, cardToBitwise(self.player.cards))
        # remove already played cards
        for playedCards in self.cc.played_cards:
            placeholder = np.subtract(placeholder, cardToBitwise(playedCards))
        placeholder = np.maximum(placeholder, np.zeros_like(placeholder))

        # get player specific possible cards
        players = [copy.deepcopy(placeholder), copy.deepcopy(placeholder), copy.deepcopy(placeholder)] # players = [partner, opponent_1, opponent_2]
        players_id = [partner_id, opponent_1_id, opponent_2_id]
        for i, (player, player_id) in enumerate(zip(players, players_id)):
            players[i] = np.logical_and(player, self.getFlagsBitwise(player_id))
        # find unicates (Cards only a single player can have and hence must have)
        UnicatesPerPlayer = {}
        for index, (player, player_id) in enumerate(zip(players, players_id)):
            others = [x for i,x in enumerate(players) if i != index]
            others = np.logical_or(others[0], others[1])
            non_unicates = np.logical_and(player, others)
            unicates = np.subtract(player.astype(int), non_unicates.astype(int))
            UnicatesPerPlayer[player_id] = unicates
        
        NumberOfRandomCardsPerPlayer = {player_id: (9 - len(self.cc.played_cards[player_id])-np.sum(UnicatesPerPlayer[player_id])) for player_id in players_id}
        
        #create a dict which contains possible random cards for each player. They contain unicates.
        CardsToDistributeBitwise = {}
        for key, value in zip(players_id, players):
            CardsToDistributeBitwise[key] = value.astype(int)

        # remove unicates from randomly to distribute cards (CardsToDistributeBitwise)
        for random_dist, unicates in zip(CardsToDistributeBitwise.values(), UnicatesPerPlayer.values()):
            random_dist = np.subtract(random_dist, unicates)
            random_dist = np.minimum(random_dist, np.zeros_like(random_dist))

        return NumberOfRandomCardsPerPlayer, UnicatesPerPlayer, CardsToDistributeBitwise

    def getFlagsBitwise(self, player_id):
        """Gets flags of given player_id in bitwise representation.
        only failedToServeSuit implemented. other flag types are ignored. 

        Args:
            player_id (int): player id of interest

        Returns:
            np array: bitwise representation of flag cards (1 = flag cards).
        """
        bitwiseFlags = np.ones((4, 9))
        for flag in self.player.strategy.card_counter.flags[player_id]:
            if not isinstance(flag, FailedToServeSuitFlag):
                continue
            if flag.color != None:
                bitwiseFlags[flag.color.value-1] = np.zeros((1, 9))
        # assert np.amax(bitwiseFlags) == 1
        return bitwiseFlags

    def order_cards_by_strength(self, cards):
        """Orders Cards by strength depending on OBE_ABE, UNDE_UFE or TRUMPF.

        Args:
            cards (list, Cards): Cards to be ordered by strength

        Returns:
            list, Cards: List of Cards, first entry is the strongest.
        """
        trumpf = self.rootstate['trumpf']
        if trumpf == 'OBE_ABE':
            return sorted(cards, reverse=True)
        if trumpf == 'UNDE_UFE':
            return sorted(cards, reverse=False)  
        trumpf_list = []
        non_trumpf_list = []
        for card in cards:
            if card.suit.name == trumpf:
                trumpf_list.append(card)
            else:
                non_trumpf_list.append(card)
        trumpf_list = sorted(trumpf_list, reverse=True)
        non_trumpf_list = sorted(non_trumpf_list, reverse=True)
        return list(np.append(trumpf_list, non_trumpf_list))

class Node:
    """A Node of the game tree, representing a possible state.

    Returns:
        int: score of chosen card
    """

    def __init__(self, parent_deepcopy, card, transpositionTable):
        self.tree = parent_deepcopy
        self.card = card
        self.score = None
        self.children = None # children are several future gamestates we can reach by playing our handcards. 
        self.state = self.tree.rootstate
        self.cc = self.tree.cc
        self.depth = self.tree.depth
        self.transpositionTable = transpositionTable

    def alpha_beta_search(self):
        self.depth -= 1
        # create table...
        cards_on_table = []
        for tablecard in self.state['table']:
            card = from_string_to_card(tablecard['card'])
            player = BasePlayer(name=str(tablecard['player_id']))
            player.id = tablecard['player_id']
            cards_on_table.append(PlayedCard(player, card))
        # actor plays card
        cards_on_table.append(PlayedCard(self.tree.player, self.card))
        # remove played card from hand.
        self.tree.npc_cards[self.tree.player.id].remove(self.card)

        # check transposition table
        table_entry = self.transpositionTable.lookup_table(self.tree.npc_cards, cards_on_table, get_trumpf(self.state['trumpf']))
        if table_entry != None:
            # print('Transposition Entry found!')
            return table_entry

        # update state and other players
        self.state['table'] = [played_cards_dict(played_card) for played_card in cards_on_table]
        self.tree.player.move_made(self.tree.player.id, self.card, dict(self.state))

        # check if table full:
        if len(cards_on_table) == 4:
            stich = stich_rules[get_trumpf(self.state['trumpf'])](played_cards=cards_on_table)
            self.state['stiche'].append(stich_dict(stich))
            self.count_points(stich)
            next_player_id = stich.player.id
            cards_on_table = []
            self.state['table'] = [played_cards_dict(played_card) for played_card in cards_on_table]
            self.state = dict(self.state)
        else:
            next_player_id = (self.tree.player.id + 1) % 4

        # Check if Leafnode was reached and stop
        if self.isEndgame_Tablebase():
            return self.endgame_tablebase(next_player_id)
        if self.isTerminal():
            return self.terminal_util()
        # if self.isDepthlimit():
        #     return self.depthlimit_util()

        # continue with next player
        self.getNextPlayer(next_player_id)
        cards = self.tree.player.choose_card_treesearch(self.state)
        self.children = []
        if isinstance(cards, Card):
            self.children.append(Node(copy.deepcopy(self.tree), cards, self.transpositionTable))
        else:
            for card in cards:
                self.children.append(Node(copy.deepcopy(self.tree), card, self.transpositionTable))
        
        if self.score == None:
            self.score = 0
        
        if next_player_id % 2 != self.tree.initial_id % 2:
            # opponents are next players
            self.score += self.min_value()
        else:
            # player or partner is next
            self.score += self.max_value()

        # # update transposition table - adapt, here it does not work because table was already trashed again. !!!
        # table_entry = self.transpositionTable.lookup_table(self.tree.npc_cards, cards_on_table, get_trumpf(self.state['trumpf']))
        # if table_entry == None:
        #     zobrist = self.transpositionTable.getZobristHash(self.tree.npc_cards, cards_on_table, get_trumpf(self.state['trumpf']))
        #     self.transpositionTable.add_zobristHash(zobrist, self.score)
        return self.score

    def max_value(self):
        value = -float('inf')
        for child in self.children:
            value = max(value, child.alpha_beta_search())
            if value >= self.tree.beta:
                # print('skipped max')
                return value
            self.tree.alpha = max(self.tree.alpha, value)
        return value

    def min_value(self):
        value = float('inf')
        for child in self.children:
            value = min(value, child.alpha_beta_search())
            if value <= self.tree.alpha:
                # print('skipped min')
                return value
            self.tree.beta = min(self.tree.beta, value)
        return value

    def isTerminal(self):
        # check if all cards have been played
        return not any(x != [] for x in self.tree.npc_cards.values())

    def terminal_util(self):
        # assert self.score != 0 # !!! gave out error for end-easy 161. Why was this here?
        if self.score == None:
            self.score = 0
        return self.score

    def isDepthlimit(self):
        # check if time limit reached
        if time() >= self.tree.time_s + self.tree.starttime:
            return True
        # check if depth limit reached
        if self.depth <= 0:
            return True
        return False
    
    def depthlimit_util(self, cards):
        # pass hand and table to heuristic to evaluate remaining cards and add to score !!!
        pass

    def heuristics(self,cards):
        # Does not work like this...
        # trumpf = get_trumpf(self.state['trumpf'])
        # if trumpf == Trumpf.OBE_ABE:
        #     mode = TopDownMode()
        # if trumpf == Trumpf.UNDE_UFE:
        #     mode = BottomUpMode()
        # if trumpf == Trumpf.ROSE:
        #     mode = TrumpfColorMode(Suit.ROSE)
        # if trumpf == Trumpf.BELL:
        #     mode = TrumpfColorMode(Suit.BELL)
        # if trumpf == Trumpf.ACORN:
        #     mode = TrumpfColorMode(Suit.ACORN)
        # if trumpf == Trumpf.SHIELD:
        #     mode = TrumpfColorMode(Suit.SHIELD)       
        # return mode.calculate_mode_score(cards, False)
        pass

    def isEndgame_Tablebase(self):
        pass
    #     # additional: check if current player has bock until end of game? !!! TBD
    #     count = 0
    #     for listElem in self.tree.npc_cards.values():
    #         count += len(listElem)
    #     return count == 4

    # def endgame_tablebase(self, next_player_id):
    #     """_summary_

    #     Args:
    #         next_player_id (_type_): _description_

    #     Returns:
    #         _type_: _description_
    #     """
    #     player = BasePlayer(name=str(next_player_id))
    #     player.id = next_player_id
    #     cards_on_table = [PlayedCard(player, self.tree.npc_cards[next_player_id][0])]

    #     for _ in range(3):
    #         next_player_id = (next_player_id+1)%4
    #         player = BasePlayer(name=str(next_player_id))
    #         card = self.tree.npc_cards[next_player_id][0]
    #         player.id = next_player_id
    #         cards_on_table.append(PlayedCard(player, card))
    #     stich = stich_rules[get_trumpf(self.state['trumpf'])](played_cards=cards_on_table)
    #     self.count_points(stich)
    #     return self.score    

    def getNextPlayer(self, next_player_id):
        """ Updates everything required for next player to function correctly.
        Update the following of self:
        role (treeplayer)
        name (baseplayer)
        cards (baseplayer)
        id (baseplayer)
        played_cards (Cardcounter)
        flags (Cardcounter)
        my_id (Cardcounter)
        partner_id (Cardcounter)
        opponent_1_id (Cardcounter)
        opponent_2_id (Cardcounter)

        Some may not be required and are not updated. They are commented out below.

        Args:
            next_player_id (_type_): player ID of the next player.
        """
        self.tree.player.role = self.tree.roles[next_player_id]
        # self.tree.player.name = 
        self.tree.player.cards = self.tree.npc_cards[next_player_id]
        self.tree.player.id = next_player_id
        # self.cc.played_cards = 
        # self.cc.flags = 
        self.cc.my_id = next_player_id
        self.partner_id = (next_player_id + 2) % 4
        self.opponent_1_id = (next_player_id + 1) % 4
        self.opponent_2_id = (next_player_id + 3) % 4

    def count_points(self, stich):
            """
            Gets the team of the winner of the stich and counts the points.
            :param stich:
            :param last: True if it is the last stich of the Game, False otherwise
            :return:
            """
            stich_player_index = stich.player.id
            cards = [played_card.card for played_card in stich.played_cards]
            self.add_points(team_index=(stich_player_index % 2), cards=cards)
        
    def add_points(self, team_index, cards):
        """
        Adds the points of the cards to the score of the team who won the stich.
        :param team_index:
        :param cards:
        :param last:
        :return:
        """
        points = count_stich(cards, get_trumpf(self.state['trumpf']), last = (len(self.state['stiche']) == 9))
        self.state['teams'][team_index]['points'] += points
        if self.state['teams'][team_index]['points'] == 157:
            counter = [0,0]
            for stich in self.state['stiche']:
                stich_player_index = stich['player_id']
                counter[stich_player_index % 2] += 1
            if counter[team_index] == 9:
                self.state['teams'][team_index]['points'] += 100
                points += 100

        if self.score == None:
            self.score = 0

        if self.tree.initial_id % 2 == team_index:
            self.score += points
        else:
            self.score -= points


if __name__ == "__main__":
    print('This Skript can not be run by itself!')