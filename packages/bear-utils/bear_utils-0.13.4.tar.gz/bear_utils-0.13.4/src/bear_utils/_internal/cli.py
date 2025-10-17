# TODO: Replace with the Typer Version eventually

# - When you run `python -m bear_utils` python will execute
#   `__main__.py` as a script. That means there won't be any
#   `bear_utils.__main__` in `sys.modules`.
# - When you import `__main__` it will get executed again (as a module) because
#   there's no `bear_utils.__main__` in `sys.modules`.
from __future__ import annotations

from argparse import ArgumentParser, Namespace
import sys

from bear_dereth.cli.arg_helpers import CLIArgsType, args_parse
from bear_dereth.cli.exit_code import ExitCode
from bear_dereth.versioning import VALID_BUMP_TYPES, BumpType, cli_bump
from bear_utils._internal._info import _METADATA
from bear_utils._internal.debug import _print_debug_info


def _get_args(args: CLIArgsType) -> Namespace:
    name: str = _METADATA.name
    parser = ArgumentParser(description=name.capitalize(), prog=name, exit_on_error=False)
    subparser = parser.add_subparsers(dest="command", required=False, help="Available commands")
    subparser.add_parser("version", help="Get the current version of the package")
    debug = subparser.add_parser("debug_info", help="Print debug information")
    debug.add_argument("-n", "--no-color", action="store_true", help="Disable color output")
    bump: ArgumentParser = subparser.add_parser("bump")
    bump.add_argument("bump_type", type=str, choices=VALID_BUMP_TYPES, help="major, minor, or patch")
    return parser.parse_args(args)


def _debug_info(no_color: bool = False) -> ExitCode:
    """CLI command to print debug information."""
    _print_debug_info(no_color=no_color)
    return ExitCode.SUCCESS


def _version(name: bool = False) -> ExitCode:
    """CLI command to get the current version of the package."""
    to_print: str = ""
    if name:
        to_print += _METADATA.name + " "
    to_print += _METADATA.version
    print(to_print)
    return ExitCode.SUCCESS


def _bump(bump_type: BumpType) -> ExitCode:
    """CLI command to bump the version of the package."""
    return cli_bump(b_type=bump_type, package_name=_METADATA.name, ver=_METADATA.version_tuple)


@args_parse()
def main(args: CLIArgsType) -> ExitCode:
    """Main entry point for the CLI.

    This function is called when the CLI is executed. It can be used to
    initialize the CLI, parse arguments, and execute commands.

    Args:
        args (list[str] | None): A list of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        int: Exit code of the CLI execution. 0 for success, non-zero for failure.
    """
    arguments: Namespace = _get_args(args)
    try:
        if arguments.command == "version":
            return _version()
        if arguments.command == "debug_info":
            return _debug_info()
        if arguments.command == "bump":
            return _bump(bump_type=arguments.bump_type)
        return ExitCode.SUCCESS
    except SystemExit as e:
        if e.code is not None and isinstance(e.code, int):
            return ExitCode(e.code)
        return ExitCode.SUCCESS
    except Exception:
        return ExitCode.FAILURE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
