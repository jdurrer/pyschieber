import pytest

from pyschieber.card import Card
from pyschieber.player.treePlayer.treesearch.helper import (
    array_to_list_of_cards,
    card_to_array,
    flip_ones_and_zeros_in_2d_list,
    flip_ones_and_zeros_in_list,
    list_of_cards_to_array,
)
from pyschieber.suit import Suit


def test_card_to_array() -> None:
    card = Card(value=6, suit=Suit(1))

    result = card_to_array(card)

    assert len(result) == 36
    assert result[0] == 1
    assert sum(result) == 1


def test_card_to_array_uses_suit_and_value_index() -> None:
    card = Card(value=14, suit=Suit(4))

    result = card_to_array(card)

    expected_index = (4 - 1) * 9 + (14 - 6)
    assert result[expected_index] == 1
    assert sum(result) == 1


def test_list_of_cards_to_array() -> None:
    cards = [
        Card(value=6, suit=Suit(1)),
        Card(value=14, suit=Suit(4)),
    ]

    result = list_of_cards_to_array(cards)

    assert len(result) == 36
    assert sum(result) == 2
    assert result[0] == 1
    assert result[35] == 1


def test_list_of_cards_to_array_empty_list() -> None:
    assert list_of_cards_to_array([]) == [0] * 36


def test_list_of_cards_to_array_rejects_non_list() -> None:
    with pytest.raises(TypeError):
        list_of_cards_to_array(())  # type: ignore[arg-type]


def test_array_to_list_of_cards() -> None:
    cards = [
        Card(value=6, suit=Suit(1)),
        Card(value=14, suit=Suit(4)),
    ]

    result = array_to_list_of_cards(list_of_cards_to_array(cards))

    assert result == cards


def test_array_to_list_of_cards_ignores_zeroes() -> None:
    assert array_to_list_of_cards([0] * 36) == []


def test_array_to_list_of_cards_rejects_non_list() -> None:
    with pytest.raises(TypeError):
        array_to_list_of_cards(())  # type: ignore[arg-type]


def test_array_to_list_of_cards_rejects_wrong_length() -> None:
    with pytest.raises(ValueError):
        array_to_list_of_cards([0] * 35)


def test_flip_ones_and_zeros_in_list() -> None:
    values = [0, 1, 1, 0]

    result = flip_ones_and_zeros_in_list(values)

    assert result == [1, 0, 0, 1]
    assert values == [0, 1, 1, 0]


def test_flip_ones_and_zeros_in_list_empty() -> None:
    assert flip_ones_and_zeros_in_list([]) == []


def test_flip_ones_and_zeros_in_list_rejects_other_values() -> None:
    with pytest.raises(ValueError):
        flip_ones_and_zeros_in_list([0, 1, 2])


def test_flip_ones_and_zeros_in_2d_list() -> None:
    values = [[0, 1], [1, 0, 1]]

    result = flip_ones_and_zeros_in_2d_list(values)

    assert result == [[1, 0], [0, 1, 0]]
    assert values == [[0, 1], [1, 0, 1]]


def test_flip_ones_and_zeros_in_2d_list_empty() -> None:
    assert flip_ones_and_zeros_in_2d_list([]) == []
