import copy

import numpy as np
import pytest

from pyschieber.card import Card
from pyschieber.player.treePlayer.treesearch.ismcts.evaluator import Evaluator
from pyschieber.player.treePlayer.treesearch.ismcts.game_state import GameState
from pyschieber.player.treePlayer.treesearch.ismcts.ismcts import (
    UNEXPANDED_VISIT_COUNT,
    ChildInfo,
    ChildSelectionPolicy,
    ISMCTSBot,
    ISMCTSFinalPolicyType,
    ISMCTSNode,
)
from pyschieber.suit import Suit


class DummyGameState(GameState):
    """Minimal GameState stub for testing ISMCTSBot.

    This stub bypasses the full GameState initialization and only provides the
    attributes and methods that ISMCTSBot interacts with, including a dummy
    `informationset` field to satisfy resampling logic.
    """

    def __init__(
        self,
        num_players: int = 2,
        current_player: int = 0,
        legal_actions: list[Card] | None = None,
        is_terminal_flag: bool = False,
        is_chance_flag: bool = False,
        chance_outcomes: list[tuple[Card, float]] | None = None,
        returns_list: list[float] | None = None,
        info_state_id: int = 0,
    ) -> None:
        # Dummy fields needed by ISMCTSBot and Evaluator
        self._num_players = num_players
        self._current_player = current_player
        self._legal_actions = legal_actions or []
        self._is_terminal_flag = is_terminal_flag
        self._is_chance_flag = is_chance_flag
        self._chance_outcomes = chance_outcomes or []
        self._returns_list = returns_list or [0.0] * num_players
        self._info_state_id = info_state_id
        self.applied_actions: list[Card] = []

    def clone(self) -> "DummyGameState":
        return copy.deepcopy(self)

    def resample_from_infostate(self, informationset=None) -> "DummyGameState":
        """Return an independent determinizated copy for the simulation.

        The production method receives an information-set solver. The solver
        is irrelevant for this minimal test state, so it is accepted but not
        used.
        """
        return self.clone()

    def current_player(self) -> int:
        return self._current_player

    def information_state_string(self) -> int:
        return self._info_state_id

    def is_terminal(self) -> bool:
        return self._is_terminal_flag

    def is_chance_node(self) -> bool:
        return self._is_chance_flag

    def chance_outcomes(self) -> list[tuple[Card, float]]:  # type: ignore
        return self._chance_outcomes

    def legal_actions(self) -> list[Card]:
        return self._legal_actions

    def apply_action(self, action: Card) -> None:
        self.applied_actions.append(action)
        # For testing, mark state as terminal after one move
        self._is_terminal_flag = True

    def returns(self) -> list[float]:  # type: ignore
        return self._returns_list


class DummyEvaluator(Evaluator):
    """Minimal Evaluator stub: uniform priors, fixed value."""

    def __init__(self, value: float = 0.0) -> None:
        self._value = value

    def evaluate(self, state: GameState) -> np.ndarray:
        num_players = len(state.returns())
        return np.full(num_players, self._value, dtype=np.float64)

    def prior(self, state: GameState):
        legal_actions = state.legal_actions()
        if not legal_actions:
            return []
        p = 1.0 / len(legal_actions)
        return [(a, p) for a in legal_actions]


def make_bot(**kwargs):
    return ISMCTSBot(informationset=None, **kwargs)


def test_childinfo_value_computes_mean_return() -> None:
    child = ChildInfo(visits=4, return_sum=10.0, prior=0.5)
    assert child.value() == 2.5


def test_normalized_visited_policy() -> None:
    node = ISMCTSNode()
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    node.child_info[a1] = ChildInfo(visits=2, return_sum=0.0, prior=0.5)
    node.child_info[a2] = ChildInfo(visits=1, return_sum=0.0, prior=0.5)
    node.total_visits = 3

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
        final_policy_type=ISMCTSFinalPolicyType.NORMALIZED_VISITED_COUNT,
    )

    policy = bot.normalized_visited_policy(node)
    assert dict(policy)[a1] == pytest.approx(2 / 3)
    assert dict(policy)[a2] == pytest.approx(1 / 3)


def test_max_visit_policy_ties_split_evenly() -> None:
    node = ISMCTSNode()
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    node.child_info[a1] = ChildInfo(visits=3, return_sum=0.0, prior=0.5)
    node.child_info[a2] = ChildInfo(visits=3, return_sum=0.0, prior=0.5)
    node.total_visits = 6

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
        final_policy_type=ISMCTSFinalPolicyType.MAX_VISIT_COUNT,
    )

    policy = bot.max_visit_policy(node)
    probs = dict(policy)
    assert probs[a1] == pytest.approx(0.5)
    assert probs[a2] == pytest.approx(0.5)


def test_max_value_policy_uses_child_value() -> None:
    node = ISMCTSNode()
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    node.child_info[a1] = ChildInfo(visits=2, return_sum=4.0, prior=0.5)  # value=2.0
    node.child_info[a2] = ChildInfo(visits=2, return_sum=6.0, prior=0.5)  # value=3.0
    node.total_visits = 4

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
        final_policy_type=ISMCTSFinalPolicyType.MAX_VALUE,
    )

    policy = bot.max_value_policy(node)
    probs = dict(policy)
    assert probs[a2] == pytest.approx(1.0)
    assert probs[a1] == pytest.approx(0.0)


