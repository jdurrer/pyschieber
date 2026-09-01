"""Actively reconcile the repository's spoke INDEX.md files against disk.

Intended to run as a Copilot SessionStart hook from
`.github/hooks/index_hooks.json`.

`check_knowledge_index.py` can auto-write correct rows because frontmatter
gives it a reliable `type`/`status`/`description` to copy. The areas this
hook covers have no such structured source for most of their files, but
*some* of what they track is reliably derivable without inventing anything:
a Python module's own docstring, most notably. Those fields are re-derived
and overwritten on every run, exactly like frontmatter is for the knowledge
index — so the index can never drift from its source. Anything with no
reliable source (what a raw, non-Python file actually is) is written once,
as a clearly-marked placeholder, when its row is first added, and never
touched again — a real description, once written over that placeholder, is
never silently overwritten. Rows for deleted files are always removed; rows
for new files are always added. Only rows still showing the placeholder are
reported (non-blocking `additionalContext`) — everything else is a silent
auto-fix, matching `check_knowledge_index.py`'s own behavior of only
speaking up about what it can't resolve on its own.

Areas nest (e.g. `src/INDEX.md` and `src/utils/INDEX.md`): each area's
INDEX.md is only responsible for files directly inside it, plus anything in
a subdirectory that does *not* have its own `INDEX.md` — recursion stops at
any subdirectory that owns its own nested index, so a file is never expected
in two places at once.

This is the standard for any future spoke, too: give it an `AreaConfig` that
auto-derives whatever it reliably can, and falls back to the write-once
placeholder for anything it can't — not a report-only stub.
"""

from __future__ import annotations

import ast
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

INDEX_FILENAME = "INDEX.md"
# Instruction files and generated or environment directories are not
# repository content and should never appear in an index.
IGNORED_FILENAMES = {INDEX_FILENAME, "CLAUDE.md"}
IGNORED_DIR_NAMES = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    ".venv-build",
    "build",
    "dist",
    "venv",
}
PLACEHOLDER_DESCRIPTION = "_(needs a description)_"
PATH_COLUMN = "File Path"

# `Callable[...]` is spelled out inline at each usage below rather than
# bound to a module-level type-alias name: as a plain top-level assignment
# it would be evaluated immediately (and `collections.abc.Callable` isn't
# subscriptable before Python 3.9), but inside an annotation it stays an
# unevaluated string, thanks to `from __future__ import annotations`.


@dataclass(frozen=True)
class AreaConfig:
    """One spoke's reconciliation rules."""

    columns: tuple[str, ...]
    build_row: Callable[[str, Path, dict[str, str] | None], dict[str, str]]


def find_owned_files(area_dir: Path) -> set[str]:
    """List files `area_dir`'s own `INDEX.md` is responsible for.

    Recurses into subdirectories, but stops at (and excludes the contents
    of) any subdirectory that has its own `INDEX.md` — that subdirectory
    owns its own listing from that point down, so its files aren't also
    expected in the parent's index. Also skips `__pycache__` directories
    and files in `IGNORED_FILENAMES`.

    Args:
        area_dir: The area's directory.

    Returns:
        POSIX-style paths relative to `area_dir`.
    """
    owned: set[str] = set()

    def _walk(current_dir: Path) -> None:
        for entry in current_dir.iterdir():
            if entry.is_dir():
                if entry.name in IGNORED_DIR_NAMES or entry.name.endswith(".egg-info"):
                    continue
                if (entry / INDEX_FILENAME).exists():
                    continue  # owned by its own nested index instead
                _walk(entry)
            elif entry.is_file() and entry.name not in IGNORED_FILENAMES:
                owned.add(entry.relative_to(area_dir).as_posix())

    _walk(area_dir)
    return owned


def parse_index_table(
    index_path: Path, columns: tuple[str, ...]
) -> dict[str, dict[str, str]]:
    """Parse an area `INDEX.md`'s data rows, keyed by path.

    Args:
        index_path: Path to the area's `INDEX.md`.
        columns: The table's expected column headers, in order — the first
            is always the path column.

    Returns:
        `{path: {column: value}}` for every data row. Empty if the file
        doesn't exist or its table doesn't match the expected column count.
    """
    if not index_path.exists():
        return {}

    rows: dict[str, dict[str, str]] = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != len(columns):
            continue

        path = cells[0].strip("`")
        if not path or path.lower() == columns[0].lower():
            continue
        if set(path) <= {"-"}:  # header separator row, e.g. |---|---|
            continue

        rows[path] = dict(zip(columns, [path, *cells[1:]]))
    return rows


