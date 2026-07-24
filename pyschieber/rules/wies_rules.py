from enum import Enum
from pyschieber import card
import numpy as np


# TODO: Implement Wiesen and the corresponding rules

# def wies_allowed(wies, hand_cards):
#     allowed = False
#     if not len(wies) >= 3:
#         return False
#     if not set(wies) < set(hand_cards):
#         return False
#     return allowed

def weisen(hand_cards,trumpf):
    # print(hand_cards)
    # print(type(hand_cards))
    # hand_cards = ','.join(hand_cards)
    points_wies = [20, 50, 100, 150, 200, 250, 300, 100, 150, 200, 20]
    #               3,  4,   5,   6,   7,   8,   9, 4x?, 4x9, 4xU, Stoeck
    GLEICH = [0,0,0,0,0,0,0,0,0]
    Count = 0
    Cards = np.zeros((4,9))
    Cards_weis = np.zeros((4,9))
    total_weis = 0                #Totale summe weis
    max_weis = 0               #der höchste wert, der gewiesen wird
    # print(type(hand_cards))
    for i in range(len(hand_cards)):
        suit, value = card.from_string_to_card_weis(hand_cards[i])
        Cards[suit,value] = 1
    #     '''
    #     TEST HAND GENERATOR
    #     '''
    #     cont = 1
    #     while(cont == 1):
    #         suit = np.random.randint(3)
    #         value = np.random.randint(9)
    #         if Cards[suit,value] == 0:
    #             Cards[suit,value] = 1
    #             cont = 0
    #         else: 
    #             cont = 1  
    # print(Cards)
    # '''
    # END TEST HAND GENERATOR
    # '''
    
    '''
    Vier gleiche
    '''
    # print(hand_cards)
    for i in range(9):
        for j in range(4):
            if Cards[j,i] == 1:
                GLEICH[i] += 1/4
        if GLEICH[i] == 1 and i != 3 and i != 5:
            for k in range(4):
                Cards_weis[k,i] = 1
            total_weis += points_wies[7]
            if max_weis < points_wies[7]:
                max_weis = points_wies[7]
        if GLEICH[3]  == 1 and i == 3:
            for k in range(4):
                Cards_weis[k,i] = 1
            total_weis += points_wies[8]
            if max_weis < points_wies[8]:
                max_weis = points_wies[8]
        if GLEICH[5]  == 1 and i == 5:
            for k in range(4):
                Cards_weis[k,i] = 1
            total_weis += points_wies[9]
            if max_weis < points_wies[9]:
                max_weis = points_wies[9]
    '''
    AUFEINANDERFOLGENDE KARTEN EINER FARBE
    '''
    for j in range(4):
        Count = 0
        for i in range(9):
            
            if Cards[j,i] == 1:                             #aufsummieren aufeinanderfolgender karten
                Count += 1
                
            if Cards[j,i] == 0:                             #keine aufeinanderfolgende karte mehr
                if Count >= 3:
                    total_weis += points_wies[Count-3]
                    if max_weis < points_wies[Count-3]:
                        max_weis = points_wies[Count-3]
                    for k in range(i-Count,i):
                        Cards_weis[j,k] = 1
                Count = 0
                        
            if Cards[j,i] == 1 and i == 8:                  #spezialfall ass
                if Count >= 3:
                    total_weis += points_wies[Count-3]
                    if max_weis < points_wies[Count-3]:
                        max_weis = points_wies[Count-3]
                    for k in range(i+1-Count,i+1):
                        Cards_weis[j,k] = 1
                Count = 0
                
    '''
    Stoeck fehlt
    '''
    # trumpf = trumpf-3                                                         #punkte für stöck
    # if Cards[trumpf,6] == 1 and Cards[trumpf,7] == 1:
    #     total_weis += points_wies[10]
                
    # print(max_weis)
    # print(total_weis)
        
    return max_weis, total_weis, Cards_weis


