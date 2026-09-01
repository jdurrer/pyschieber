import numpy as np
from pyschieber.card import Card
from pyschieber.player.treePlayer.treesearch.ismcts.evaluator import (
    Evaluator,
    RandomRolloutEvaluator,
)
from pyschieber.player.treePlayer.treesearch.ismcts.game_state import GameState
from pyschieber.suit import Suit


class DummyGameState(GameState):
    """Minimal GameState stub for testing RandomRolloutEvaluator."""

    def __init__(
        self,
        num_players: int = 2,
        is_terminal_flag: bool = False,
        is_chance_flag: bool = False,
        legal_actions: list[Card] | None = None,
        chance_outcomes: list[tuple[Card, float]] | None = None,
        returns_list: list[float] | None = None,
    ) -> None:
        # Store simple attributes used by the evaluator
        self._num_players = num_players
        self._is_terminal_flag = is_terminal_flag
        self._is_chance_flag = is_chance_flag
        self._legal_actions = legal_actions or []
        self._chance_outcomes = chance_outcomes or []
        self._returns_list = returns_list or [0.0] * num_players
        # Record actions applied for verification
        self.applied_actions: list[Card] = []

    def clone(self) -> "DummyGameState":
        """Return a shallow clone with the same configuration."""
        clone_state = DummyGameState(
            num_players=self._num_players,
            is_terminal_flag=self._is_terminal_flag,
            is_chance_flag=self._is_chance_flag,
            legal_actions=list(self._legal_actions),
            chance_outcomes=list(self._chance_outcomes),
            returns_list=list(self._returns_list),
        )
        return clone_state

    def is_terminal(self) -> bool:
        return self._is_terminal_flag

    def is_chance_node(self) -> bool:
        return self._is_chance_flag

    def chance_outcomes(self) -> list[tuple[Card, float]]:
        return self._chance_outcomes

    def legal_actions(self) -> list[Card]:
        return self._legal_actions

    def apply_action(self, action: Card) -> None:
        # Record applied action
        self.applied_actions.append(action)
        # For testing, we can optionally mark the state as terminal after one move
        self._is_terminal_flag = True

    def returns(self) -> list[float]:
        return self._returns_list


def test_evaluator_is_abstract() -> None:
    """Evaluator base class should raise NotImplementedError for abstract methods."""
    evaluator = Evaluator()

    dummy_state = DummyGameState()
    try:
        evaluator.evaluate(dummy_state)  # type: ignore[arg-type]
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Evaluator.evaluate did not raise NotImplementedError")

    try:
        evaluator.prior(dummy_state)  # type: ignore[arg-type]
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Evaluator.prior did not raise NotImplementedError")


def test_random_rollout_evaluator_evaluate_terminal_state() -> None:
    """evaluate on a terminal state should return the state's returns directly."""
    returns = [1.0, -1.0]
    state = DummyGameState(
        num_players=2,
        is_terminal_flag=True,
        returns_list=returns,
    )

    evaluator = RandomRolloutEvaluator(
        n_rollouts=5, random_state=np.random.RandomState(0)
    )
    value = evaluator.evaluate(state)

    # Since the state is already terminal, no actions are applied and returns
    # should be the same across rollouts; average equals original returns.
    assert np.allclose(value, np.array(returns))


def test_random_rollout_evaluator_evaluate_non_terminal_state_with_max_length() -> None:
    """evaluate should respect max_length and perform random actions until terminal or max_length."""
    actions = [Card(Suit.BELL, 7), Card(Suit.ROSE, 8)]
    state = DummyGameState(
        num_players=2,
        is_terminal_flag=False,
        is_chance_flag=False,
        legal_actions=actions,
        returns_list=[2.0, -2.0],
    )

    evaluator = RandomRolloutEvaluator(
        n_rollouts=3, random_state=np.random.RandomState(1), max_length=1
    )
    value = evaluator.evaluate(state)

    # After one action, state becomes terminal by design of DummyGameState.apply_action
    # So evaluate should return the returns_list averaged over rollouts (same each time).
    assert np.allclose(value, np.array([2.0, -2.0]))
    # At least one action must have been applied in each rollout
    assert (
        len(state.applied_actions) == 0
    )  # original state is cloned; its list stays empty


def test_random_rollout_evaluator_prior_on_chance_node() -> None:
    """prior on a chance node should delegate to chance_outcomes."""
    actions = [Card(Suit.SHIELD, 7), Card(Suit.ACORN, 8)]
    probs = [0.3, 0.7]
    outcomes = list(zip(actions, probs))
    state = DummyGameState(
        num_players=2,
        is_terminal_flag=False,
        is_chance_flag=True,
        chance_outcomes=outcomes,
    )

    evaluator = RandomRolloutEvaluator(random_state=np.random.RandomState(0))
    prior = evaluator.prior(state)

    assert prior == outcomes


def test_random_rollout_evaluator_prior_on_decision_node_uniform() -> None:
    """prior on a decision node should return uniform probabilities over legal actions."""
    actions = [Card(Suit.ROSE, 7), Card(Suit.BELL, 8), Card(Suit.ACORN, 9)]
    state = DummyGameState(
        num_players=2,
        is_terminal_flag=False,
        is_chance_flag=False,
        legal_actions=actions,
    )

    evaluator = RandomRolloutEvaluator(random_state=np.random.RandomState(0))
    prior = evaluator.prior(state)

    assert len(prior) == len(actions)
    probs = [p for _, p in prior]
    # Uniform distribution
    assert np.allclose(probs, np.full(len(actions), 1.0 / len(actions)))
    # Actions preserved
    returned_actions = [a for a, _ in prior]
    assert returned_actions == actions