def build_table_block(columns: tuple[str, ...], rows: dict[str, dict[str, str]]) -> str:
    """Render an area's table: header, separator, and one row per path, sorted.

    Args:
        columns: The table's column headers, in order.
        rows: `{path: {column: value}}`, as returned by `parse_index_table`
            or built fresh by reconciliation.

    Returns:
        The table as markdown lines, joined with newlines (no trailing
        newline).
    """
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for path in sorted(rows):
        row = rows[path]
        cells = [
            f"`{path}`" if col == PATH_COLUMN else row.get(col, "") for col in columns
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def rewrite_index_table(
    index_path: Path, columns: tuple[str, ...], rows: dict[str, dict[str, str]]
) -> None:
    """Replace an area `INDEX.md`'s table in place, preserving surrounding text.

    Args:
        index_path: Path to the area's `INDEX.md`.
        columns: The table's column headers, in order.
        rows: The full, already-reconciled set of rows the table should
            contain.

    Raises:
        ValueError: If the expected table header can't be found, so a
            malformed rewrite never silently corrupts the file.
    """
    text = index_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header_line = "| " + " | ".join(columns) + " |"

    try:
        header_idx = lines.index(header_line)
    except ValueError as exc:
        raise ValueError(
            f"Could not locate the expected table header in {index_path}: {header_line!r}"
        ) from exc

    table_end = header_idx + 2  # skip the header and its separator line
    while table_end < len(lines) and lines[table_end].strip().startswith("|"):
        table_end += 1

    new_lines = [
        *lines[:header_idx],
        *build_table_block(columns, rows).splitlines(),
        *lines[table_end:],
    ]
    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    index_path.write_text(new_text, encoding="utf-8")


def _preserve_or_default(
    previous: dict[str, str] | None, key: str, default: str
) -> str:
    """Keep an existing, already-replaced value; otherwise use `default`.

    Args:
        previous: The row's previous value (from `parse_index_table`), or
            `None` if this is a brand-new row.
        key: Which column to look at.
        default: Value to use when there's no previous row, or its value
            is still the unreplaced placeholder.

    Returns:
        The value this column should have.
    """
    if previous is not None:
        existing = previous.get(key)
        if existing and existing != PLACEHOLDER_DESCRIPTION:
            return existing
    return default


def _describe_python_module(full_path: Path) -> str:
    """Derive a one-line description from a Python module's own docstring.

    Args:
        full_path: Path to the `.py` file.

    Returns:
        The docstring's first line, or a fixed fallback if the file has no
        module docstring or can't be parsed.
    """
    try:
        tree = ast.parse(full_path.read_text(encoding="utf-8"))
        docstring = ast.get_docstring(tree)
    except (SyntaxError, UnicodeDecodeError, OSError):
        docstring = None

    if not docstring:
        return "No module docstring."
    return docstring.strip().splitlines()[0].strip()


def _python_row(
    rel_path: str, full_path: Path, _previous: dict[str, str] | None
) -> dict[str, str]:
    """Row builder for code-directory spokes: description always re-derived from the docstring."""
    return {PATH_COLUMN: rel_path, "Description": _describe_python_module(full_path)}


def _mixed_code_row(
    rel_path: str, full_path: Path, previous: dict[str, str] | None
) -> dict[str, str]:
    """Build a row for a code spoke containing Python and other files."""
    if full_path.suffix == ".py":
        return _python_row(rel_path, full_path, previous)
    return _docs_row(rel_path, full_path, previous)


def _docs_row(
    rel_path: str, full_path: Path, previous: dict[str, str] | None
) -> dict[str, str]:
    """Row builder for `docs/`: no reliable content source, but 0-byte files get a truthful default."""
    default = (
        "Placeholder (empty)."
        if full_path.stat().st_size == 0
        else PLACEHOLDER_DESCRIPTION
    )
    return {
        PATH_COLUMN: rel_path,
        "Description": _preserve_or_default(previous, "Description", default),
    }


def build_area_configs(workspace_root: Path) -> dict[str, AreaConfig]:
    """Build the reconciliation config for every spoke this hook covers.

    Args:
        workspace_root: The workspace root. Unused for now — kept so a
            future area config that needs to look elsewhere in the
            workspace (as `results/`/`task_description/` once did) doesn't
            require changing this function's signature.

    Returns:
        `{area directory name: AreaConfig}`.
    """
    del workspace_root
    python_columns = (PATH_COLUMN, "Description")

    return {
        "docs": AreaConfig(columns=python_columns, build_row=_docs_row),
        "pyschieber": AreaConfig(columns=python_columns, build_row=_mixed_code_row),
        "tests": AreaConfig(columns=python_columns, build_row=_mixed_code_row),
    }


def reconcile_area(area_dir: Path, area_name: str, config: AreaConfig) -> list[str]:
    """Reconcile one area's `INDEX.md` against disk, rewriting it if anything changed.

    Args:
        area_dir: The area's directory.
        area_name: The area's directory name, used to prefix reported paths.
        config: The area's reconciliation rules.

    Returns:
        Workspace-relative paths whose row still shows the unreplaced
        placeholder description, needing a human/AI to write a real one.
    """
    owned = find_owned_files(area_dir)
    index_path = area_dir / INDEX_FILENAME
    existing_rows = parse_index_table(index_path, config.columns)

    new_rows = {
        rel_path: config.build_row(
            rel_path, area_dir / rel_path, existing_rows.get(rel_path)
        )
        for rel_path in owned
    }

    if new_rows != existing_rows:
        rewrite_index_table(index_path, config.columns, new_rows)

    return sorted(
        f"{area_name}/{rel_path}"
        for rel_path, row in new_rows.items()
        if row.get("Description") == PLACEHOLDER_DESCRIPTION
    )


def build_report(needs_description: list[str]) -> str:
    """Format the residual "needs a real description" list as `additionalContext`.

    Args:
        needs_description: Workspace-relative paths still showing the
            placeholder description.

    Returns:
        A human-readable multi-line report, or `""` if the list is empty.
    """
    if not needs_description:
        return ""

    lines = ["Spoke INDEX.md rows were auto-added but still need a real description:"]
    lines.extend(f"  - {path}" for path in needs_description)
    lines.append(
        f'Replace the "{PLACEHOLDER_DESCRIPTION}" placeholder with real text once you '
        "know what the file is — everything else in these rows is kept in sync automatically."
    )
    return "\n".join(lines)


def main() -> None:
    """Reconcile every configured spoke INDEX.md against disk and report residual gaps."""
    workspace_root = Path.cwd()
    configs = build_area_configs(workspace_root)

    needs_description: list[str] = []
    for area_name, config in configs.items():
        area_dir = workspace_root / area_name
        if not area_dir.is_dir():
            continue
        needs_description.extend(reconcile_area(area_dir, area_name, config))

    if report := build_report(sorted(needs_description)):
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": report,
                    }
                }
            )
        )


if __name__ == "__main__":
    main()
