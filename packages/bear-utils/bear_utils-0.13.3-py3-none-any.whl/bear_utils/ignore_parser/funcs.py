"""Ignore Parser related helpers."""

from __future__ import annotations

from pathlib import Path

from pathspec import PathSpec

from bear_dereth.operations.iterstuffs import ListMerge


def create_spec(patterns: list[str]) -> PathSpec:
    """Create a pathspec from the given patterns.

    Args:
        patterns: List of ignore patterns

    Returns:
        A pathspec object
    """
    return PathSpec.from_lines("gitwildmatch", patterns)


def file_to_pattern(gitignore_path: Path | str) -> list[str]:
    """Read a .gitignore file and return its patterns as a list.

    Args:
        gitignore_path: Path to the .gitignore file
    Returns:
        A list of patterns from the .gitignore file
    """
    path = Path(gitignore_path)
    if not path.exists() or not path.is_file():
        return []
    try:
        lines: list[str] = path.read_text().splitlines()
    except (FileNotFoundError, OSError):
        return []
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("!") and line
    ]


def combine_patterns(*pattern_lists: list[str]) -> list[str]:
    """Combine multiple lists of patterns into a single list without duplicates.

    Args:
        *pattern_lists: Multiple lists of patterns to combine

    Returns:
        A combined list of unique patterns
    """
    return ListMerge(*pattern_lists, unique=True).as_list()
