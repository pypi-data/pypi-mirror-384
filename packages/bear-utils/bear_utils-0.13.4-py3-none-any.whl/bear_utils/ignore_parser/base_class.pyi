from pathlib import Path

from pathspec import PathSpec

from bear_utils.ignore_parser.common import IgnoreConfig

class BaseIgnoreHandler:
    ignore_files: list[Path]
    patterns: list[str]
    spec: PathSpec
    config: IgnoreConfig

    def __init__(
        self,
        ignore_files: list[Path] | Path | None = None,
        patterns: list[str] | None = None,
        verbose: bool = False,
        ignore_count: int = 100,
        config: IgnoreConfig | None = None,
    ) -> None: ...
    def _create_patterns(self) -> list[str]: ...
    def add_pattern(self, pattern: str) -> None: ...
    def add_patterns(self, patterns: list[str]) -> None: ...
    def should_ignore(self, path: Path | str) -> bool: ...
