"""Main entry point for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from importlib import import_module

from bosa_cli.commands.base import BaseCommands
from bosa_cli.config import CLIConfig
from bosa_cli.constants import EXIT_GENERAL_ERROR, EXIT_INVALID_SUBCOMMAND, MAIN_EPILOG
from bosa_cli.utils import fail, print_error


def discover_commands() -> dict[str, BaseCommands]:
    """Discover command modules from the commands folder.

    Returns:
        Dict of command name to command class

    """
    # Register subcommands
    subcommands = [
        "auth",
        "integrations",
        "users",
    ]

    commands = {}
    for module_name in subcommands:
        try:
            module = import_module(f"bosa_cli.commands.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and attr_name.endswith("Commands")
                    and attr_name != "BaseCommands"
                    and issubclass(attr, BaseCommands)
                ):
                    commands[module_name] = attr
                    break

        except ImportError as e:
            print_error(f"Failed to import command module '{module_name}': {e}")
            sys.exit(EXIT_GENERAL_ERROR)

    return commands


def create_parser() -> tuple[ArgumentParser, dict[str, BaseCommands]]:
    """Create argument parser for BOSA CLI.

    Returns:
        Configured argument parser

    """
    parser = ArgumentParser(
        prog="bosa",
        description="BOSA CLI - Command line interface for BOSA API",
        formatter_class=RawDescriptionHelpFormatter,
        epilog=MAIN_EPILOG,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    commands = discover_commands()

    for command_class in commands.values():
        command_class.add_subparser(subparsers)

    return parser, commands


def main() -> int:
    """Run the main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for error)

    """
    try:
        parser, available_commands = create_parser()
        args = parser.parse_args()

        if args.command in available_commands:
            command_class = available_commands[args.command]

            config = CLIConfig()
            command_instance = command_class(config)

            return command_instance.handle(args)

        else:
            parser.print_help()
            return EXIT_INVALID_SUBCOMMAND

    except KeyboardInterrupt:
        return fail("Operation cancelled by user")
    except Exception as e:
        return fail(f"Unexpected error: {str(e)}")
