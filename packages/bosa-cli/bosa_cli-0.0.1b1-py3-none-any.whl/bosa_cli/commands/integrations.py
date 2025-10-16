"""Integration management commands for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import argparse
import json
import webbrowser
from typing import Optional, Union

from bosa_cli.api import IntegrationsAPIClient, UsersAPIClient
from bosa_cli.api.models import BosaUser
from bosa_cli.commands.base import BaseCommands
from bosa_cli.config import CLIConfig
from bosa_cli.constants import (
    CONNECTOR_FIELD,
    EXIT_AUTH_ERROR,
    EXIT_GENERAL_ERROR,
    EXIT_INVALID_SUBCOMMAND,
    EXIT_REQUEST_ERROR,
    HELP_CONNECTOR,
    HELP_IDENTIFIER,
    INTEGRATIONS_ADD_EPILOG,
    INTEGRATIONS_COUNT_FIELD,
    INTEGRATIONS_MAIN_EPILOG,
    INTEGRATIONS_REMOVE_EPILOG,
    INTEGRATIONS_SHOW_EPILOG,
    METAVAR_ACCOUNT,
    METAVAR_CONNECTOR,
    USER_IDENTIFIER_FIELD,
)
from bosa_cli.utils import (
    CLIError,
    confirm_action,
    fail,
    print_error,
    print_header,
    print_info,
    print_success,
    print_table,
    print_warning,
    succeed,
)


class IntegrationsCommands(BaseCommands):
    """Integration management command handlers."""

    def __init__(self, config: Optional[CLIConfig] = None):
        """Initialize integration commands.

        Args:
            config: CLI configuration (optional for parser setup)

        """
        super().__init__(config)
        if config:
            self.integrations_api_client = IntegrationsAPIClient(config.get_api_url())
            self.users_api_client = UsersAPIClient(config.get_api_url())

    @classmethod
    def add_subparser(cls, subparsers):
        """Add command-specific subparser and arguments (class method).

        Args:
            subparsers: Parent subparsers object

        Returns:
            The integrations parser for help display

        """
        integrations_parser = subparsers.add_parser(
            "integrations",
            help="Integration management",
            epilog=INTEGRATIONS_MAIN_EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        integrations_subparsers = integrations_parser.add_subparsers(dest="integrations_command", required=False)
        integrations_parser.error = cls.integrations_error_handler

        # Default to list
        integrations_parser.set_defaults(integrations_command="list")

        # List command
        integrations_subparsers.add_parser("list", help="List all integrations (default)")

        # Add command
        add_parser = integrations_subparsers.add_parser(
            "add", help="Add a new integration", epilog=INTEGRATIONS_ADD_EPILOG
        )
        add_parser.add_argument("connector", metavar=METAVAR_CONNECTOR, help=HELP_CONNECTOR)

        # Remove command
        remove_parser = integrations_subparsers.add_parser(
            "remove", help="Remove an integration", epilog=INTEGRATIONS_REMOVE_EPILOG
        )
        remove_parser.add_argument("connector", metavar=METAVAR_CONNECTOR, help=HELP_CONNECTOR)
        remove_parser.add_argument("account", metavar=METAVAR_ACCOUNT, help=HELP_IDENTIFIER)

        # Show command
        show_parser = integrations_subparsers.add_parser(
            "show", help="Show integration details", epilog=INTEGRATIONS_SHOW_EPILOG
        )
        show_parser.add_argument("connector", metavar=METAVAR_CONNECTOR, help=HELP_CONNECTOR)
        show_parser.add_argument("identifier", nargs="?", metavar=METAVAR_ACCOUNT, help=HELP_IDENTIFIER)

        # Select command
        select_parser = integrations_subparsers.add_parser("select", help="Set an integration as selected")
        select_parser.add_argument("connector", metavar=METAVAR_CONNECTOR, help=HELP_CONNECTOR)
        select_parser.add_argument("account", metavar=METAVAR_ACCOUNT, help=HELP_IDENTIFIER)

        cls.parser = integrations_parser

        return integrations_parser

    @classmethod
    def integrations_error_handler(cls, message: str) -> None:
        """Handle integration command errors.

        Args:
            message: Error message

        """
        cls.parser.print_help()
        return fail(message, EXIT_INVALID_SUBCOMMAND)

    def handle(self, args):
        """Handle integration commands.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 for success, 1 for error)

        """
        if not self._is_authenticated():
            return fail("Not authenticated", EXIT_AUTH_ERROR)

        match args.integrations_command:
            case "list":
                return self.list_integrations()
            case "add":
                return self.add_integration(args.connector)
            case "remove":
                return self.remove_integration(args.connector, args.account)
            case "show":
                return self.show_integration(args.connector, args.identifier)
            case "select":
                return self.select_integration(args.connector, args.account)

    def list_integrations(self) -> int:
        """List all integrations (like the dashboard).

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            client_key = self.config.get_client_key()
            token = self.config.get_token()
            print_info("Loading connectors...")

            user_info = self.users_api_client.get_user_info(client_key, token)
            connectors = self.integrations_api_client.get_connectors(client_key)

            if not connectors:
                print_warning("No connectors available.")
                return succeed()

            connector_counts = {}
            for integration in user_info.integrations:
                connector_name = integration.get("connector")
                if connector_name:
                    connector_counts[connector_name] = connector_counts.get(connector_name, 0) + 1

            table_data = []
            for connector in connectors:
                count = connector_counts.get(connector, 0)
                table_data.append([connector, str(count)])

            print_header("Integrations List")
            print_info(f"User: {self.config.get_username()}")
            print_info(f"API URL: {self.config.get_api_url()}")
            print_table(headers=[CONNECTOR_FIELD, INTEGRATIONS_COUNT_FIELD], rows=table_data)

            return succeed()

        except CLIError as e:
            return fail(str(e), EXIT_REQUEST_ERROR)
        except Exception as e:
            return fail(f"Failed to list integrations: {str(e)}")

    def add_integration(self, connector: str) -> int:
        """Add a new integration.

        Args:
            connector: Connector name

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            client_key = self.config.get_client_key()
            token = self.config.get_token()

            print_info("Validating connector...")
            available_connectors = self.integrations_api_client.get_connectors(client_key)

            if connector not in available_connectors:
                print_info(f"Available connectors: {', '.join(available_connectors)}")
                return fail(f"Connector '{connector}' not found.", EXIT_REQUEST_ERROR)

            has_integration = self.integrations_api_client.check_integration_status(client_key, connector, token)
            if has_integration:
                print_warning(f"You already have an integration for '{connector}'.")
                if not confirm_action("Do you want to add another integration?"):
                    return succeed("Operation cancelled by user")

            print_info(f"Initiating OAuth flow for {connector}...")
            auth_url = self.integrations_api_client.initiate_integration(client_key, connector, token)

            print_success(f"OAuth flow initiated for {connector}!")
            print_info("Please visit the following URL to complete the integration:")
            print()
            print_info(f"  {auth_url}")
            print()
            print_info("After completing the OAuth flow, you can check your integrations with:")
            print_info("  bosa integrations")

            if confirm_action("Open URL in browser?"):
                try:
                    webbrowser.open(auth_url)
                    print_info("URL opened in browser.")
                except Exception:
                    print_warning("Failed to open browser. Please visit the URL manually.")

            return succeed("Integration initiated successfully")

        except CLIError as e:
            return fail(str(e), EXIT_REQUEST_ERROR)
        except Exception as e:
            return fail(f"Failed to add integration: {str(e)}")

    def remove_integration(self, connector: str, account: str) -> int:  # noqa: PLR0911
        """Remove an integration.

        Args:
            connector: Connector name
            account: Account identifier

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            client_key = self.config.get_client_key()
            token = self.config.get_token()

            user_info = self.users_api_client.get_user_info(client_key, token)

            target_integration = None
            for integration in user_info.integrations:
                if integration.get("connector") == connector and integration.get("user_identifier") == account:
                    target_integration = integration
                    break

            if not target_integration:
                self._show_available_integrations(user_info)
                return fail(f"Integration not found: {connector} with account {account}", EXIT_REQUEST_ERROR)

            print_warning("You are about to remove the integration:")
            print_info(f"  Connector: {connector}")
            print_info(f"  Account: {account}")
            print_info(f"  ID: {target_integration.get('id', 'N/A')}")
            print()

            if not confirm_action("Are you sure you want to remove this integration?"):
                print_info("Operation cancelled.")
                return succeed("Integration removal cancelled by user")

            print_info("Removing integration...")
            result = self.integrations_api_client.remove_integration(client_key, connector, account, token)

            if result.get("success", False):
                return succeed(f"Integration removed successfully: {connector} - {account}")
            else:
                return fail(
                    f"Failed to remove integration: {result.get('message', 'Unknown error')}", EXIT_REQUEST_ERROR
                )

        except CLIError as e:
            return fail(str(e), EXIT_REQUEST_ERROR)
        except Exception as e:
            return fail(f"Failed to remove integration: {str(e)}")

    def show_integration(self, connector: str, identifier: str = None) -> int:
        """Show integration details for a connector.

        Args:
            connector: Connector name
            identifier: Optional user identifier for specific integration

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            client_key = self.config.get_client_key()
            token = self.config.get_token()

            if identifier:
                return self._show_specific_integration(client_key, token, connector, identifier)

            return self._show_connector_integrations(client_key, token, connector)

        except CLIError as e:
            return fail(str(e), EXIT_REQUEST_ERROR)
        except Exception as e:
            return fail(f"Failed to show integration: {str(e)}")

    def select_integration(self, connector: str, account: str) -> int:  # noqa: PLR0911
        """Select or unselect an integration.

        Args:
            connector: Connector name
            account: Account identifier

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            if not self._is_authenticated():
                return fail("Not authenticated", EXIT_AUTH_ERROR)

            client_key = self.config.get_client_key()
            token = self.config.get_token()

            user_info = self.users_api_client.get_user_info(client_key, token)
            target_integration = None
            for integration in user_info.integrations:
                if integration.get("connector") == connector and integration.get("user_identifier") == account:
                    target_integration = integration
                    break

            if not target_integration:
                print_error(f"Integration not found: {connector} with account {account}")
                return self._show_available_integrations(user_info)

            current_selected = target_integration.get("selected", False)
            if current_selected:
                print_info(f"Integration {connector} - {account} is already selected")
                return succeed()

            print_info("Selecting integration...")
            result = self.integrations_api_client.set_selected_integration(client_key, connector, account, token, True)

            if result.get("success", False):
                return succeed(f"Integration selected successfully: {connector} - {account}")
            else:
                return fail(
                    f"Failed to select integration: {result.get('message', 'Unknown error')}", EXIT_REQUEST_ERROR
                )

        except CLIError as e:
            return fail(str(e), EXIT_REQUEST_ERROR)
        except Exception as e:
            return fail(f"Failed to selectintegration: {str(e)}")

    def _show_connector_integrations(self, client_key: str, token: str, connector: str) -> int:
        """Show all integrations for a connector.

        Args:
            client_key: Client API key
            token: User token
            connector: Connector name

        Returns:
            Exit code (0 for success, 1 for error)

        """
        user_info = self.users_api_client.get_user_info(client_key, token)

        connector_integrations = []
        for integration in user_info.integrations:
            if integration.get("connector") == connector:
                connector_integrations.append(integration)

        if not connector_integrations:
            self._show_available_integrations(user_info)
            return fail(f"No integrations found for connector: {connector}", EXIT_REQUEST_ERROR)

        print_header(f"Integrations for {connector}")
        print_info(f"Found {len(connector_integrations)} integration(s)")
        print()

        table_data = []
        for integration in connector_integrations:
            selected_status = "✓ Selected" if integration.get("selected", False) else "Not Selected"
            table_data.append(
                [
                    integration.get("user_identifier", "N/A"),
                    selected_status,
                ]
            )

        print_table(headers=[USER_IDENTIFIER_FIELD, "Status"], rows=table_data)

        return succeed()

    def _show_specific_integration(self, client_key: str, token: str, connector: str, identifier: str) -> int:
        """Show details for a specific integration.

        Args:
            client_key: Client API key
            token: User token
            connector: Connector name
            identifier: User identifier

        Returns:
            Exit code (0 for success, 1 for error)

        """
        try:
            integration_data = self.integrations_api_client.get_integration_details_by_identifier(
                client_key, connector, identifier, token
            )

            print_header(f"Account Details: {identifier}")
            auth_data = self._parse_auth_string(integration_data.auth_string)

            table_data = [
                ["Connector", integration_data.connector],
                ["User Identifier", integration_data.user_identifier],
                ["Selected", "Yes" if integration_data.selected else "No"],
                ["Auth Scopes", self._format_auth_scopes(integration_data.auth_scopes)],
            ]

            if isinstance(auth_data, dict):
                for key, value in auth_data.items():
                    table_data.append([f"{key.title()}", str(value)])
            else:
                display_value = str(auth_data) if auth_data else "N/A"
                table_data.append(["Auth String", display_value])

            print_table(headers=["Property", "Value"], rows=table_data)

            return succeed()

        except CLIError as e:
            return fail(str(e), EXIT_REQUEST_ERROR)
        except Exception as e:
            return fail(f"Failed to show integration: {str(e)}")

    def _show_available_integrations(self, user_info: BosaUser) -> int:
        """Show all available integrations.

        Args:
            user_info: User information

        Returns:
            Exit code (always 1 for error context)

        """
        print_header("Existing integrations:")
        print()
        table_data = []
        for integration in user_info.integrations:
            table_data.append([integration.get("connector"), integration.get("user_identifier")])
        print_table(headers=[CONNECTOR_FIELD, USER_IDENTIFIER_FIELD], rows=table_data)
        return EXIT_GENERAL_ERROR

    def _parse_auth_string(self, auth_string: str) -> Union[dict, str]:
        """Parse auth_string which can be a simple string or stringified JSON.

        Args:
            auth_string: The auth string from the integration

        Returns:
            Parsed data (dict if JSON, original string if not)

        """
        if not auth_string:
            return ""

        try:
            return json.loads(auth_string)
        except (json.JSONDecodeError, TypeError):
            return auth_string

    def _format_auth_scopes(self, auth_scopes) -> str:
        """Format auth_scopes for display, handling various edge cases.

        Args:
            auth_scopes: The auth_scopes from integration data

        Returns:
            Formatted string for display

        """
        if not auth_scopes:
            return "-"

        if isinstance(auth_scopes, list):
            valid_scopes = [scope for scope in auth_scopes if scope and scope.strip()]

            if not valid_scopes:
                return "-"

            return ", ".join(valid_scopes)

        if isinstance(auth_scopes, str):
            if not auth_scopes.strip():
                return "-"
            return auth_scopes

        return str(auth_scopes) if auth_scopes else "-"
