"""A module for various utilities in Bear Utils extras."""

from .clipboard import (
    ClipboardManager,
    clear_clipboard,
    clear_clipboard_async,
    copy_to_clipboard,
    copy_to_clipboard_async,
)

__all__ = [
    "ClipboardManager",
    "clear_clipboard",
    "clear_clipboard_async",
    "copy_to_clipboard",
    "copy_to_clipboard_async",
]
