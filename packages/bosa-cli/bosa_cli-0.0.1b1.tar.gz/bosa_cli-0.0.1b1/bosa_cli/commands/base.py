"""Base command class for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

from abc import ABC, abstractmethod
from typing import Optional

from bosa_cli.config import CLIConfig
from bosa_cli.constants import AUTH_LOGIN_HELP
from bosa_cli.utils import print_error, print_info


class BaseCommands(ABC):
    """Base class for all CLI commands."""

    def __init__(self, config: Optional[CLIConfig] = None):
        """Initialize the base commands.

        Args:
            config: CLI configuration

        """
        self.config = config

    def _is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True if authenticated, False if not (and error message shown)

        """
        if not self.config or not self.config.is_authenticated():
            print_error("Not authenticated.")
            print_info(AUTH_LOGIN_HELP)
            return False

        return True

    @classmethod
    @abstractmethod
    def add_subparser(cls, subparsers) -> None:
        """Add command-specific subparser and arguments.

        Args:
            subparsers: Parent subparsers object

        Returns:
            The command parser for help display (optional)

        """
        raise NotImplementedError()

    @abstractmethod
    def handle(self, args) -> int:
        """Handle the command execution.

        Returns:
            Exit code (0 for success, non-zero for error)

        """
        raise NotImplementedError()
