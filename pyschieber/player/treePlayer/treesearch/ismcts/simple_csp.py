"""
CARD DISTRIBUTION Constaint Satisfactio Problem (CSP) USING PYTHON-CONSTRAINT2
=============================================================
GitHub: https://github.com/python-constraint/python-constraint
PyPI: https://pypi.org/project/python-constraint2/
"""

from collections import Counter
from collections.abc import Iterator
from typing import Any, Never

from constraint import Problem
from constraint.solvers import OptimizedBacktrackingSolver


class CardDistributionSolver:
    """Represent a card distribution constraint satisfaction problem instance.

    This class encapsulates the configuration and solving of a CSP that models how
    cards can be distributed among players while respecting hand sizes and card
    holding possibilities.

    Args:
        player: The rule-based player for whom the card distribution is being modeled.
        hand_card_lengths: A list containing the number of cards expected in each players hand, starting at player_id 0.
        possible_players_holding_card: A list of lists, where each inner list represents a card and the values represent which players are able to hold said card.
        state: The current game status used to contextualize the card distribution problem.
    """
    def __init__(self,  
                 hand_card_lengths: list[int], 
                 possible_players_holding_card: list[list[int]], 
                 ) -> None:
        """Initialize a new card distribution constraint satisfaction problem instance.

        This constructor prepares the internal state required to model card distributions
        as a constraint satisfaction problem for the given player and game status.

        Args:
            player: The rule-based player for whom the card distribution is being modeled.
            hand_card_lengths: A list containing the number of cards expected in each players hand, starting at player_id 0.
                Example at start of the game: [9, 9, 9, 9], because player1, player2, player3, player4 all have 9 handcards.
            possible_players_holding_card: A list of lists, where each inner list represents a card and the values represent which players are able to hold said card.
                Example: [[1,2,3],[1],[1,3,4],...] -> player1,2,3 can hold first card, only player1 can hold second card, etc.
            state: The current game status used to contextualize the card distribution problem.
        """
        self.hand_card_lengths = hand_card_lengths
        self.possible_players_holding_card = possible_players_holding_card
        self.number_of_players = len(hand_card_lengths)
        self.number_of_cards = len(possible_players_holding_card)
        self.problem: Problem = Problem(OptimizedBacktrackingSolver())
        self._initialize_problem()


    def occurrence_constraint(self, *assigned_values: int) -> bool:
        """Check whether the assigned values match the required hand card lengths.

        This constraint validates that the number of occurrences of each player index in
        the assigned values is exactly equal to the predefined hand card lengths.

        Args:
            assigned_values: The values assigned to the CSP variables for this constraint.

        Returns:
            True if the number of occurrences of each player index matches the configured
            hand card lengths, otherwise False.
        """
        value_counts: Counter[int] = Counter(assigned_values)
        expected_counts: list[int] = self.hand_card_lengths
        return [value_counts.get(player_idx, 0) for player_idx in range(self.number_of_players)] == expected_counts
    

    def _initialize_problem(self) -> None:
        """Set up the CSP variables and constraints for card distribution.

        This method initializes one variable per card with domains representing
        candidate players, and adds a global constraint to enforce hand sizes.

        """
        variable_names = range(self.number_of_cards)
        for variable, candidates in enumerate(self.possible_players_holding_card):
            self.problem.addVariable(variable, candidates)

        # self.problem.addVariables(variable_names, self.possible_players_holding_card)
        self.problem.addConstraint(self.occurrence_constraint, variable_names)


    def solve_iter(self) -> Iterator[Never] | Any:
        """Return an iterator over all valid card distribution solutions.

        This method provides a lazy interface to iterate through each solution
        that satisfies the configured card distribution constraints.

        Returns:
            An iterator yielding solutions to the card distribution constraint
            satisfaction problem.
        """
        return self.problem.getSolutionIter()


def main() -> None:
    print('This file cannot be run by itself.')


if __name__ == "__main__":
    main()