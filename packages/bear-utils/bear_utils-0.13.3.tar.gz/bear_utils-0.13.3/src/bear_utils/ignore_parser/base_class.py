"""Base class for handling ignore patterns and checking if files should be ignored."""

from pathlib import Path
from typing import TYPE_CHECKING

from bear_utils.ignore_parser.common import IgnoreConfig
from bear_utils.ignore_parser.funcs import combine_patterns, create_spec, file_to_pattern

if TYPE_CHECKING:
    from pathspec import PathSpec


class BaseIgnoreHandler:
    """Basic ignore handler for manually checking if a file should be ignored based on set patterns."""

    def __init__(self, **kwargs) -> None:
        """Initialize the IgnoreHandler with an optional ignore file."""
        self.config: IgnoreConfig = kwargs.pop("config") or IgnoreConfig().update(**kwargs)
        self.ignore_count: int = self.config.ignore_count
        self.ignore_files: list[Path] = self.config.ignore_files
        self.patterns: list[str] = self._create_patterns()
        self.spec: PathSpec = create_spec(self.patterns)

    def _create_patterns(self) -> list[str]:
        """Create and return the current list of ignore patterns.

        Returns:
            List of current ignore patterns
        """
        patterns: list[list[str]] = [self.config.patterns]
        for path in self.ignore_files:
            patterns.append(file_to_pattern(path))
        return combine_patterns(*patterns)

    def add_pattern(self, pattern: str) -> None:
        """Inject a single pattern into the existing spec.

        Args:
            pattern: The pattern to inject
        """
        if pattern not in self.patterns:
            self.patterns.append(pattern)
            self.spec = create_spec(self.patterns)

    def add_patterns(self, patterns: list[str]) -> None:
        """Inject additional patterns into the existing spec.

        Args:
            patterns: List of additional patterns to inject
        """
        self.patterns = combine_patterns(self.patterns, patterns)
        self.spec = create_spec(self.patterns)

    def should_ignore(self, path: Path | str) -> bool:
        """Check if a given path should be ignored based on the ignore patterns.

        Args:
            path (Path): The path to check
        Returns:
            bool: True if the path should be ignored, False otherwise
        """
        path = Path(path).expanduser().resolve()
        if path.is_dir() and not str(path).endswith("/"):
            return self.spec.match_file(str(path) + "/")
        return self.spec.match_file(str(path))
