"""Reconcile knowledge/INDEX.md against knowledge files.

Intended to run as a Copilot SessionStart hook from
`.github/hooks/index_hooks.json`. Silently does nothing if the current
working directory has no knowledge/ folder.

Files carrying complete frontmatter (`type`, `status`, `description`) are
reconciled automatically: added, updated, or removed from INDEX.md's table
with no review step. Files with missing or incomplete frontmatter can't be
auto-filled, so they're reported as additionalContext for manual follow-up.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

IGNORED_FILENAMES = {"INDEX.md", "README.md", "CLAUDE.md", "TEMPLATE.md", ".gitkeep"}
REQUIRED_FRONTMATTER_KEYS = ("type", "status", "description")

FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---\r?\n", re.DOTALL)

TABLE_HEADER = "| File Path | Type | Status | Description |"
TABLE_SEPARATOR = "|---|---|---|---|"
EMPTY_TABLE_NOTE = "_No files yet — rows are added as knowledge files are created._"
TABLE_BLOCK_RE = re.compile(
    re.escape(TABLE_HEADER)
    + r"\n"
    + re.escape(TABLE_SEPARATOR)
    + r"\n(?:.*\n?)*?(?=\n## |\Z)",
)


@dataclass(frozen=True)
class IndexRow:
    """One data row of the knowledge/INDEX.md table."""

    path: str
    type: str
    status: str
    description: str


def find_knowledge_files(knowledge_dir: Path) -> set[str]:
    """List files under knowledge_dir as paths relative to it.

    Args:
        knowledge_dir: The `knowledge/` directory to scan.

    Returns:
        POSIX-style relative paths for every file under `knowledge_dir`,
        excluding `INDEX.md`, `CLAUDE.md`, and `TEMPLATE.md` files.
    """
    return {
        path.relative_to(knowledge_dir).as_posix()
        for path in knowledge_dir.rglob("*")
        if path.is_file() and path.name not in IGNORED_FILENAMES
    }


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract scalar key/value pairs from a leading YAML frontmatter block.

    Only handles scalar values and strips trailing `# ...` comments;
    this is intentionally minimal rather than a full YAML parser, since
    the hook only needs the `type`/`status`/`description` scalar fields.

    Args:
        text: Full contents of a markdown file.

    Returns:
        Mapping of frontmatter keys to their string values. Empty if the
        file has no leading `---` frontmatter block.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        uncommented = re.sub(r"\s+#.*$", "", line).strip()
        if not uncommented or ":" not in uncommented:
            continue
        key, _, value = uncommented.partition(":")
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


def has_complete_frontmatter(frontmatter: dict[str, str]) -> bool:
    """Check whether frontmatter has non-empty type/status/description.

    Args:
        frontmatter: Parsed frontmatter fields for one file.

    Returns:
        True if all fields required to auto-manage an INDEX.md row are
        present and non-empty.
    """
    return all(frontmatter.get(key) for key in REQUIRED_FRONTMATTER_KEYS)


def row_from_frontmatter(path: str, frontmatter: dict[str, str]) -> IndexRow:
    """Build the INDEX.md row a file's frontmatter implies.

    Args:
        path: The file's path relative to `knowledge/`.
        frontmatter: That file's parsed frontmatter; must be complete
            per `has_complete_frontmatter`.

    Returns:
        The row that should represent this file in INDEX.md.
    """
    return IndexRow(
        path=path,
        type=frontmatter["type"],
        status=frontmatter["status"],
        description=frontmatter["description"],
    )


def parse_index_rows(index_path: Path) -> list[IndexRow]:
    """Parse every data row of INDEX.md's markdown table.

    Args:
        index_path: Path to `knowledge/INDEX.md`.

    Returns:
        One `IndexRow` per data row, in file order. Empty if the file is
        missing or has no data rows.
    """
    if not index_path.exists():
        return []

    rows: list[IndexRow] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue

        first_cell = cells[0].strip("`")
        if not first_cell or first_cell.lower() == "file path":
            continue
        if set(first_cell) <= {"-"}:  # header separator row, e.g. |---|---|
            continue

        rows.append(
            IndexRow(
                path=first_cell, type=cells[1], status=cells[2], description=cells[3]
            )
        )

    return rows


def reconcile(
    on_disk: set[str],
    frontmatter_by_path: dict[str, dict[str, str]],
    existing_rows: list[IndexRow],
) -> tuple[list[IndexRow], list[str], list[str], list[str], list[str]]:
    """Reconcile INDEX.md rows against files on disk and their frontmatter.

    Args:
        on_disk: Paths (relative to `knowledge/`) of tracked files that
            currently exist.
        frontmatter_by_path: Each on-disk file's parsed frontmatter.
        existing_rows: The current INDEX.md rows.

    Returns:
        `(new_rows, added, updated, removed, needs_manual)`: the rows
        INDEX.md should now contain (sorted by path), and path lists
        describing rows added from frontmatter, rows whose Type/Status/
        Description were corrected, rows removed because the file is
        gone, and untracked files whose frontmatter is missing or
        incomplete so no row could be auto-added.
    """
    existing_by_path = {row.path: row for row in existing_rows}

    kept_rows = [row for row in existing_rows if row.path in on_disk]
    removed = sorted(row.path for row in existing_rows if row.path not in on_disk)

    updated: list[str] = []
    for i, row in enumerate(kept_rows):
        frontmatter = frontmatter_by_path.get(row.path, {})
        if not has_complete_frontmatter(frontmatter):
            continue
        fresh = row_from_frontmatter(row.path, frontmatter)
        if fresh != row:
            kept_rows[i] = fresh
            updated.append(row.path)

    added: list[str] = []
    needs_manual: list[str] = []
    for path in sorted(on_disk - existing_by_path.keys()):
        frontmatter = frontmatter_by_path.get(path, {})
        if has_complete_frontmatter(frontmatter):
            kept_rows.append(row_from_frontmatter(path, frontmatter))
            added.append(path)
        else:
            needs_manual.append(path)

    new_rows = sorted(kept_rows, key=lambda row: row.path)
    return new_rows, added, updated, removed, needs_manual


def build_table_block(rows: list[IndexRow]) -> str:
    """Render the full INDEX.md table block: header, separator, and body.

    Data rows must sit directly under the separator with no blank line, or
    GFM stops treating them as table rows. The empty-table placeholder is
    prose, not a row, so it keeps the original blank line before it.

    Args:
        rows: Rows to render, already sorted by path.

    Returns:
        The header, separator, and either the data rows or the
        "no files yet" placeholder paragraph.
    """
    if not rows:
        return f"{TABLE_HEADER}\n{TABLE_SEPARATOR}\n\n{EMPTY_TABLE_NOTE}\n\n"
    body = "\n".join(
        f"| {row.path} | {row.type} | {row.status} | {row.description} |"
        for row in rows
    )
    return f"{TABLE_HEADER}\n{TABLE_SEPARATOR}\n{body}\n\n"


def rewrite_index(index_path: Path, rows: list[IndexRow]) -> None:
    """Replace INDEX.md's table block with `rows`, preserving surrounding text.

    Args:
        index_path: Path to `knowledge/INDEX.md`.
        rows: The full, already-sorted set of rows the table should contain.

    Raises:
        ValueError: If the table header/separator markers can't be found,
            so a malformed rewrite never silently corrupts the file.
    """
    text = index_path.read_text(encoding="utf-8")
    replacement = build_table_block(rows)
    new_text, count = TABLE_BLOCK_RE.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError(f"Could not locate the INDEX.md table block in {index_path}")
    index_path.write_text(new_text, encoding="utf-8")


def build_report(
    added: list[str], updated: list[str], removed: list[str], needs_manual: list[str]
) -> str:
    """Format the SessionStart context describing INDEX.md reconciliation.

    Args:
        added: Paths auto-added as new INDEX.md rows from their frontmatter.
        updated: Paths whose row Type/Status/Description was auto-corrected.
        removed: Paths auto-removed because the file no longer exists.
        needs_manual: Untracked paths whose frontmatter is missing or
            incomplete, so a row could not be auto-added.

    Returns:
        A human-readable multi-line report.
    """
    lines = ["knowledge/INDEX.md was reconciled against knowledge/ contents:"]

    if added:
        lines.append("Added (new file, row created from its frontmatter):")
        lines.extend(f"  - {path}" for path in added)
    if updated:
        lines.append(
            "Updated (Type/Status/Description corrected to match frontmatter):"
        )
        lines.extend(f"  - {path}" for path in updated)
    if removed:
        lines.append("Removed (file no longer exists):")
        lines.extend(f"  - {path}" for path in removed)
    if needs_manual:
        lines.append(
            "Needs manual reconciliation (frontmatter missing or incomplete "
            "type/status/description, so no row could be auto-added):"
        )
        lines.extend(f"  - {path}" for path in needs_manual)
        lines.append(
            "Add a row for these with a best-effort Type/Status/Description. "
            "See .github/copilot-instructions.md."
        )

    return "\n".join(lines)


def main() -> None:
    """Reconcile knowledge/INDEX.md against knowledge/ contents and report it."""
    knowledge_dir = Path.cwd() / "knowledge"
    if not knowledge_dir.is_dir():
        return

    index_path = knowledge_dir / "INDEX.md"
    on_disk = find_knowledge_files(knowledge_dir)
    frontmatter_by_path = {
        path: parse_frontmatter((knowledge_dir / path).read_text(encoding="utf-8"))
        for path in on_disk
    }
    existing_rows = parse_index_rows(index_path)

    new_rows, added, updated, removed, needs_manual = reconcile(
        on_disk, frontmatter_by_path, existing_rows
    )

    if new_rows != existing_rows:
        rewrite_index(index_path, new_rows)

    if not (added or updated or removed or needs_manual):
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": build_report(
                        added, updated, removed, needs_manual
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