def test_pad_policy_with_unexpanded_actions_adds_zero_prob_entries() -> None:
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    a3 = Card(Suit.SHIELD, 9)
    state = DummyGameState(legal_actions=[a1, a2, a3])

    node = ISMCTSNode()
    node.child_info[a1] = ChildInfo(visits=1, return_sum=0.0, prior=0.5)
    node.total_visits = 1

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )

    base_policy = [(a1, 1.0)]
    final_policy = bot._pad_policy_with_unexpanded_actions(state, node, base_policy)
    probs = dict(final_policy)

    assert probs[a1] == pytest.approx(1.0)
    assert probs[a2] == pytest.approx(0.0)
    assert probs[a3] == pytest.approx(0.0)


def test_get_state_key_uses_current_player_and_info_state() -> None:
    state = DummyGameState(current_player=1, info_state_id=42)
    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )
    assert bot.get_state_key(state) == (1, 42)


def test_create_and_lookup_node() -> None:
    state = DummyGameState(current_player=0, info_state_id=1)
    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )
    assert bot.lookup_node(state) is None

    node = bot.create_new_node(state)
    assert node.total_visits == UNEXPANDED_VISIT_COUNT
    assert bot.lookup_node(state) is node


def test_filter_illegals_removes_children_not_in_legal_actions() -> None:
    node = ISMCTSNode()
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    node.child_info[a1] = ChildInfo(visits=2, return_sum=0.0, prior=0.5)
    node.child_info[a2] = ChildInfo(visits=3, return_sum=0.0, prior=0.5)
    node.total_visits = 5

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )
    legal_actions = [a1]
    new_node = bot.filter_illegals(node, legal_actions)

    assert a1 in new_node.child_info
    assert a2 not in new_node.child_info
    assert new_node.total_visits == 2


def test_expand_if_necessary_adds_child_with_prior() -> None:
    a1 = Card(Suit.BELL, 7)
    state = DummyGameState(legal_actions=[a1])
    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )
    node = ISMCTSNode()
    node.prior_map[a1] = 0.8

    bot.expand_if_necessary(state, node, a1)
    assert a1 in node.child_info
    assert node.child_info[a1].prior == pytest.approx(0.8)


def test_action_value_uct_increases_with_exploration() -> None:
    node = ISMCTSNode()
    node.total_visits = 10
    child = ChildInfo(visits=2, return_sum=4.0, prior=0.5)  # value=2.0

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        uct_c=1.0,
        random_state=np.random.RandomState(0),
        child_selection_policy=ChildSelectionPolicy.UCT,
    )

    value = bot._action_value(node, child)
    # Should be greater than plain value due to exploration term
    assert value > child.value()


def test_select_candidate_actions_respects_tie_tolerance() -> None:
    node = ISMCTSNode()
    node.total_visits = 10
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    node.child_info[a1] = ChildInfo(visits=5, return_sum=10.0, prior=0.5)
    node.child_info[a2] = ChildInfo(visits=5, return_sum=10.0, prior=0.5)

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )

    candidates = bot._select_candidate_actions(node)
    assert set(candidates) == {a1, a2}


def test_check_expand_returns_unexpanded_action_or_invalid() -> None:
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    legal_actions = [a1, a2]

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )

    node = ISMCTSNode()
    # No children yet: should return some legal action
    action = bot.check_expand(node, legal_actions)
    assert action in legal_actions

    # Add both actions as children: should return _InvalidAction
    node.child_info[a1] = ChildInfo(1, 0.0, 0.5)
    node.child_info[a2] = ChildInfo(1, 0.0, 0.5)
    action2 = bot.check_expand(node, legal_actions)
    from pyschieber.player.treePlayer.treesearch.ismcts.ismcts import _InvalidAction

    assert isinstance(action2, _InvalidAction)


def test_run_simulation_terminal_returns_state_returns() -> None:
    state = DummyGameState(
        num_players=2, is_terminal_flag=True, returns_list=[1.0, -1.0]
    )
    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )

    result = bot.run_simulation(state)
    assert np.allclose(result, np.array([1.0, -1.0]))


def test_run_search_single_legal_action_returns_deterministic_policy() -> None:
    a1 = Card(Suit.BELL, 7)
    state = DummyGameState(num_players=2, legal_actions=[a1], returns_list=[0.0, 0.0])
    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=10,
        random_state=np.random.RandomState(0),
    )

    policy = bot.run_search(state)
    assert policy == [(a1, 1.0)]


def test_get_policy_and_step_raise_on_chance_node() -> None:
    a1 = Card(Suit.BELL, 7)
    state = DummyGameState(
        num_players=2,
        legal_actions=[a1],
        is_chance_flag=True,
        chance_outcomes=[(a1, 1.0)],
    )

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=1,
        random_state=np.random.RandomState(0),
    )

    with pytest.raises(ValueError):
        bot.get_policy(state)

    with pytest.raises(ValueError):
        bot.step(state)


def test_step_with_policy_returns_policy_and_sampled_action() -> None:
    a1 = Card(Suit.BELL, 7)
    a2 = Card(Suit.ROSE, 8)
    state = DummyGameState(
        num_players=2, legal_actions=[a1, a2], returns_list=[0.0, 0.0]
    )

    bot = make_bot(
        evaluator=DummyEvaluator(),
        max_simulations=5,
        random_state=np.random.RandomState(0),
    )

    policy, action = bot.step_with_policy(state)
    assert isinstance(policy, list)
    assert action in [a1, a2]
