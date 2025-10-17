"""Schemas for file operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Self

from pathspec import PathSpec
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from pathspec import PathSpec

IGNORE_PATTERNS: list[str] = [
    "**/__pycache__",
    ".git",
    "**/.venv",
    ".env",
    ".vscode",
    ".idea",
    "*.DS_Store*",
    "__pypackages__",
    ".pytest_cache",
    ".coverage",
    ".*.swp",
    ".*.swo",
    "*.lock",
    "dist/",
    "**/.nox",
    "**/.pytest_cache",
    "**/.ruff_cache",
]


class IgnoreConfig(BaseModel):
    """Configuration for the IgnoreHandler."""

    # model_config = {"extra": "ignore"}

    directory: Path = Path().cwd()
    verbose: bool = False
    ignore_count: int = 100
    ignore_files: list[Path] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)

    def model_post_init(self, context: dict) -> None:
        """Post-initialization to set default patterns if none are provided."""
        self.patterns = [*IGNORE_PATTERNS, *self.patterns]
        if self.ignore_files is None:
            self.ignore_files = [self.directory / ".gitignore"]
        super().model_post_init(context)

    @field_validator("directory", mode="before")
    @classmethod
    def force_path(cls, v: Path | str) -> Path:
        """Ensure the directory is a Path object."""
        return Path(v).expanduser().resolve()

    def update(self, **kwargs) -> Self:
        """Update the configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


@dataclass(slots=True)
class PathObject:
    """Container for a path, a string representation, and an ignore status."""

    path: Path
    str_path: str = field(init=False)
    ignored: bool = False

    def __post_init__(self) -> None:
        self.str_path = str(self.path)


@dataclass
class PathsContainer:
    """Container for multiple PathContainer objects."""

    root: Path = Path(".")
    paths: list[PathObject] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of files that were processed."""
        return len(self.paths)

    @cached_property
    def ignored_count(self) -> int:
        """Number of ignored files."""
        return len([c for c in self.paths if c.ignored])

    @cached_property
    def non_ignored_count(self) -> int:
        """Number of non-ignored files."""
        return len([c for c in self.paths if not c.ignored])

    @cached_property
    def ignored_paths(self) -> list[Path]:
        """List of ignored paths."""
        return [c.path for c in self.paths if c.ignored]

    @cached_property
    def non_ignored_paths(self) -> list[Path]:
        """List of non-ignored paths."""
        return [c.path for c in self.paths if not c.ignored]

    @classmethod
    def create(cls, directory: Path | str, spec: PathSpec) -> PathsContainer:
        """Create a PathsContainer from a directory and a PathSpec."""
        new: Self = cls()
        new.root = Path(directory).expanduser().resolve()
        for path in new.root.rglob("*"):
            rel_path: Path = path.relative_to(new.root)
            obj = PathObject(rel_path)
            if path.is_file():
                obj.ignored = spec.match_file(obj.str_path)
            elif path.is_dir() and not obj.str_path.endswith("/"):
                obj.ignored = spec.match_file(obj.str_path + "/")
            new.paths.append(obj)
        return new
