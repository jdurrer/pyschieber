"""Nudge at the end of a Copilot session when compound notes may be missing.

Intended to run as a Copilot Stop hook from `.github/hooks/index_hooks.json`.
Silently does nothing on its first run, so existing history is not reported.

"Changed since last check" is approximated by file modification time against
a small persisted timestamp, not a real diff. This
is a heuristic nudge, not an enforced gate: it never blocks, and a
change to this state file itself is not itself compound-worthy.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

WATCHED_DIRS = ("docs", "pyschieber", "tests")
COMPOUND_DIR = "knowledge"
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
IGNORED_FILENAMES = {"INDEX.md"}
IGNORED_SUFFIXES = {".pyc"}
MAX_LISTED_FILES = 20

STATE_PATH = Path(".github/hooks/.last_compound_check")


def _is_tracked(path: Path) -> bool:
    """Whether `path` counts as a real source file for this check.

    Args:
        path: A file path found under one of the watched directories.

    Returns:
        False for cache directories and known non-source suffixes
        (e.g. `.pyc`), True otherwise.
    """
    if any(part in IGNORED_DIR_NAMES for part in path.parts):
        return False
    return path.name not in IGNORED_FILENAMES and path.suffix not in IGNORED_SUFFIXES


def _latest_mtime(root: Path) -> float | None:
    """Latest modification time among tracked files under `root`.

    Args:
        root: Directory to scan.

    Returns:
        The newest modification time, or `None` if `root` doesn't exist
        or has no tracked files.
    """
    if not root.is_dir():
        return None
    mtimes = [
        path.stat().st_mtime
        for path in root.rglob("*")
        if path.is_file() and _is_tracked(path)
    ]
    return max(mtimes, default=None)


def _changed_files(root: Path, since: float, *, relative_to: Path) -> list[str]:
    """Tracked files under `root` modified after `since`.

    Args:
        root: Directory to scan.
        since: Epoch timestamp to compare against.
        relative_to: Base directory the returned paths are made relative to.

    Returns:
        POSIX-style paths (relative to `relative_to`), sorted, of files
        modified after `since`.
    """
    if not root.is_dir():
        return []
    return sorted(
        path.relative_to(relative_to).as_posix()
        for path in root.rglob("*")
        if path.is_file() and _is_tracked(path) and path.stat().st_mtime > since
    )


def build_report(changed_code: list[str]) -> str:
    """Format the Stop-hook reminder for code changes with no matching knowledge/ update.

    Args:
        changed_code: Paths (relative to cwd) that changed since the last check.

    Returns:
        A human-readable multi-line reminder, capped at `MAX_LISTED_FILES` paths.
    """
    lines = [
        (
            "Compound-step reminder: these files changed since the last check, "
            "but nothing under knowledge/ was added or updated to match:"
        ),
    ]
    lines.extend(f"  - {path}" for path in changed_code[:MAX_LISTED_FILES])
    if len(changed_code) > MAX_LISTED_FILES:
        lines.append(f"  ... and {len(changed_code) - MAX_LISTED_FILES} more")
    lines.append(
        "If this was non-trivial work, add a knowledge/decisions/, "
        "knowledge/status/, knowledge/tasks/, or knowledge/measurements/ entry "
        "(skip this for trivial/one-line changes)."
    )
    return "\n".join(lines)


def main() -> None:
    """Compare src/tests/templates vs knowledge/ modification times since the last check."""
    cwd = Path.cwd()
    watched_roots = [cwd / name for name in WATCHED_DIRS]
    if not any(root.is_dir() for root in watched_roots):
        return

    state_path = cwd / STATE_PATH
    now = time.time()

    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(str(now), encoding="utf-8")
        return  # first run: nothing to compare against yet, avoid flagging all history

    try:
        since = float(state_path.read_text(encoding="utf-8").strip())
    except ValueError:
        since = now
    state_path.write_text(str(now), encoding="utf-8")

    changed_code: list[str] = []
    for root in watched_roots:
        changed_code.extend(_changed_files(root, since, relative_to=cwd))
    if not changed_code:
        return

    knowledge_latest = _latest_mtime(cwd / COMPOUND_DIR)
    if knowledge_latest is not None and knowledge_latest > since:
        return  # knowledge/ was also touched since the last check

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": build_report(changed_code),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
