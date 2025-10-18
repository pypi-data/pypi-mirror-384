"""A set of utilities for managing the system clipboard with platform-specific commands."""

import asyncio
from asyncio.subprocess import PIPE
from functools import cached_property
import shutil
from typing import TYPE_CHECKING

from bear_dereth.cli.shell._base_command import BaseShellCommand as ShellCommand
from bear_dereth.cli.shell._base_shell import AsyncShellSession
from bear_dereth.data_structs.stacks.simple import BoundedStack
from bear_dereth.platform_utils import OS, get_platform

if TYPE_CHECKING:
    from subprocess import CompletedProcess


def shutil_which(cmd: str) -> None | str:
    """A wrapper around shutil.which to return None if the command is not found."""
    return shutil.which(cmd)


class ClipboardManager:
    """A class to manage clipboard operations such as copying, pasting, and clearing.

    This class provides methods to interact with the system clipboard.
    """

    def __init__(self, maxlen: int = 10) -> None:
        """Initialize the ClipboardManager with a maximum history length."""
        self.clipboard_history: BoundedStack[str] = BoundedStack(max_size=maxlen, overflow="drop_oldest")
        self.shell = AsyncShellSession(env={"LANG": "en_US.UTF-8"}, verbose=False)
        self.platform: OS = get_platform()

    @cached_property
    def _copy(self) -> ShellCommand[str]:
        """Get the copy command based on the platform."""
        return get_copy(self.platform)

    @cached_property
    def _paste(self) -> ShellCommand[str]:
        """Get the paste command based on the platform."""
        return get_paste(self.platform)

    def get_history(self) -> list[str]:
        """Get the clipboard history.

        Returns:
            deque: The history of clipboard entries.
        """
        return self.clipboard_history.copy()

    async def copy(self, output: str) -> int:
        """A function that copies the output to the clipboard.

        Args:
            output (str): The output to copy to the clipboard.

        Returns:
            int: The return code of the command.
        """
        await self.shell.run(cmd=self._copy, stdin=PIPE)
        result: CompletedProcess[str] = await self.shell.communicate(stdin=output)
        return result.returncode

    async def paste(self) -> str:
        """Paste the output from the clipboard.

        Returns:
            str: The content of the clipboard.

        Raises:
            RuntimeError: If the paste command fails.
        """
        try:
            await self.shell.run(cmd=self._paste)
            result: CompletedProcess[str] = await self.shell.communicate()
        except Exception as e:
            raise RuntimeError(f"Error pasting from clipboard: {e}") from e
        if result.returncode != 0:
            raise RuntimeError(f"{self._paste.cmd} failed with return code {result.returncode}")
        return result.stdout

    async def clear(self) -> int:
        """A function that clears the clipboard.

        Returns:
            int: The return code of the command.
        """
        return await self.copy(output="")


def copy_to_clipboard(output: str) -> int:
    """Copy the output to the clipboard.

    Args:
        output (str): The output to copy to the clipboard.

    Returns:
        int: The return code of the command.
    """
    clipboard_manager = ClipboardManager()
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    return loop.run_until_complete(future=clipboard_manager.copy(output))


async def copy_to_clipboard_async(output: str) -> int:
    """Asynchronously copy the output to the clipboard.

    Args:
        output (str): The output to copy to the clipboard.

    Returns:
        int: The return code of the command.
    """
    clipboard_manager = ClipboardManager()
    return await clipboard_manager.copy(output=output)


def paste_from_clipboard() -> str:
    """Paste the output from the clipboard.

    Returns:
        str: The content of the clipboard.
    """
    clipboard_manager = ClipboardManager()
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    return loop.run_until_complete(future=clipboard_manager.paste())


async def paste_from_clipboard_async() -> str:
    """Asynchronously paste the output from the clipboard.

    Returns:
        str: The content of the clipboard.
    """
    clipboard_manager = ClipboardManager()
    return await clipboard_manager.paste()


def clear_clipboard() -> int:
    """Clear the clipboard.

    Returns:
        int: The return code of the command.
    """
    clipboard_manager = ClipboardManager()
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    return loop.run_until_complete(clipboard_manager.clear())


async def clear_clipboard_async() -> int:
    """Asynchronously clear the clipboard.

    Returns:
        int: The return code of the command.
    """
    clipboard_manager = ClipboardManager()
    return await clipboard_manager.clear()


PBCOPY: ShellCommand = ShellCommand.adhoc(name="pbcopy")
PBPASTE: ShellCommand = ShellCommand.adhoc(name="pbpaste")
WL_COPY: ShellCommand = ShellCommand.adhoc(name="wl-copy")
WL_PASTE: ShellCommand = ShellCommand.adhoc(name="wl-paste")
XCLIP_COPY: ShellCommand = ShellCommand.adhoc(name="xclip").sub("-selection clipboard")
XCLIP_PASTE: ShellCommand = ShellCommand.adhoc(name="xclip").sub("-selection clipboard -o")
CLIP: ShellCommand = ShellCommand.adhoc(name="clip")
POWERSHELL_GET_CLIPBOARD: ShellCommand = ShellCommand.adhoc(name="powershell").sub("Get-Clipboard")


def get_copy(platform: OS) -> ShellCommand[str]:
    """Get the copy command based on the platform.

    Returns:
        ShellCommand[str]: The command to copy to the clipboard.

    Raises:
        RuntimeError: If no clipboard command is found for the platform.
    """
    match platform:
        case OS.DARWIN:
            return PBCOPY
        case OS.LINUX:
            if shutil_which(cmd="wl-copy") and shutil_which(cmd="wl-paste"):
                return WL_COPY
            if shutil_which(cmd="xclip"):
                return XCLIP_COPY
            raise RuntimeError("No clipboard command found on Linux")
        case OS.WINDOWS:
            return CLIP
        case _:
            raise RuntimeError(f"Unsupported platform: {platform}")


def get_paste(platform: OS) -> ShellCommand[str]:
    """Get the paste command based on the platform.

    Returns:
        ShellCommand[str]: The command to paste from the clipboard.

    Raises:
        RuntimeError: If no clipboard command is found for the platform.
    """
    match platform:
        case OS.DARWIN:
            return PBPASTE
        case OS.LINUX:
            if shutil_which(cmd="wl-copy") and shutil_which(cmd="wl-paste"):
                return WL_PASTE
            if shutil_which(cmd="xclip"):
                return XCLIP_PASTE
            raise RuntimeError("No clipboard command found on Linux")
        case OS.WINDOWS:
            return POWERSHELL_GET_CLIPBOARD
        case _:
            raise RuntimeError(f"Unsupported platform: {platform}")


__all__ = [
    "ClipboardManager",
    "clear_clipboard",
    "clear_clipboard_async",
    "copy_to_clipboard",
    "copy_to_clipboard_async",
    "get_copy",
    "get_paste",
    "paste_from_clipboard",
    "paste_from_clipboard_async",
]
