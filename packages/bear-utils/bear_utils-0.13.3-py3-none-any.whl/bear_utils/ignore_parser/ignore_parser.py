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
        )
        self.ignore_handler: BaseIgnoreHandler = BaseIgnoreHandler(config=config)
        self.path: Path = Path(path)
        self._files: PathsContainer | None = None
        if scan:
            self._files = self.scan_codebase()

    @property
    def spec(self) -> PathSpec:
        """Get the current PathSpec object."""
        return self.ignore_handler.spec

    @cached_property
    def files(self) -> PathsContainer:
        """Get the PathsContainer object, creating it if it doesn't exist."""
        if self._files is None:
            self._files = PathsContainer().create(self.path, self.spec)
        return self._files

    @cached_property
    def ignored_files_count(self) -> int:
        """Get the count of ignored files.

        Returns:
            int: The number of ignored files
        """
        return self.files.ignored_count

    @cached_property
    def non_ignored_files_count(self) -> int:
        """Get the count of non-ignored files.

        Returns:
            int: The number of non-ignored files
        """
        return self.files.non_ignored_count

    @cached_property
    def ignored_files(self) -> list[Path]:
        """Get a list of ignored files.

        Returns:
            List of ignored files as Path objects
        """
        return self.files.ignored_paths

    @cached_property
    def non_ignored_files(self) -> list[Path]:
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
        return PathsContainer.create(self.path, self.spec)

    def check_path(self, path: Path | str) -> bool:
        """Check if a specific path is ignored.

        Args:
            path: The path to check
        Returns:
            bool: True if the path is ignored, False otherwise
        """
        return self.ignore_handler.should_ignore(path)


if __name__ == "__main__":
    handler = IgnoreHandler(
        path=Path("/Users/chaz/Documents/repos/github/sicksubroutine/bear-utils/src/bear_utils"),
        ignore_files=[Path("/Users/chaz/Documents/repos/github/sicksubroutine/bear-utils/.gitignore")],
        verbose=True,
    )

    print(handler.spec)

    print(f"Ignored files count: {handler.ignored_files_count}")
    print(f"Non-ignored files count: {handler.non_ignored_files_count}")

    # print out 5 ignored and non-ignored files
    print(f"Ignored files: {handler.ignored_files[:5]}")

    print(f"Non-ignored files: {handler.non_ignored_files[:5]}")
    test_path = Path(__file__)
    print(f"Is '{test_path}' ignored? {handler.check_path(test_path)}")
