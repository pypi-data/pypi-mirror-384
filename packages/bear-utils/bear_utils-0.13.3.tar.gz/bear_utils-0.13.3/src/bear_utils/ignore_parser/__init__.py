"""A module for file handling utilities in Bear Utils."""

from .common import IGNORE_PATTERNS
from .funcs import combine_patterns, create_spec, file_to_pattern
from .ignore_parser import IgnoreHandler

__all__ = ["IGNORE_PATTERNS", "IgnoreHandler", "combine_patterns", "create_spec", "file_to_pattern"]
