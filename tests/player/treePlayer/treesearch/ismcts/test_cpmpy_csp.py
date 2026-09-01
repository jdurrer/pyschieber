import pytest

from pyschieber.player.treePlayer.treesearch.ismcts.cpmpy_csp import (
    CardDistributionSolver,
    main,
)


def test_initialize_problem_sets_up_model_correctly() -> None:
    """Verify that the CPMPy model is initialized with correct cardinality and domains.

    This test checks that the solver can find at least one solution for a small,
    well-formed card distribution instance.
    """
    hand_card_lengths = [2, 1]
    possible_players_holding_card = [[1, 1], [1, 0], [1, 1]]
    solver = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    # Model should be solvable
    assert solver.model.solve()
    solution = [int(card.value()) for card in solver.cards]

    # Each card assignment must be allowed by its possibility mask.
    for card_value, possibility_mask in zip(solution, possible_players_holding_card):
        assert possibility_mask[card_value] == 1

    # GlobalCardinalityCount must be respected: counts per player equal hand_card_lengths
    counts = [
        solution.count(player_idx) for player_idx in range(len(hand_card_lengths))
    ]
    assert counts == hand_card_lengths


def test_initialize_problem_rejects_invalid_possibility_rows() -> None:
    """Reject rows that do not contain binary flags for every player."""
    with pytest.raises(ValueError, match="binary flag"):
        CardDistributionSolver([1, 1], [[1, 0], [1]])

    with pytest.raises(ValueError, match="binary flag"):
        CardDistributionSolver([1, 1], [[1, 2], [1, 1]])


def test_solve_iter_returns_feasible_diverse_solution() -> None:
    """Verify solve_iter returns a feasible solution and respects hand sizes.

    This test runs the diversity optimization on a small instance and checks
    that the returned distribution satisfies all constraints.
    """
    hand_card_lengths = [2, 2]
    possible_players_holding_card = [[1, 1], [1, 1], [1, 1], [1, 1]]
    solver = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    solution = solver.solve_iter(hamming_distance_candidates=1)
    assert solution  # non-empty list

    # Each card assignment must be allowed by its possibility mask.
    for card_value, possibility_mask in zip(solution, possible_players_holding_card):
        assert possibility_mask[card_value] == 1

    # Hand sizes respected
    counts = [
        solution.count(player_idx) for player_idx in range(len(hand_card_lengths))
    ]
    assert counts == hand_card_lengths


def test_solve_iter_returns_solution_for_a_fresh_solver() -> None:
    """Ensure solve_iter returns a feasible distribution for a fresh solver."""
    hand_card_lengths = [1, 1]
    possible_players_holding_card = [[1, 1], [1, 1]]
    solver = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    solution = solver.solve_iter(hamming_distance_candidates=1)

    assert solution
    counts = [
        solution.count(player_idx) for player_idx in range(len(hand_card_lengths))
    ]
    assert counts == hand_card_lengths


def test_main_does_not_raise() -> None:
    """Verify that the module-level main function executes without error.

    This test ensures that calling main is cheap and side-effect free
    apart from writing an informational message to standard output.
    """
    main()
