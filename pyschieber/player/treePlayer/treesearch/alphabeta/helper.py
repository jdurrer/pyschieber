
import numpy as np
import numpy.typing as npt
from math import factorial, exp
from typing import List, Any

from pyschieber.card import Card
from pyschieber.suit import Suit
from pyschieber.trumpf import Trumpf


def combinations_without_repetition(n: int, k: int) -> int:
    """Calculates all Combinations without Repetition. 
        0 < k < n

    Args:
        n (int): all remaining objects (i.e. cards)
        k (int): number of objects drawn (i.e. random handcards drawn)

    Returns:
        int: number of combinations without repetition
    """
    return int(factorial(n)/(factorial(n-k) * factorial(k)))


def calculate_combinations(number_of_random_cards_per_player: npt.NDArray[np.uint8]) -> int: # CardsToDistributeBitwise?
    """Calculates the total number of combinations without repetition for 
    given Number of Cards per player and Unicate Cards per player.

    Args:
        number_of_random_cards_per_player (np.array): 3*[4x9] array containing all possible player handcards without unicates
    
    Returns:
        int: Total Number of card distributions that are possible in the given state.
    """
    remaining_cards = np.sum(number_of_random_cards_per_player)
    factor1 = int(combinations_without_repetition(remaining_cards, number_of_random_cards_per_player[0]))
    remaining_cards = remaining_cards-np.sum(number_of_random_cards_per_player[0])
    factor2 = int(combinations_without_repetition(remaining_cards, number_of_random_cards_per_player[1]))
    return factor1 * factor2


def cardToBitwise(list_of_cards: List[Card]):
    """Takes in a list of cards and returns a bitmap.
        [ 0 0 0 0 0 0 0 0 0]
        [ 0 0 0 0 0 0 0 0 0]
        [ 0 0 0 0 0 0 0 0 0]
        [ 0 0 0 0 0 0 0 0 0]

    Returns:
        np array: bitmap, ones containing the given cards.
    """
    bitmap = np.zeros((4,9))

    # ensure list was passed.
    if not isinstance(list_of_cards, list):
        list_of_cards = [list_of_cards]

    for single_card in list_of_cards:
        suit, value = from_string_to_card_value(single_card)
        bitmap[suit,value] = 1
    return np.short(bitmap)


def BitwiseToCards(bitmap) -> List[Card]:
    """Takes in a bitmap and returns a list of corresponding cards.
        [ 0 0 0 0 0 0 0 0 0]
        [ 0 0 0 0 0 0 0 0 0]
        [ 0 0 0 0 0 0 0 0 0]
        [ 0 0 0 0 0 0 0 0 0]

    Returns:
        List of Card: List with entries of class Card.
    """
    if not np.any(bitmap):
        return []
    rows, columns = np.nonzero(bitmap)
    cards = []
    cards = [Card(suit = Suit(row+1),value = column+6) for row, column in zip(rows, columns)]
    return cards


def trumpf_to_value(trumpf: Trumpf) -> int | None:
    if trumpf == Trumpf.OBE_ABE:
        return 0
    if trumpf == Trumpf.UNDE_UFE:
        return 1
    if trumpf == Trumpf.ROSE:
        return 2
    if trumpf == Trumpf.BELL:
        return 3
    if trumpf == Trumpf.ACORN:
        return 4
    if trumpf == Trumpf.SHIELD:
        return 5
    return None    


def value_to_trumpf(trumpf_value: int) -> Trumpf | None:
    if trumpf_value == 0:
        assert True
        return Trumpf.OBE_ABE
    if trumpf_value == 1:
        assert True
        return Trumpf.UNDE_UFE
    if trumpf_value == 2:
        return Trumpf.ROSE
    if trumpf_value == 3:
        return Trumpf.BELL
    if trumpf_value == 4:
        return Trumpf.ACORN
    if trumpf_value == 5:
        return Trumpf.SHIELD
    return None    


def rotate_cards(bitwise: npt.NDArray[Any]) -> npt.NDArray[Any]:
    return np.roll(bitwise, 1, axis=0)


def rotate_trumpf(trumpf: Trumpf) -> Trumpf | None:
    trumpf_value = trumpf_to_value(trumpf)
    if trumpf_value < 2:
        return trumpf
    temp = [2,3,4,5]
    trumpf_value = temp[(trumpf_value-1)%4]
    return value_to_trumpf(trumpf_value)


def collision_probability(n: int, k: int) -> float:
    """Calculates the probability of a (hash) collision.

    Args:
        n (int): number of bits
        k (int): number of entries in the database

    Returns:
        _type_: _description_
    """
    n = 2**n
    return 1 - exp(-k*(k-1)/(2*n))


if __name__ == '__main__':
    print('This script is not executable.')