"""Modified Cache Module."""

from __future__ import annotations

from typing import Any

from diskcache import Cache


class ModifiedCache(Cache):
    """A modified cache class with additional functionality."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the cache with custom parameters."""
        super().__init__(*args, **kwargs)

    def find_and_delete(self, query: Any) -> bool:
        """Find and delete cache entries matching the query.

        Args:
            query: The query string to match against cache keys.
        """
        return any(isinstance(key, tuple | list) and str(query) in str(key) and self.delete(key) for key in self)
