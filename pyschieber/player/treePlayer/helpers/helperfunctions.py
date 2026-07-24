from typing import Any, List

def flatten_matrix(matrix: List[List[Any]]) -> List[Any]:
    """Flattens a two-dimensional list into a single list.

    This function takes a matrix (list of lists) and returns a flat list containing all elements in row-major order.

    Args:
        matrix (List[List[Any]]): The matrix to flatten.

    Returns:
        List[Any]: The flattened list of elements.
    """
    return [item for row in matrix for item in row]


def is_empty_or_none(x) -> bool:
    """Checks whether a value is empty or None.

    This function evaluates the given value and returns True if it is falsy, such as None, an empty collection, or zero.

    Args:
        x: The value to check for emptiness or None.

    Returns:
        bool: True if the value is empty or None, False otherwise.
    """
    return not bool(x)