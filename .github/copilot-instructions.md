# PySchieber Copilot Instructions

## General Principles

- Prioritize correctness, readability, and maintainability.
- Prefer simple, explicit solutions over clever abstractions.
- Understand the existing implementation and align with its patterns before adding functionality.
- Make the smallest reasonable change that satisfies the requirements.
- Do not introduce unnecessary dependencies.

## Scope and Priorities

- This repository supports Python `>=3.12`; use modern syntax and standard-library APIs compatible with that version.
- Preserve the existing `pyschieber/` package layout and public APIs unless the task explicitly requests a breaking change.
- Before changing code, inspect the owning implementation and nearby tests. Keep changes focused and avoid unrelated refactors or new dependencies.
- Prefer simple, explicit code and standard-library solutions.

## Python Conventions

- Add complete type annotations to new and modified functions, methods, and public attributes. Avoid `Any` unless there is no practical alternative.
- Add or update concise docstrings for modules, classes, functions, and methods. Describe intent, parameters, return values, and important exceptions when applicable.
- Keep docstrings synchronized with the implementation. Use `typing.Self` where it improves recursive or fluent type annotations.
- Keep business logic separate from I/O, keep functions focused, and avoid hidden side effects.
- Fail fast when an invalid state cannot be recovered from. Raise specific exceptions with actionable messages and never silently swallow exceptions.
- Use the `logging` module for application diagnostics; use `print` only for intentional CLI output.
- Include useful context in log messages and use structured fields, such as `extra`, when that improves diagnostics.
- Prefer concrete classes first. Use `Protocol` for capability-based boundaries and test doubles; use an ABC only when shared implementation or hierarchy invariants justify it. Prefer composition over deep inheritance.
- Use dataclasses for structured state when they improve clarity. Use `slots=True` or `frozen=True` when appropriate for the object's required mutation.

## Formatting, Linting, and Types

- Treat `pyproject.toml` as the source of truth for Ruff, pytest, and mypy configuration.
- Run `ruff format .` and `ruff check .` for Python changes. Do not hand-format against a different style.
- Run mypy when changing typed interfaces or type-heavy code.
- Remove unused imports and dead code introduced by the change.

## Testing

- Add or update focused pytest tests for behavior changes, including relevant failure cases.
- Test public behavior rather than implementation details. Prefer small fakes over mocks when a boundary needs a test double.
- Testmon is required: use it to skip tests already proven unaffected by the current changes. Run `pytest` with the repository's configured testmon options.
- Run a focused command such as `pytest tests/test_game.py` while iterating, then run the full testmon-backed suite before completing the task.

## Performance

- Optimize only after correctness is established; avoid premature optimization.
- For large datasets or search spaces, consider iterators, generators, and algorithmic complexity before micro-optimizations.

## Completion Checklist

- [ ] Type annotations are complete for new and modified interfaces.
- [ ] Docstrings are present and synchronized for modules, classes, functions, and methods touched by the change.
- [ ] Ruff formatting and linting pass.
- [ ] Imports and dead code introduced by the change are removed.
- [ ] Relevant happy-path and failure-case tests are present.
- [ ] Exceptions and logging follow the project conventions.
- [ ] The solution remains focused and simple.

## Workflow

- For a small change, implement and run the narrowest useful validation immediately.
- For an ambiguous, multi-file, or architectural change, state assumptions and a short plan before editing.
- After editing, report the files changed and the validation commands run. Mention unrelated pre-existing failures separately.
- Update `README.md` or relevant `docs/` files when user-facing behavior or setup changes.

## Brainstorm, Plan, Work, Compound

- Scale this loop to the task; a one-line fix does not need a formal plan or knowledge entry.
- **Brainstorm:** For ambiguous or non-trivial requests, surface assumptions, open questions, and viable options before committing to an approach.
- **Plan:** For multi-file or architectural changes, state a short implementation and validation plan before editing. Revise it when new evidence changes the approach.
- **Work:** Implement only the agreed scope, following the existing ownership boundaries and patterns.
- **Compound:** After non-trivial work, add a concise entry under `knowledge/decisions/`, `knowledge/status/`, `knowledge/tasks/`, or `knowledge/measurements/` explaining what changed, why, and what remains. Keep `knowledge/INDEX.md` synchronized.
- The `.github/hooks/check_compound_step.py` Stop hook is a reminder, not a substitute for judgment; skip compound documentation for genuinely trivial changes.

## Hub-and-Spoke Indexes

- Use the root `INDEX.md` as the repository hub and keep it linked to the `docs/`, `pyschieber/`, and `tests/` spoke indexes.
- Keep each spoke index focused on its own directory. Do not duplicate files that belong to a nested spoke.
- Run `.github/hooks/check_area_indexes.py` after adding, removing, or moving files so spoke rows stay synchronized.
- Write meaningful descriptions for new non-Python files when the reconciler marks them with `_(needs a description)_`.
