"""Authentication commands for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import argparse
from typing import Optional

from bosa_cli.api import AuthAPIClient
from bosa_cli.commands.base import BaseCommands
from bosa_cli.config import CLIConfig
from bosa_cli.constants import (
    AUTH_LOGIN_EPILOG,
    AUTH_MAIN_EPILOG,
    DEFAULT_API_URL,
    EXIT_AUTH_ERROR,
    EXIT_GENERAL_ERROR,
    EXIT_INVALID_SUBCOMMAND,
)
from bosa_cli.utils import (
    CLIError,
    fail,
    mask_client_key,
    mask_token,
    print_header,
    print_info,
    print_success,
    prompt_for_input,
    succeed,
)


class AuthCommands(BaseCommands):
    """Authentication command handlers."""

    def __init__(self, config: Optional[CLIConfig] = None):
        """Initialize auth commands.

        Args:
            config: CLI configuration (optional for parser setup)

        """
        super().__init__(config)
        if config:
            self.api_client = AuthAPIClient(config.get_api_url())

    @classmethod
    def add_subparser(cls, subparsers):
        """Add command-specific subparser and arguments (class method).

        Args:
            subparsers: Parent subparsers object

        Returns:
            The auth parser for help display

        """
        auth_parser = subparsers.add_parser(
            "auth",
            help="Authentication commands",
            epilog=AUTH_MAIN_EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        auth_subparsers = auth_parser.add_subparsers(dest="auth_command", required=False)
        auth_parser.error = cls.auth_error_handler

        login_parser = auth_subparsers.add_parser(
            "login",
            help="Login with client API key and user credentials",
            epilog=AUTH_LOGIN_EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        login_parser.add_argument("--api-url", help="BOSA API base URL", default=DEFAULT_API_URL)
        login_parser.add_argument("client_api_key", nargs="?", help="Client API key (sk-client-...)")
        login_parser.add_argument("username", nargs="?", help="User identifier")
        login_parser.add_argument("user_secret", nargs="?", help="User secret")

        # Logout command
        auth_subparsers.add_parser("logout", help="Logout and clear session")

        # Status command
        auth_subparsers.add_parser("status", help="Show authentication status")

        cls.parser = auth_parser

        return auth_parser

    @classmethod
    def auth_error_handler(cls, message):
        """Handle authentication errors.

        Args:
            message: Error message

        Returns:
            Exit code (0 for success, 3 for invalid subcommand)

        """
        cls.parser.print_help()
        return fail(message, EXIT_INVALID_SUBCOMMAND)

    def handle(self, args):
        """Handle auth commands.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 for success, 1 for error)

        """
        match args.auth_command:
            case "login":
                api_url = getattr(args, "api_url", DEFAULT_API_URL)
                return self.login(args.client_api_key, args.username, args.user_secret, api_url)
            case "logout":
                return self.logout()
            case "status":
                return self.status()
            case _:
                print(
                    """
usage: bosa auth [-h] {login,logout,status} ...

positional arguments:
    {login,logout,status}

options:
    -h, --help            show this help message and exit
"""
                )
                return EXIT_INVALID_SUBCOMMAND

    def login(
        self,
        client_api_key: Optional[str] = None,
        username: Optional[str] = None,
        user_secret: Optional[str] = None,
        api_url: str = DEFAULT_API_URL,
    ) -> int:
        """Login with client API key and user credentials.

        Args:
            client_api_key: Client API key (sk-client-...)
            username: User identifier
            user_secret: User secret
            api_url: BOSA API base URL

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            self.api_client = AuthAPIClient(api_url)

            if not client_api_key:
                client_api_key = prompt_for_input("Client API Key", hide=True)

            if not username:
                username = prompt_for_input("Username (User Identifier)")

            if not user_secret:
                user_secret = prompt_for_input("User Secret", hide=True)

            print_info("Authenticating...")
            token_info = self.api_client.authenticate_user(client_api_key, username, user_secret)

            self.config.save_session(
                client_api_key=client_api_key,
                api_url=api_url,
                username=username,
                token=token_info.token,
                token_type=token_info.token_type,
                expires_at=token_info.expires_at.isoformat(),
                user_id=str(token_info.user_id),
                is_revoked=token_info.is_revoked,
            )

            print_success("Authentication successful!")
            print_info(f"Logged in as: {username}")
            print_info(f"Token expires: {token_info.expires_at}")
            print_info(f"Session saved to: {self.config.config_path}")

            return succeed("Authentication successful!")

        except CLIError as e:
            return fail(f"Authentication failed: {str(e)}", EXIT_AUTH_ERROR)
        except Exception as e:
            return fail(f"Login failed: {str(e)}", EXIT_GENERAL_ERROR)

    def logout(self) -> int:
        """Logout and clear session.

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            self.config.clear_session()
            return succeed("Successfully logged out")

        except Exception as e:
            return fail(f"Logout failed: {str(e)}", EXIT_GENERAL_ERROR)

    def status(self) -> int:
        """Show authentication status.

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            session = self.config.get_session()
            print_header("Authentication Status")
            print_info(f"Username: {session.username}")
            print_info(f"API URL: {session.api_url}")
            print_info(f"Client API Key: {mask_client_key(session.client_api_key)}")
            print_info(f"Token: {mask_token(session.token)}")
            print_info(f"Token Type: {session.token_type}")
            print_info(f"Token Expires: {session.expires_at}")
            print_info(f"User ID: {session.user_id}")
            print_info(f"Config File: {self.config.config_path}")

            return succeed("Status check successful!")

        except Exception as e:
            return fail(f"Status check failed: {str(e)}", EXIT_GENERAL_ERROR)
