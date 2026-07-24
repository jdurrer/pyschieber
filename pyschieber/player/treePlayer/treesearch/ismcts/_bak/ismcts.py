# original source: https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/ismcts.py

# Copyright 2019 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""An implementation of Information Set Monte Carlo Tree Search (IS-MCTS).

See Cowling, Powley, and Whitehouse 2011.
https://ieeexplore.ieee.org/document/6203567
"""

import copy
import enum
from typing import Any
from absl import logging
import numpy as np
import pyspiel # TODO replace here and everywhere in code + typehints.

UNLIMITED_NUM_WORLD_SAMPLES: int = -1
UNEXPANDED_VISIT_COUNT:int = -1
TIE_TOLERANCE: float = 1e-5


class ISMCTSFinalPolicyType(enum.Enum):
    """A enumeration class for final ISMCTS policy type.

    Args:
        enum (Enum): 
    """
    NORMALIZED_VISITED_COUNT = 1
    MAX_VISIT_COUNT = 2
    MAX_VALUE = 3


class ChildSelectionPolicy(enum.Enum):
    """A enumeration class for children selection in ISMCTS.

    UCT - Upper Confidence bounds applied to Trees
    classic MCTS selection rule. 

    PUCT - Predictor + UTC
    Adds a prior probability for each action from heuristic.

    Args:
        enum (Enum): selection formulas for child node.
    """
    UCT = 1
    PUCT = 2


class ChildInfo(object):
    """
    Child node information for the search tree with visit statistics and prior probability.

    This constructor stores the number of visits, accumulated return, and
    prior probability associated with the child node.

    Args:
        visits: The number of times this child node has been visited.
        return_sum: The accumulated return value for this child node.
        prior: The prior probability assigned to this child node.
    """
    def __init__(self, visits, return_sum, prior) -> None:
        self.visits: int = visits
        self.return_sum: float = return_sum
        self.prior: float = prior


    def value(self) -> float:
        return self.return_sum / self.visits


class ISMCTSNode(object):
    """
    Node data structure for the search tree.
    Initialize an IS-MCTS node with empty statistics and priors.


    This constructor prepares containers for child visit statistics and
    prior probabilities used during tree search.

    The action (card to play) is represented by an integer (action ID).
    i.e. possible actions are represented in a list and the integer points to the action in the list.

    """    

    def __init__(self) -> None:
        self.child_info: dict[int, ChildInfo] = {}
        self.total_visits: int = 0
        self.prior_map: dict[int, float] = {}


class ISMCTSBot(pyspiel.Bot): # TODO
    """Create an ISMCTS-based bot configured for a specific game and evaluator.

    This bot runs Information Set Monte Carlo Tree Search to select actions
    using a configurable number of simulations and child selection policy.

    Args:
        game: The OpenSpiel game for which this bot will act.
        evaluator: The evaluation object providing priors and value estimates.
        uct_c: The exploration constant used in the tree policy.
        max_simulations: The maximum number of simulations to run per move.
        max_world_samples: The maximum number of root determinizations to cache.
        random_state: Optional numpy random state for reproducibility.
        final_policy_type: How to derive the final action policy from the tree.
        use_observation_string: Whether to key nodes by observation instead of information state.
            False (default): player-specific, hidden-information description. Uses hidden info and public info for each player.
            True: only observable part of the state is used? # TODO Implement? Ignore? Remove?
        allow_inconsistent_action_sets: Whether to tolerate differing legal action sets across determinizations.
        child_selection_policy: The strategy used to score and select child actions during search.

    Adapted from the C++ implementation.
    """
    
    def __init__(self,
               game: pyspiel.Game,
               evaluator,
               uct_c: float,
               max_simulations: int,
               max_world_samples: int = UNLIMITED_NUM_WORLD_SAMPLES,
               random_state=None,
               final_policy_type: ISMCTSFinalPolicyType = ISMCTSFinalPolicyType.MAX_VISIT_COUNT,
               use_observation_string: bool = False,
               allow_inconsistent_action_sets: bool = False,
               child_selection_policy: ChildSelectionPolicy = ChildSelectionPolicy.UCT) -> None:

        pyspiel.Bot.__init__(self)
        self._game = game
        self._evaluator = evaluator
        self._uct_c = uct_c
        self._max_simulations = max_simulations
        self._max_world_samples = max_world_samples
        self._final_policy_type = final_policy_type
        self._use_observation_string = use_observation_string
        self._allow_inconsistent_action_sets = allow_inconsistent_action_sets
        self._nodes: dict[tuple[int, str], ISMCTSNode] = {}
        self._node_pool: list[ISMCTSNode] = []
        self._root_samples: list[pyspiel.State] = []
        self._random_state: np.random.RandomState = random_state or np.random.RandomState()
        self._child_selection_policy = child_selection_policy
        self._resampler_cb = None


    def random_number(self) -> float:
        return self._random_state.uniform()


    def reset(self) -> None:
        self._nodes = {}
        self._node_pool = []
        self._root_samples = []


    def get_state_key(self, state: pyspiel.State) -> tuple[int, str]: # TODO
        """Return a key representing the current information state.

        Args:
            state (_type_): The game state from which to derive the key.

        Returns:
            tuple[int, str]: current player index as integer, information about state as string. # TODO adapt to work with pyschieber.
        """
        if self._use_observation_string:
            return state.current_player(), state.observation_string()
        else:
            return state.current_player(), state.information_state_string()


    def normalized_visited_policy(self, node: ISMCTSNode) -> list[tuple[int, float]]:
        """Compute a probability distribution proportional to visit counts.

        This policy assigns each action a probability equal to its visit
        count divided by the total number of visits at the node.

        Args:
            state (pyspiel.State): The current game state associated with the node.
            node (ISMCTSNode): The ISMCTS node whose child visit statistics define the policy.

        Returns:
            list[tuple[int, float]]: policy - A list of (action, probability) pairs representing a normalized
            distribution over the node's child actions.
        """
        assert node.total_visits > 0
        total_visits = node.total_visits
        return [
            (action, child.visits / total_visits)
            for action, child in node.child_info.items()
        ]


    def max_visit_policy(self, node: ISMCTSNode) -> list[tuple[int, float]]:
        """Compute a policy that selects actions with the highest visit count.

        This policy assigns equal probability to all actions that share the
        maximum number of visits and zero probability to all other actions.

        Args:
            node (ISMCTSNode): The node whose child visit statistics define the policy.

        Returns:
            list[tuple[int, float]]: policy - A list of (action, probability) pairs where
            actions with the highest visit count share the probability mass.
        """
        assert node.total_visits > 0
        max_visits = -float('inf')
        count = 0
        for action, child in node.child_info.items():
            if child.visits == max_visits:
                count += 1
            elif child.visits > max_visits:
                max_visits = child.visits
                count = 1
        return [(action, 1. / count if child.visits == max_visits else 0.0)
                    for action, child in node.child_info.items()]


    def max_value_policy(self, node: ISMCTSNode) -> list[tuple[int, float]]:
        """Compute a policy that selects actions with the highest estimated value.

        This policy assigns equal probability to all actions whose mean return
        matches the maximum value at the node and zero probability to all others.

        Args:
            node (ISMCTSNode): The node whose child value statistics define the policy.

        Returns:
            list[tuple[int, float]]: A list of (action, probability) pairs where
            actions with the highest value share the probability mass.
        """
        assert node.total_visits > 0
        max_value = -float('inf')
        count = 0
        for action, child in node.child_info.items():
            if child.value() == max_value:
                count += 1
            elif child.value() > max_value:
                max_value = child.value()
                count = 1
        return [(action, 1. / count if child.value() == max_value else 0.0)
                    for action, child in node.child_info.items()]


    def _compute_base_policy(self, node: ISMCTSNode) -> list[tuple[int, float]]:
        """Compute the base policy from the node according to the configured final policy type.

        This method selects and applies the appropriate policy computation
        method based on the current final policy configuration.

        Args:
            node (ISMCTSNode): The ISMCTS node whose statistics define the base policy.

        Raises:
            ValueError: An unexpected policy is received. Error risen because no policy can be constructed.

        Returns:
            list[tuple[int, float]]: policy - A list of (action, probability) pairs representing the base policy.
        """
        if (self._final_policy_type == ISMCTSFinalPolicyType.NORMALIZED_VISITED_COUNT):
            return self.normalized_visited_policy(node)
        elif self._final_policy_type == ISMCTSFinalPolicyType.MAX_VISIT_COUNT:
            return self.max_visit_policy(node)
        elif self._final_policy_type == ISMCTSFinalPolicyType.MAX_VALUE:
            return self.max_value_policy(node)
        else:
            raise ValueError('An undefined policy was received.')


    def _pad_policy_with_unexpanded_actions(
        self,
        state: pyspiel.State,
        node: ISMCTSNode,
        policy: list[tuple[int, float]]
    ) -> list[tuple[int, float]]: # TODO
        """Extend the policy to include all legal actions with zero probability if needed.

        This ensures that every legal action in the state appears in the policy,
        assigning zero probability to actions that have not been expanded.

        Args:
            state (pyspiel.State): The game state whose legal actions must be covered by the policy.
            node (ISMCTSNode): The ISMCTS node associated with the state.
            policy (list[tuple[int, float]]): The already computed base policy to extend.

        Returns:
            list[tuple[int, float]]: The extended policy including missing legal actions with zero probability.
        """
        
        legal_actions = state.legal_actions()
        if len(policy) < len(legal_actions):  # do we really need this step? (not my comment)
            policy.extend(
                (action, 0.0)
                for action in legal_actions
                if action not in node.child_info
            )
        return policy


    def get_final_policy(self, state: pyspiel.State, node: ISMCTSNode) -> list[tuple[int, float]]:
        """Compute the final action policy for a state and its corresponding search node.

        This method derives a base policy from the node statistics and then
        ensures that all legal actions in the given state are represented by
        padding with zero-probability entries for unexpanded actions.

        Args:
            state (pyspiel.State): The current game state whose legal actions define the policy support.
            node (ISMCTSNode): The search node whose visit and value statistics form the base policy.

        Returns:
            list[tuple[int, float]]: A list of (action, probability) pairs representing the final policy.
        """
        assert node

        policy = self._compute_base_policy(node)
        policy = self._pad_policy_with_unexpanded_actions(state, node, policy)
        return policy


    def resample_from_infostate(self, state: pyspiel.State) -> pyspiel.State: # TODO
        """Resample a determinizated state consistent with the current information state.

        This method returns a single `pyspiel.State` sample drawn from the
        information state of the current player, using either a custom callback
        or the game's built-in resampling mechanism.

        Args:
            state (pyspiel.State): The game state whose information state is used as
                the basis for generating a new determinizated state.

        Returns:
            pyspiel.State: A newly sampled state compatible with the current player's
            information state in the provided `state`.
        """
        if self._resampler_cb:
            return self._resampler_cb(state, state.current_player())
        else:
            return state.resample_from_infostate(
            state.current_player(), pyspiel.UniformProbabilitySampler(0., 1.))
        

    def sample_root_state(self, state: pyspiel.State) -> pyspiel.State: # TODO
        """Sample or reuse a root determinizated state for the current information state.

        This method manages a cache of previously resampled root states up to
        a configured limit and returns either a new resample or a cloned cached state.

        Args:
            state (pyspiel.State): The original game state whose information state
                defines the root determinizations to be sampled or reused.

        Raises:
            pyspiel.SpielError: If an unexpected number of cached world samples is
                encountered relative to the configured maximum.

        Returns:
            pyspiel.State: A determinizated root state consistent with the given
            state's information state, either newly resampled or cloned from cache.
        """
        if self._max_world_samples == UNLIMITED_NUM_WORLD_SAMPLES:
            return self.resample_from_infostate(state)
        elif len(self._root_samples) < self._max_world_samples:
            self._root_samples.append(self.resample_from_infostate(state))
            return self._root_samples[-1].clone()
        elif len(self._root_samples) == self._max_world_samples:
            idx = self._random_state.randint(len(self._root_samples))
            return self._root_samples[idx].clone()
        else:
            raise pyspiel.SpielError(
            'Case not handled (badly set max_world_samples..?)')


    def create_new_node(self, state: pyspiel.State) -> ISMCTSNode: # TODO state
        """Create and register a new search node for the given information state.

        This method allocates a fresh ISMCTSNode, initializes its visit count,
        and stores it in the node mapping keyed by the state's information key.

        Args:
            state (pyspiel.State): The game state for which to create a node.

        Returns:
            ISMCTSNode: The newly created node associated with the given state.
        """
        infostate_key = self.get_state_key(state)
        self._node_pool.append(ISMCTSNode())
        node = self._node_pool[-1]
        self._nodes[infostate_key] = node
        node.total_visits = UNEXPANDED_VISIT_COUNT
        return node


    def set_resampler(self, cb) -> None: # TODO What is _resampler_cb?
        """Register a custom resampling callback for information-state sampling.

        This callback is used to generate determinizations from a given state
        and current player instead of relying on the default game resampling.

        Args:
            cb: A callable taking a state and player index and returning a
                resampled pyspiel.State from the corresponding information state.
        """
        self._resampler_cb = cb


    def lookup_node(self, state: pyspiel.State) -> ISMCTSNode | None: # TODO pyspiel.State
        """Retrieve the search node corresponding to the given game state if it exists.

        This method looks up the internal node mapping using the state's
        information key and returns the associated ISMCTS node, or None if no node has been created.

        Args:
            state (pyspiel.State): The game state whose associated node is being requested.

        Returns:
            ISMCTSNode | None: The node associated with the state's information key,
            or None if the state has not yet been added to the search tree.
        """
        if self.get_state_key(state) in self._nodes:
            return self._nodes[self.get_state_key(state)]
        return None


    def lookup_or_create_node(self, state: pyspiel.State) -> ISMCTSNode: # TODO pyspiel.State
        """Return the existing node for the state or create a new one if needed.

        This method looks up the node associated with the given state and, if no
        node is found, creates and registers a new search node for that state.

        Args:
            state (pyspiel.State): The game state whose search node is requested.

        Returns:
            ISMCTSNode: The existing or newly created node corresponding to the state.
        """
        node = self.lookup_node(state)
        return node or self.create_new_node(state)


    def filter_illegals(self, node: ISMCTSNode, legal_actions: list[int]) -> ISMCTSNode:
        """Create a filtered copy of a node containing only legal child actions.

        This method removes any child entries whose actions are not present in
        the provided legal action set and adjusts the visit count accordingly.

        Args:
            node (ISMCTSNode): The original node to filter.
            legal_actions (list[int]): The list of actions that are legal in the current state.

        Returns:
            ISMCTSNode: A new node instance that includes only legal actions and updated visit counts.
        """
        new_node = copy.deepcopy(node)
        for action, child in node.child_info.items():
            if action not in legal_actions:
                new_node.total_visits -= child.visits
                del new_node.child_info[action]
        return new_node


    def repopulate_prior_map_inconsistent_action_sets(self, state: pyspiel.State, node: ISMCTSNode) -> None: # TODO
        """Rebuild and normalize a node's prior map when legal action sets differ.

        This method updates the node's prior probabilities to include priors for
        newly legal actions and renormalizes all priors to form a valid distribution.

        Args:
            state (pyspiel.State): The game state providing the current action priors.
            node (ISMCTSNode): The node whose prior map will be updated and normalized.
        """
        new_prior_map = node.prior_map.copy()
        for action, prob in self._evaluator.prior(state):
            if action not in new_prior_map:
                new_prior_map[action] = prob
        # now, normalize
        sum_probs = sum(new_prior_map.values())
        for action, prob in new_prior_map.items():
            new_prior_map[action] = prob / sum_probs
        node.prior_map = new_prior_map


    def expand_if_necessary(self, state: pyspiel.State, node: ISMCTSNode, action: int) -> None: # TODO pyspiel.State
        """Ensure that a child entry exists for the given action at the node.

        This method adds a new child for the action if it is missing, optionally
        updating the node's prior map first when legal action sets are inconsistent.

        Args:
            state (pyspiel.State): The current game state used to refresh priors if needed.
            node (ISMCTSNode): The search node at which the child action may be expanded.
            action (int): The action identifier that should be present in the node's children.
        """
        if action not in node.child_info:
            if self._allow_inconsistent_action_sets and action not in node.prior_map:
                # This can happen if the prior map was populated from a state that had
                # a different legal action set than the current state.
                self.repopulate_prior_map_inconsistent_action_sets(state, node)
            node.child_info[action] = ChildInfo(0.0, 0.0, node.prior_map[action])


    def _action_value(self, node: ISMCTSNode, child: ChildInfo) -> float:
        """Compute the selection value of a child according to the configured policy.

        This method combines the child's mean return with an exploration bonus
        derived from either the UCT or PUCT formula to score the action.

        Args:
            node (ISMCTSNode): The parent node providing aggregate visit statistics.
            child (ChildInfo): The child entry containing per-action statistics and priors.

        Raises:
            pyspiel.SpielError: If the configured child selection policy is unrecognized.

        Returns:
            float: The computed selection value for the child action.
        """
        assert child.visits > 0
        action_value = child.value()
        if self._child_selection_policy == ChildSelectionPolicy.UCT:
            action_value += self._uct_c * np.sqrt(
                np.log(node.total_visits) / child.visits
            )
        elif self._child_selection_policy == ChildSelectionPolicy.PUCT:
            action_value += (
                self._uct_c
                * child.prior
                * np.sqrt(node.total_visits)
                / (1 + child.visits)
            )
        else:
            raise pyspiel.SpielError('Child selection policy unrecognized.')
        return action_value


    def _select_candidate_actions(self, node: ISMCTSNode) -> list[int]:
        """Identify the set of child actions that are effectively tied for best.

        This method scores each child using the configured selection policy and
        returns all actions whose score lies within a small tolerance of the maximum.

        Args:
            node (ISMCTSNode): The node whose child actions are being evaluated.

        Returns:
            list[int]: A list of action identifiers that form the candidate set.
        """
        max_action_value = max(
            self._action_value(node, child) for child in node.child_info.values()
        )

        candidates: list[int] = [
            action
            for action, child in node.child_info.items()
            if self._action_value(node, child) > max_action_value - TIE_TOLERANCE
        ]
        return candidates


    def select_action(self, node: ISMCTSNode) -> int:
        """Sample an action from the candidate set produced by the tree policy.

        This method selects one of the best-scoring child actions according to
        the configured child selection policy, breaking ties uniformly at random.

        Args:
            node (ISMCTSNode): The node whose child actions are being considered.

        Returns:
            int: The chosen action identifier from the candidate action set.
        """
        candidates = self._select_candidate_actions(node)
        assert len(candidates) >= 1
        return candidates[self._random_state.randint(len(candidates))]
    

    def select_action_tree_policy(self, state: pyspiel.State, node:ISMCTSNode, legal_actions: list[int]) -> int:
        """Select an action from the tree using the configured child selection policy.

        This method chooses between random expansion and value-based selection
        while optionally handling inconsistent legal action sets by filtering the node.

        Args:
            state (pyspiel.State): The current game state from which the selection is made.
            node (ISMCTSNode): The ISMCTS node representing the current information set.
            legal_actions (list[int]): The list of legal actions available in the current state.

        Returns:
            int: The chosen action as an integer action identifier.
        """
        if not self._allow_inconsistent_action_sets:
            return self.select_action(node)

        temp_node = self.filter_illegals(node, legal_actions)
        if temp_node.total_visits != 0:
            return self.select_action(temp_node)       

        action = legal_actions[self._random_state.randint(
            len(legal_actions))]  # prior? (not my comment)
        self.expand_if_necessary(state, node, action)
        return action


    def check_expand(self, node: ISMCTSNode, legal_actions: list[int]) -> int:
        """Determine whether a new child should be expanded at the given node.

        This method selects an unexpanded legal action for expansion or signals
        that no further expansion is needed when all legal actions are already children.

        Args:
            node (ISMCTSNode): The search node whose children may be expanded.
            legal_actions (list[int]): The list of actions that are legal in the current state.

        Returns:
            int: The identifier of an unexpanded legal action to add as a child,
            or pyspiel.INVALID_ACTION (-1) if no expansion should occur.
        """
        if not self._allow_inconsistent_action_sets and len(
        node.child_info) == len(legal_actions):
            return pyspiel.INVALID_ACTION
        legal_actions_copy = copy.deepcopy(legal_actions)
        self._random_state.shuffle(legal_actions_copy)
        return next(
            (
                action
                for action in legal_actions_copy
                if action not in node.child_info
            ),
            pyspiel.INVALID_ACTION,
        )


    def run_simulation(self, state: pyspiel.State):
        if state.is_terminal():
            return state.returns()
        elif state.is_chance_node():
            action_list, prob_list = zip(*state.chance_outcomes())
            chance_action = self._random_state.choice(action_list, p=prob_list)
            state.apply_action(chance_action)
            return self.run_simulation(state)
        legal_actions = state.legal_actions()
        cur_player = state.current_player()
        node = self.lookup_or_create_node(state)

        assert node

        if node.total_visits == UNEXPANDED_VISIT_COUNT:
            node.total_visits = 0
            for action, prob in self._evaluator.prior(state):
                node.prior_map[action] = prob
            return self._evaluator.evaluate(state)
        else:
            chosen_action = self.check_expand(
            node, legal_actions)  # add one children at a time?
            if chosen_action != pyspiel.INVALID_ACTION:
                # check if all actions have been expanded, if not, select one?
                # if yes, ucb?
                self.expand_if_necessary(state, node, chosen_action)
            else:
                chosen_action = self.select_action_tree_policy(state, node,
                                                               legal_actions)

            assert chosen_action != pyspiel.INVALID_ACTION

            node.total_visits += 1
            node.child_info[chosen_action].visits += 1
            state.apply_action(chosen_action)
            returns = self.run_simulation(state)
            node.child_info[chosen_action].return_sum += returns[cur_player]
            return returns


    def run_search(self, state: pyspiel.State) -> list[tuple[int, float]]: # TODO
        """Run multiple IS-MCTS simulations from the given state and derive an action policy.

        This method repeatedly samples root determinizations, calls
        `run_simulation` to update tree statistics, and uses only those updated
        statistics (not the raw return vectors) to construct a final action policy.

        Args:
            state (pyspiel.State): The imperfect-information game state for which
                an IS-MCTS-based action policy is computed.

        Returns:
            list[tuple[int, float]]: A list of (action, probability) pairs
            representing the final policy derived from the root node statistics.
        """
        self.reset()
        assert state.get_game().get_type(
        ).dynamics == pyspiel.GameType.Dynamics.SEQUENTIAL
        assert state.get_game().get_type(
        ).information == pyspiel.GameType.Information.IMPERFECT_INFORMATION

        legal_actions = state.legal_actions()
        if len(legal_actions) == 1:
            return [(legal_actions[0], 1.0)]

        self._root_node = self.create_new_node(state)

        assert self._root_node

        root_infostate_key = self.get_state_key(state)

        for _ in range(self._max_simulations):
            # how to sample a pyspiel.state from another pyspiel.state?
            sampled_root_state = self.sample_root_state(state)
            assert root_infostate_key == self.get_state_key(sampled_root_state)
            assert sampled_root_state
            self.run_simulation(sampled_root_state)

        if self._allow_inconsistent_action_sets:  # when this happens?
            legal_actions = state.legal_actions()
            temp_node = self.filter_illegals(self._root_node, legal_actions)
            assert temp_node.total_visits > 0
            return self.get_final_policy(state, temp_node)
        else:
            return self.get_final_policy(state, self._root_node)
        

    def step(self, state:pyspiel.State) -> Any:
        """Recursively simulate play from the given state and return per-player payoffs.

        This method advances the game through terminal, chance, and decision
        states, updating tree statistics along the way and finally returning
        the resulting payoff vector for all players.

        Args:
            state (pyspiel.State): The current game state from which the simulation is executed.

        Returns:
            list[float]: A list of numeric payoffs corresponding to each player
            at the end of the simulated game trajectory.
        """
        if state.is_chance_node():
            logging.info('State is a chance node, returning invalid action policy.')
            return pyspiel.INVALID_ACTION
        action_list, prob_list = zip(*self.run_search(state))
        return self._random_state.choice(action_list, p=prob_list)


    def get_policy(self, state: pyspiel.State) -> list[tuple[int, float]]:
        """Compute an action probability policy for the given game state.

        This method returns a trivial invalid-action policy when the state is a
        chance node, and otherwise delegates to `run_search` to construct an
        IS-MCTS-based policy over the current player's legal actions.

        Args:
            state (pyspiel.State): The current game state for which an action
                policy is requested.

        Returns:
            list[tuple[int, float]]: A list of (action, probability) pairs
            representing the policy for the current player, or a single invalid
            action with probability 1.0 if the state is a chance node.
        """
        if state.is_chance_node():
            logging.info('State is a chance node, returning invalid action policy.')
            return [(pyspiel.INVALID_ACTION, 1.0)]
        return self.run_search(state)


    def step_with_policy(self, state: pyspiel.State) -> tuple[list[tuple[int, float]], Any]:
        """Compute a policy for the given state and sample an action from it.

        This method first obtains an action-probability policy for the current
        player and then draws a single action according to that distribution.

        Args:
            state (pyspiel.State): The current game state for which a policy and
                sampled action are requested.

        Returns:
            tuple[list[tuple[int, float]], Any]: A tuple containing the list of
            (action, probability) pairs that form the policy and the single
            sampled action drawn from that policy.
        """
        policy = self.get_policy(state)
        action_list, prob_list = zip(*policy)
        sampled_action = self._random_state.choice(action_list, p=prob_list)
        return policy, sampled_action