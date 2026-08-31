# from math import exp, factorial


from pyschieber.card import Card
from pyschieber.suit import Suit


def card_to_array(card: Card) -> list[int]:
    """Convert a single card into a one-hot encoded NumPy array.

    This function represents the given card as a length-36 vector with a
    single element set to 1 at the index corresponding to its suit and rank.

    Args:
        card (Card): The card to convert into a one-hot encoded representation.

    Returns:
        list[int]: A one-dimensional list of length 36 with
        exactly one entry set to 1 and all others set to 0.
    """
    card_array: list[int] = [0] * 36
    card_array[(card.suit.value - 1) * 9 + (card.value - 6)] = 1
    return card_array


def list_of_cards_to_array(list_of_cards: list[Card]) -> list[int]:
    """Convert a list of cards into a one-hot encoded NumPy array.

    This function represents the given list of cards as a length-36 vector with
    elements set to 1 at the indices corresponding to the suits and ranks of the
    cards in the list.

    Args:
        list_of_cards (list[Card]): The list of cards to convert into a one-hot
        encoded representation.

    Returns:
        list[int]: A one-dimensional list of length 36 with
        entries set to 1 for each card in the input list and all others set to 0.
    """
    if not isinstance(list_of_cards, list):
        raise TypeError("list_of_cards must be a list of Card instances")

    card_array: list[int] = [0] * 36
    for card in list_of_cards:
        card_array[(card.suit.value - 1) * 9 + (card.value - 6)] = 1

    return card_array


def array_to_list_of_cards(array: list[int]) -> list[Card]:
    """Convert a one-hot encoded NumPy array back into a list of cards.

    This function takes a length-36 vector with elements set to 1 at the indices
    corresponding to the suits and ranks of the cards, and converts it back into
    a list of Card instances.

    Args:
        array (list[int]): A one-dimensional list of length 36 with entries set to 1 for each card and all others set to 0.

    Returns:
        list[Card]: A list of Card instances corresponding to the input array.
    """
    if not isinstance(array, list):
        raise TypeError("array must be a list")
    if len(array) != 36:
        raise ValueError("array must be a one-dimensional list of length 36")

    list_of_cards: list[Card] = []
    for idx in range(36):
        if array[idx] == 1:
            suit_value = (idx // 9) + 1
            card_value = (idx % 9) + 6
            suit = Suit(suit_value)
            card = Card(value=card_value, suit=suit)
            list_of_cards.append(card)

    return list_of_cards


def flip_ones_and_zeros_in_list(input_list: list[int]) -> list[int]:
    """Flip 1s to 0s and 0s to 1s in a given list.

    This function takes a list of integers containing only 0s and 1s, and
    returns a new list where each 1 is replaced with a 0 and each 0 is
    replaced with a 1.

    Args:
        input_list (list[int]): A list of integers containing only 0s and 1s.

    Returns:
        list[int]: A new list with the same length as input_list, where
        each element is the flipped value of the corresponding element in
        input_list.
    """
    if any(x not in (0, 1) for x in input_list):
        raise ValueError("Input list must contain only 0s and 1s.")

    return [1 - x for x in input_list]


def flip_ones_and_zeros_in_2d_list(input_list: list[list[int]]) -> list[list[int]]:
    """Flip 1s to 0s and 0s to 1s in a list of lists.

    This function takes a list of lists containing only 0s and 1s, and
    returns a new list of lists where each 1 is replaced with a 0 and
    each 0 is replaced with a 1.

    Args:
        input_list (list[list[int]]): A list of lists containing only 0s and 1s.

    Returns:
        list[list[int]]: A new list of lists with the same structure,
        where each element is the flipped value of the corresponding element.
    """
    return [[1 - x for x in sublist] for sublist in input_list]


# def combinations_without_repetition(n: int, k: int) -> int:
#     """Calculates all Combinations without Repetition.
#         0 < k < n

#     Args:
#         n (int): all remaining objects (i.e. cards)
#         k (int): number of objects drawn (i.e. random handcards drawn)

#     Returns:
#         int: number of combinations without repetition
#     """
#     return int(factorial(n)/(factorial(n-k) * factorial(k)))


# def calculate_combinations(number_of_cards_per_player) -> int:
#     """Calculates the total number of combinations without repetition for
#     given Number of Cards per player and Unicate Cards per player.

#     Args:
#         number_of_cards_per_player (np.array): 3*[4x9] array containing all possible player handcards without unicates

#     Returns:
#         int: Total Number of card distributions that are possible in the given state.
#     """
#     remaining_cards = np.sum(number_of_cards_per_player)
#     factor1 = int(combinations_without_repetition(remaining_cards, number_of_cards_per_player[0]))
#     remaining_cards = remaining_cards - np.sum(number_of_cards_per_player[0])
#     factor2 = int(combinations_without_repetition(remaining_cards, number_of_cards_per_player[1]))
#     return factor1 * factor2


if __name__ == "__main__":
    print("This script is not executable.")
