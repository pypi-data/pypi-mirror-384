"""A module for handling file ignore patterns and directories in Bear Utils."""

from functools import cached_property
from pathlib import Path

from pathspec import PathSpec

from bear_utils.ignore_parser.base_class import BaseIgnoreHandler
from bear_utils.ignore_parser.common import IgnoreConfig, PathsContainer


class IgnoreHandler:
    """Handles the logic for ignoring files and directories based on .gitignore-style rules."""

    def __init__(
        self,
        path: Path | str,
        ignore_files: list[Path] | None = None,
        patterns: list[str] | None = None,
        verbose: bool = False,
        scan: bool = False,
        output_as_absolute: bool = False,
    ) -> None:
        """Initialize the IgnoreHandler with a directory to search and an optional ignore file.

        Args:
            path: The directory to search
            ignore_file: An optional path to a .gitignore-style file
            scan: Whether to immediately scan the directory upon initialization
        """
        config = IgnoreConfig(
            directory=Path(path),
            verbose=verbose,
            ignore_files=ignore_files or [],
            patterns=patterns or [],
            output_as_absolute=output_as_absolute,
        )
        self.ih: BaseIgnoreHandler = BaseIgnoreHandler(config=config)
        self.path: Path = Path(path)
        self._files: PathsContainer | None = self.scan_codebase() if scan else None

    def _create(self) -> PathsContainer:
        """Create and return a PathsContainer for the current path and spec.

        Returns:
            PathsContainer: A container with details about ignored and non-ignored files
        """
        return PathsContainer.create(self.path, self.spec, self.ih.output_as_absolute)

    @property
    def spec(self) -> PathSpec:
        """Get the current PathSpec object."""
        return self.ih.spec

    @cached_property
    def files(self) -> PathsContainer:
        """Get the PathsContainer object, creating it if it doesn't exist."""
        if self._files is None:
            self._files = self._create()
        return self._files

    @cached_property
    def ignored_count(self) -> int:
        """Get the count of ignored files.

        Returns:
            int: The number of ignored files
        """
        return self.files.ignored_count

    @cached_property
    def non_ignored_count(self) -> int:
        """Get the count of non-ignored files.

        Returns:
            int: The number of non-ignored files
        """
        return self.files.non_ignored_count

    @cached_property
    def ignored(self) -> list[Path]:
        """Get a list of ignored files.

        Returns:
            List of ignored files as Path objects
        """
        return self.files.ignored_paths

    @cached_property
    def non_ignored(self) -> list[Path]:
        """Get a list of non-ignored files.

        Returns:
            List of non-ignored files as Path objects
        """
        return self.files.non_ignored_paths

    def scan_codebase(self) -> PathsContainer:
        """Generate a report of ignored and non-ignored files in the directory.

        Returns:
            PathsContainer: A container with details about ignored and non-ignored files
        """
        return self._create()

    def check_path(self, path: Path | str) -> bool:
        """Check if a specific path is ignored.

        Args:
            path: The path to check
        Returns:
            bool: True if the path is ignored, False otherwise
        """
        return self.ih.should_ignore(path)


# if __name__ == "__main__":
#     ih = IgnoreHandler(
#         path="src/bear_utils",
#         ignore_files=[Path(".gitignore")],
#         patterns=["*.md"],
#         verbose=True,
#         scan=True,
#     )

#     print("Non-ignored files:")
#     for file in ih.non_ignored:
#         print(f" - {file}")
