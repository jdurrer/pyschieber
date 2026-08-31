import numpy as np
from numpy.typing import NDArray

from pyschieber.card import Card
from pyschieber.player.treePlayer.treesearch.ismcts.game_state import GameState


class ChanceNodeError(Exception):
    """Raised when a chance node is encountered in a game without chance nodes."""


class Evaluator:
    """Abstract class representing an evaluation function for a game.

    The evaluation function takes in an intermediate state in the game and returns
    an evaluation of that state, which should correlate with chances of winning
    the game. It returns the evaluation from all player's perspectives.
    """

    def evaluate(self, state: GameState) -> NDArray[np.float64]:
        """Returns evaluation on given state."""
        raise NotImplementedError

    def prior(self, state: GameState) -> list[tuple[Card, float]]:
        """Returns a probability for each legal action in the given state."""
        raise NotImplementedError


class RandomRolloutEvaluator(Evaluator):
    """A simple evaluator doing random rollouts.

    This evaluator returns the average outcome of playing random actions from the
    given state until the end of the game.  n_rollouts is the number of random
    outcomes to be considered.
    """

    def __init__(
        self, n_rollouts: int = 1, random_state=None, max_length: int | None = None
    ) -> None:
        self.n_rollouts = n_rollouts
        self.max_length = max_length
        self._random_state: np.random.RandomState = (
            random_state or np.random.RandomState()
        )

    def evaluate(self, state: GameState) -> NDArray[np.float64]:
        # sourcery skip: remove-unnecessary-else
        """Returns evaluation on given state."""
        result = None
        for _ in range(self.n_rollouts):
            working_state = state.clone()
            length = 0
            while not working_state.is_terminal():
                if working_state.is_chance_node():
                    raise ChanceNodeError(
                        "Jass has no chance nodes. This code shall never be executed."
                    )
                    # outcomes = working_state.chance_outcomes()
                    # action_list, prob_list = zip(*outcomes)
                    # action = self._random_state.choice(action_list, p=prob_list)
                else:
                    legal_actions = working_state.legal_actions()
                    action = legal_actions[
                        self._random_state.choice(len(legal_actions))
                    ]
                working_state.apply_action(action)
                length += 1
                if self.max_length is not None and length >= self.max_length:
                    break
            returns = np.array(working_state.returns())
            result = returns if result is None else result + returns

        return result / self.n_rollouts  # type: ignore

    def prior(self, state: GameState) -> list[tuple[Card, float]]:
        """Returns equal probability for all actions."""
        if state.is_chance_node():
            return state.chance_outcomes()  # type: ignore
        legal_actions = state.legal_actions()
        return [(action, 1.0 / len(legal_actions)) for action in legal_actions]
