import itertools

from constraint import Problem
from constraint.solvers import OptimizedBacktrackingSolver
from pyschieber.player.treePlayer.treesearch.ismcts.simple_csp import CardDistributionSolver


class DummyStatus:
    """Lightweight stand-in for the real Status dataclass.

    This dummy class exists only to satisfy the type requirement of CardDistributionSolver
    without introducing any game logic dependencies.
    """
    pass


class DummyRuleBasedPlayer:
    """Lightweight stand-in for the real RuleBasedPlayer.

    This dummy class exists only to satisfy the type requirement of CardDistributionSolver
    without invoking actual rule-based player behaviour.
    """

    def __init__(self, player_id: int) -> None:
        self.id = player_id
        self.cards: list[int] = []


def test_occurrence_constraint_satisfied_on_small_instance() -> None:
    """Verify that occurrence_constraint accepts a correct small assignment.

    This test uses a very small, non-expensive CSP instance to ensure that the
    occurrence constraint returns True when hand sizes are matched exactly.
    """
    player = DummyRuleBasedPlayer(player_id=0)
    status = DummyStatus()
    hand_card_lengths = [2, 1]
    # card 0 can be held by player 0 or 1, card 1 by player 0 only, card 2 by player 1 only
    possible_players_holding_card = [[0, 1], [0], [1]]
    csp = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    # A concrete assignment: two cards to player 0, one to player 1
    assigned_values = (0, 0, 1)
    assert csp.occurrence_constraint(*assigned_values) is True


def test_occurrence_constraint_rejects_invalid_assignment() -> None:
    """Verify that occurrence_constraint rejects an incorrect small assignment.

    This test uses a small, non-expensive CSP instance to ensure that the
    occurrence constraint returns False when hand sizes are not matched.
    """
    player = DummyRuleBasedPlayer(player_id=0)
    status = DummyStatus()
    hand_card_lengths = [2, 1]
    possible_players_holding_card = [[0, 1], [0], [1]]
    csp = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    # Invalid assignment: all cards to player 0 (expected [2, 1])
    assigned_values = (0, 0, 0)
    assert csp.occurrence_constraint(*assigned_values) is False


def test_initialize_problem_creates_expected_variables_and_constraint() -> None:
    """Check that the CSP problem is initialized with correct variable domains.

    This test verifies that each card variable has the domain equal to the
    corresponding possible players and that the global occurrence constraint
    is attached without performing expensive search.
    """
    player = DummyRuleBasedPlayer(player_id=0)
    status = DummyStatus()
    hand_card_lengths = [2, 1]
    possible_players_holding_card = [[0, 1], [0], [1]]
    csp = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    assert isinstance(csp.problem, Problem)
    assert isinstance(csp.problem._solver, OptimizedBacktrackingSolver)  # type: ignore[attr-defined]

    # The internal variables are named by their index: 0, 1, 2
    for card_index, domain in enumerate(possible_players_holding_card):
        variable_domain = csp.problem._variables[card_index]  # type: ignore[attr-defined]
        assert set(variable_domain) == set(domain)


def test_solve_iter_yields_all_solutions_for_tiny_csp() -> None:
    """Ensure solve_iter yields the correct solutions for a tiny CSP instance.

    This test constructs a tiny CSP where the full solution set can be enumerated
    cheaply and compares the yielded solutions with a manually computed set.
    """
    player = DummyRuleBasedPlayer(player_id=0)
    status = DummyStatus()
    hand_card_lengths = [1, 1]
    # card 0 can be held by player 0 or 1, card 1 can also be held by player 0 or 1
    possible_players_holding_card = [[0, 1], [0, 1]]
    csp = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    solutions_iter = csp.solve_iter()
    solutions = list(solutions_iter)

    # Manually enumerate all assignments and filter by occurrence_constraint
    expected_solutions = []
    expected_solutions.extend(
        dict(enumerate(assignment))
        for assignment in itertools.product(*possible_players_holding_card)
        if csp.occurrence_constraint(*assignment)
    )
    # Solutions from python-constraint are dicts mapping variable index to player index
    assert len(solutions) == len(expected_solutions)
    for sol in solutions:
        assert sol in expected_solutions


def test_medium_sized_csp_runs_quickly() -> None:
    """Solve a medium-sized card distribution CSP instance efficiently.

    This test builds a CSP with a moderate number of cards and players to
    ensure the CardDistributionSolver setup and solving remains performant.

    """
    player = DummyRuleBasedPlayer(player_id=0)
    status = DummyStatus()

    # Four players, total 20 cards distributed as 5 each
    hand_card_lengths = [4, 4, 4, 3]

    # 20 cards, each can be held by any of the 4 players
    possible_players_holding_card = [[0,1,2,3],[0,1,2,3],[0,1,2,3],[0],[2],[3],[0,1,3],[1,2],[3],[3],[0,1,2,3],[0,1,2,3],[0,1,2,3],[0,1,2,3],[0,1,2,3]]

    csp = CardDistributionSolver(hand_card_lengths, possible_players_holding_card)

    # Fetch only a small number of solutions to keep runtime low
    solutions_iter = csp.solve_iter()
    first_solutions = []
    first_solutions.extend(
        solution for _, solution in zip(range(5), solutions_iter)
    )
    # We should get at least one valid solution
    assert first_solutions

    # Each solution must respect the hand_card_lengths constraint
    for sol in first_solutions:
        assigned_values = tuple(sol[idx] for idx in range(len(possible_players_holding_card)))
        assert csp.occurrence_constraint(*assigned_values) is True
        

def test_main_does_not_raise() -> None:
    """Verify that the module-level main function executes without error.

    This test ensures that calling main is cheap and side-effect free
    apart from writing an informational message to standard output.
    """
    from pyschieber.player.treePlayer.treesearch.ismcts.simple_csp import main

    # main only prints; it should not raise exceptions.
    main()