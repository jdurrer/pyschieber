import pytest

from pyschieber.player.treePlayer.helpers.helperfunctions import (
    flatten_matrix,
    is_empty_or_none,
)


@pytest.mark.parametrize(
    "matrix, expected",
    [
        ([], []),
        ([[1, 2, 3]], [1, 2, 3]),
        ([[1], [2], [3]], [1, 2, 3]),
        ([[1, 2], [3, 4]], [1, 2, 3, 4]),
        ([["a", "b"], ["c"]], ["a", "b", "c"]),
        ([[None, 0], [False, True]], [None, 0, False, True]),
    ],
)
def test_flatten_matrix(matrix, expected) -> None:
    assert flatten_matrix(matrix) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, True),
        ("", True),
        ([], True),
        ({}, True),
        (0, True),
        (0.0, True),
        (False, True),
        ("non-empty", False),
        ([1], False),
        ({1: 2}, False),
        (1, False),
        (3.14, False),
        (True, False),
    ],
)
def test_is_empty_or_none(value, expected) -> None:
    assert is_empty_or_none(value) is expected
