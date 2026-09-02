"""
CARD DISTRIBUTION Constraint Satisfaction Problem (CSP) USING CPMPY
=============================================================
GitHub: https://github.com/CPMpy/cpmpy
PyPI: https://pypi.org/project/cpmpy/
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cpmpy as cp

if TYPE_CHECKING:
    from cpmpy.expressions.variables import NDVarArray


class CardDistributionSolver:
    """Represent a card distribution constraint satisfaction problem instance.

    This class encapsulates the configuration and solving of a CSP that models how
    cards can be distributed among players while respecting hand sizes and card
    holding possibilities.

    Args:
        hand_card_lengths: A list containing the number of cards expected in each players hand, starting at player_id 0.
        possible_players_holding_card: A list of binary flag lists, where each inner list represents a card and each position represents a player. A value of 1 means that the player may hold the card.
    """

    def __init__(
        self,
        hand_card_lengths: list[int],
        possible_players_holding_card: list[list[int]],
    ) -> None:
        """Initialize a new card distribution constraint satisfaction problem instance.

        This constructor prepares the internal state required to model card distributions
        as a constraint satisfaction problem for the given player and game status.

        Args:
            hand_card_lengths: A list containing the number of cards expected in each players hand, starting at player_id 0.
                Example at start of the game: [9, 9, 9, 9], because player1, player2, player3, player4 all have 9 handcards.
            possible_players_holding_card: A list of binary flag lists, where each inner list represents a card and each position represents a player. For example, [1, 0, 1, 1] means players 0, 2, and 3 may hold the card.
        """
        self.hand_card_lengths = hand_card_lengths
        self.possible_players_holding_card = possible_players_holding_card
        self.number_of_players = len(hand_card_lengths)
        self.number_of_cards = len(possible_players_holding_card)
        self._hamming_distance: int = 1
        # The extra value represents cards that have already been played.
        self.cards: NDVarArray = cp.intvar(
            0, self.number_of_players, shape=self.number_of_cards
        )
        self.model: cp.Model = cp.Model()
        self.solver: cp.SolverLookup = cp.SolverLookup.get("ortools", self.model)
        self._initialize_problem()

    def _initialize_problem(self) -> None:
        """Set up the CSP variables and constraints for card distribution.

        This method restricts each card variable to its candidate players and adds a
        global cardinality constraint to enforce the configured hand sizes.
        """
        for card, flags in zip(self.cards, self.possible_players_holding_card):  # noqa: B905
            if len(flags) != self.number_of_players or any(
                flag not in (0, 1) for flag in flags
            ):
                raise ValueError(
                    "Each card possibility row must contain one binary flag "
                    "for every player."
                )

            candidates = [
                player_id for player_id, allowed in enumerate(flags) if allowed
            ] or [self.number_of_players]
            self.model += cp.InDomain(card, candidates)

        self.model += cp.GlobalCardinalityCount(
            list(self.cards),
            list(range(self.number_of_players)),
            self.hand_card_lengths,
        )

        self.solver = cp.SolverLookup.get("ortools", self.model)

    def set_hamming_distance(self, distance: int) -> None:
        """Set the hamming distance

        Args:
            distance (int): _description_
        """
        self._hamming_distance = distance

    def solve_iter(self, already_reset_solver: bool = False) -> list[int]:
        """Search for a card distribution that is maximally different from sampled solutions.

        This method first collects a limited number of feasible card distributions and
        then optimizes for a new solution that maximizes the Hamming distance to these
        sampled candidates.

        Args:
            hamming_distance_candidates: The number of candidate solutions to sample
                before performing the diversity maximization.

        Returns:
            A list representing the optimized card distribution if found, an empty list otherwise.
            Example for four players (0-3) and 4 cards:
            [0, 1, 2, 3] -> First card given to player 0, second card to player 1, etc.
        """
        candidates: list[list[int]] = []
        while len(candidates) < self._hamming_distance and self.solver.solve():  # type: ignore
            candidates.append([int(value) for value in self.cards.value()])

        assert candidates

        self.solver.maximize(  # type: ignore
            cp.sum([cp.sum(self.cards != candidate) for candidate in candidates])
        )

        if self.solver.solve():  # type: ignore
            return [int(card.value()) for card in self.cards]

        if not already_reset_solver:
            self._initialize_problem()  # Reset the model to its original state
            return self.solve_iter(
                already_reset_solver=True
            )  # Retry the process recursively
        raise ValueError(
            "No solution found even after resetting the model. "
            "Please check the constraints and input parameters."
        )


def calculate_upper_world_boundary(csp: CardDistributionSolver) -> int:
    """Calculate the maximum possible worlds (information states) as an upper bound.
    Because CSPs become harder to solve for large problems and we cannot
    cheaply compute the exact number of worlds, a conservative approach is taken.
    This shall estimate the number of possible information states.

    Args:
        csp (CardDistributionSolver): CSP problem.

    Returns:
        int: upper bound of possible worlds.
    """
    factors = list(map(sum, csp.possible_players_holding_card))
    factors = [
        1 if x == 0 else x for x in factors
    ]  # Replace any zero factors with 1 to avoid multiplication by zero
    return math.prod(factors)  # type: ignore


def main() -> None:  # sourcery skip: use-named-expression
    print("Test CardDistributionSolver with a small example:")
    solver = CardDistributionSolver(
        hand_card_lengths=[2, 2],
        possible_players_holding_card=[[0, 1], [1, 1], [1, 1], [1, 0]],
    )

    status = solver.solve_iter()
    if status:
        # Extract the optimized card distribution: card_idx -> player_idx
        solution = [int(card.value()) for card in solver.cards]
        card_to_player = dict(enumerate(solution))
        print(card_to_player)

    print("Upper world boundary:", calculate_upper_world_boundary(solver))


if __name__ == "__main__":
    main()