def vgl_weis(max_weis, total_weis, weis_cards, trumpf_value, start_player):
    '''
    höchster weis
    stärkste karte
    zuerst angesagte, egal ob einer der weise trumpf
    '''
    # print('trumpf_value:')
    # print(trumpf_value)
    
    weis = 0
    teamnbr = 2
    highcard = np.zeros((1,4))
    decisionCard = 0
    # print('max_weis:')
    # print(max_weis)
    # print('total_weis:')
    # print(total_weis)
    # print(weis_cards)
    
    #höchster Weis
    if max(max_weis[0,0],max_weis[0,2]) > max(max_weis[0,1],max_weis[0,3]):
        # print('maxweis t0')
        weis = total_weis[0,0] + total_weis[0,2]
        teamnbr = 0
        weis_cards[1] = np.zeros((4,9))
        weis_cards[3] = np.zeros((4,9))
        
    elif max(max_weis[0,0],max_weis[0,2]) < max(max_weis[0,1],max_weis[0,3]):
        # print('maxweis t1')
        weis = total_weis[0,1] + total_weis[0,3]
        teamnbr = 1
        weis_cards[0] = np.zeros((4,9))
        weis_cards[2] = np.zeros((4,9))
    
    #höchste Karte
    else: 
        
        if trumpf_value == 2: #une_ufe
            # print('une_ufe')
            for i in range(4):
                for j in range(4):
                    for k in range(8,-1,-1):
                        if weis_cards[i,j,k] == 1:
                            highcard[0,i] = k
            # print(highcard)
            
            if min(highcard[0,0],highcard[0,2]) < min(highcard[0,1],highcard[0,3]):
                # print('team0 tiefer')
                weis = total_weis[0,0] + total_weis[0,2]
                teamnbr = 0
                # print(teamnbr)
                weis_cards[1] = np.zeros((4,9))
                weis_cards[3] = np.zeros((4,9))
                
            elif min(highcard[0,0],highcard[0,2]) > min(highcard[0,1],highcard[0,3]):
                # print('team1 tiefer')
                weis = total_weis[0,1] + total_weis[0,3]
                teamnbr = 1
                # print(teamnbr)
                weis_cards[0] = np.zeros((4,9))
                weis_cards[2] = np.zeros((4,9))
                
            else: 
                #first player that called weis
                decisionCard = np.min(highcard)
                for i in range(4):
                    player = i+start_player
                    if player >= 4:
                        player = player - 4
                    if highcard[0,player] == decisionCard:
                        weis = total_weis[0,player%2] + total_weis[0,(player%2)+2]
                        teamnbr = player%2
                        # print('team that called first:')
                        # print(teamnbr)
                        weis_cards[(player+1)%2] = np.zeros((4,9))
                        weis_cards[(player+1)%2+2] = np.zeros((4,9))
                        # print(weis_cards, weis, teamnbr)
                        return weis_cards, weis, teamnbr
        
        else:
            # print('not une_ufe')
            for i in range(4):
                for j in range(4):
                    for k in range(9):
                        if weis_cards[i,j,k] == 1:
                                highcard[0,i] = k
            # print(highcard)
                        
            if max(highcard[0,0],highcard[0,2]) > max(highcard[0,1],highcard[0,3]):
                # print('maxweis t0')
                weis = total_weis[0,0] + total_weis[0,2]
                teamnbr = 0
                # print(teamnbr)
                weis_cards[1] = np.zeros((4,9))
                weis_cards[3] = np.zeros((4,9))
                
            elif max(highcard[0,0],highcard[0,2]) < max(highcard[0,1],highcard[0,3]):
                # print('maxweis t1')
                weis = total_weis[0,1] + total_weis[0,3]
                teamnbr = 1
                # print(teamnbr)
                weis_cards[0] = np.zeros((4,9))
                weis_cards[2] = np.zeros((4,9))   
                
            else:
                #first player that called weis
                decisionCard = np.max(highcard)
                for i in range(4):
                    player = i+start_player
                    if player >= 4:
                        player = player - 4
                    if highcard[0,player] == decisionCard:
                        weis = total_weis[0,player%2] + total_weis[0,(player%2)+2]
                        teamnbr = player%2
                        # print('team that called first:')
                        # print(teamnbr)
                        weis_cards[(player+1)%2] = np.zeros((4,9))
                        weis_cards[(player+1)%2+2] = np.zeros((4,9))
                        # print(weis_cards, weis, teamnbr)
                        return weis_cards, weis, teamnbr
                    
    # print(weis_cards, weis, teamnbr)
        
    return weis_cards, weis, teamnbr