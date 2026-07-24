# Project TODO: Card Game Agent Implementation

---

## 1. Information Gathering

| Task | Resource |
|------|----------|
| Read opponent hand strategies | [AI Factory Newsletter](https://www.aifactory.co.uk/newsletter/2018_02_opponent_hand.htm) |
| Reference ISMCTS implementation | [Google DeepMind OpenSpiel](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/python/algorithms/ismcts.py) |

---

## 2. Core Design: Multiple-Observer ISMCTS

**Overview:** The agent actively uses Information Set Monte Carlo Tree Search (ISMCTS) to predict opponent behavior while accounting for the hidden information available to those opponents themselves.

### Implementation Guidelines

| Agent Type | Strategy Implementation |
|------------|------------------------|
| **Bot & Partner** | Implement full strategy |
| **Opponents** | Only implement definitely known information from game state (opponents may have unknown strategies) |

**Expected Outcome:** This approach should reduce rule-based card selection and increase the frequency of multiple node selections.

---

## 3. Completed Tasks

### Docstring Rewrites for Moved Code

| Mode | Status |
|------|--------|
| `uncolored_trumpf` | ✅ Done |
| `top_down_mode` | ✅ Done |
| `bottom_up_mode` | ✅ Done |
| `trumpf_color_mode` | ✅ Done |

### Initial Coding Work

| Task | Status |
|------|--------|
| Typehint `ismcts.py` | ✅ Done |

---

## 4. Pending Development: PySpiel Game State with Four Agents

**Reference:** Use [`alphabeta/treesearch.py`] as inspiration.

### 4.1 `pyspiel.Bot`
- 📌 **Status:** Not started

### 4.2 `pyspiel.State` Methods

| Method | Documentation | Status | Notes |
|--------|---------------|--------|-------|
| `clone()` | [State API](https://openspiel.readthedocs.io/en/latest/api_reference.html#state-methods) | 🔲 TBD | Returns deep copy independent of original |
| `current_player()` | Same as bot ID | 🔲 TBD | Returns player ID of acting player |
| `observation_string()` | [State API](https://openspiel.readthedocs.io/en/latest/api_reference.html#state-methods) | 🔲 TBD | Unclear specifics |
| `legal_actions()` | [Legal Actions](https://openspiel.readthedocs.io/en/latest/api_reference/state_legal_actions.html) | 🔲 TBD | - |
| `resample_from_infostate()` | [Resample API](https://openspiel.readthedocs.io/en/latest/api_reference/state_resample_from_infostate.html) | 🔲 TBD | - |
| `is_terminal()` | Standard check | ✅ Understood | Returns True if game ended |
| `returns()` | [Returns API](https://openspiel.readthedocs.io/en/latest/api_reference/state_returns.html) | 🔲 TBD | Cumulated reward per player |
| `is_chance_node()` | [Chance Node API](https://openspiel.readthedocs.io/en/latest/api_reference/state_is_chance_node.html) | 🔲 TBD | - |
| `chance_outcomes()` | [Chance Outcomes](https://openspiel.readthedocs.io/en/latest/api_reference/state_chance_outcomes.html) | 🔲 TBD | List of (action, probability) tuples |
| `apply_action(action: int)` | Plays a card | 🔲 TBD | - |
| `get_game()` | [Get Game API](https://openspiel.readthedocs.io/en/latest/api_reference/state_get_game.html) | 🔲 TBD | Relevance unclear - single game context |

### 4.3 Additional Components to Investigate

- ❓ `pyspiel.Game` — Check if required (no calls found in existing code)
- 🔲 `pyspiel.UniformProbabilitySampler`
- 🔲 `pyspiel.SpielError`
- 🔲 `pyspiel.INVALID_ACTION` — Expected to return `-1`
- 🔲 `pyspiel.GameType.Dynamics.SEQUENTIAL`
- 🔲 `pyspiel.GameType.Dynamics.IMPERFECT_INFORMATION`

---

## 5. Testing Pipeline

- 🔲 Write tests
- 🔲 Run tests

---

## 6. Integration

- 📌 **Play Best Found Move** — Not started

---

## Summary Statistics

| Category | Total | Completed | In Progress | Pending |
|----------|-------|-----------|-------------|---------|
| Modes (docstrings) | 4 | 4 | 0 | 0 |
| PySpiel State Methods | 11 | 1 | 0 | 10 |
| Major Milestones | 4 | 1 | 1 | 2 |

---

*Last updated: Manual review of `PROJECT_TODO.md`*