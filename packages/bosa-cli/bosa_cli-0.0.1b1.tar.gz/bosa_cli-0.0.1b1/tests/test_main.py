"""Tests for main CLI entry point.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""
import pytest
from argparse import ArgumentParser
from unittest.mock import Mock, patch

from bosa_cli.commands.auth import AuthCommands
from bosa_cli.commands.integrations import IntegrationsCommands
from bosa_cli.commands.users import UsersCommands
from bosa_cli.main import create_parser, discover_commands, main
from bosa_cli.constants import EXIT_INVALID_SUBCOMMAND, EXIT_GENERAL_ERROR, EXIT_SUCCESS


class TestMainCLI:
    """Test main CLI functionality."""

    def test_discover_commands(self):
        """Test command discovery with explicit registration."""
        commands = discover_commands()

        assert "auth" in commands
        assert "integrations" in commands
        assert "users" in commands

        assert commands["auth"] == AuthCommands
        assert commands["integrations"] == IntegrationsCommands
        assert commands["users"] == UsersCommands

    @patch("bosa_cli.main.discover_commands")
    def test_create_parser(self, mock_discover_commands):
        """Test parser creation returns tuple."""
        mock_commands = {"auth": AuthCommands, "integrations": IntegrationsCommands, "users": UsersCommands}
        mock_discover_commands.return_value = mock_commands

        parser, commands = create_parser()

        assert isinstance(parser, ArgumentParser)
        assert parser.prog == "bosa"
        assert commands == mock_commands
        mock_discover_commands.assert_called_once()

    @patch("bosa_cli.main.create_parser")
    def test_main_no_command(self, mock_create_parser):
        """Test main with no command specified."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = None
        mock_parser.parse_args.return_value = mock_args
        mock_parser.print_help.return_value = None

        mock_create_parser.return_value = (mock_parser, {})

        result = main()

        assert result == EXIT_INVALID_SUBCOMMAND
        mock_parser.print_help.assert_called_once()

    @patch("bosa_cli.main.create_parser")
    def test_main_invalid_command(self, mock_create_parser):
        """Test main with invalid command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "invalid"
        mock_parser.parse_args.return_value = mock_args
        mock_parser.print_help.return_value = None

        available_commands = {"auth": AuthCommands, "integrations": IntegrationsCommands, "users": UsersCommands}
        mock_create_parser.return_value = (mock_parser, available_commands)

        result = main()

        assert result == EXIT_INVALID_SUBCOMMAND
        mock_parser.print_help.assert_called_once()

    @patch("bosa_cli.main.create_parser")
    @patch("bosa_cli.main.CLIConfig")
    def test_main_auth_command(self, mock_config_class, mock_create_parser):
        """Test main with auth command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "auth"
        mock_parser.parse_args.return_value = mock_args

        available_commands = {"auth": AuthCommands, "integrations": IntegrationsCommands, "users": UsersCommands}
        mock_create_parser.return_value = (mock_parser, available_commands)

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with patch.object(AuthCommands, "handle") as mock_handle:
            mock_handle.return_value = 0

            result = main()

            assert result == EXIT_SUCCESS
            mock_handle.assert_called_once_with(mock_args)
            mock_config_class.assert_called_once()

    @patch("bosa_cli.main.create_parser")
    @patch("bosa_cli.main.CLIConfig")
    def test_main_integrations_command(self, mock_config_class, mock_create_parser):
        """Test main with integrations command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "integrations"
        mock_parser.parse_args.return_value = mock_args

        available_commands = {"auth": AuthCommands, "integrations": IntegrationsCommands, "users": UsersCommands}
        mock_create_parser.return_value = (mock_parser, available_commands)

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with patch.object(IntegrationsCommands, "handle") as mock_handle:
            mock_handle.return_value = 0

            result = main()

            assert result == EXIT_SUCCESS
            mock_handle.assert_called_once_with(mock_args)
            mock_config_class.assert_called_once()

    @patch("bosa_cli.main.create_parser")
    @patch("bosa_cli.main.CLIConfig")
    def test_main_users_command(self, mock_config_class, mock_create_parser):
        """Test main with users command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "users"
        mock_parser.parse_args.return_value = mock_args

        available_commands = {"auth": AuthCommands, "integrations": IntegrationsCommands, "users": UsersCommands}
        mock_create_parser.return_value = (mock_parser, available_commands)

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with patch.object(UsersCommands, "handle") as mock_handle:
            mock_handle.return_value = 0

            result = main()

            assert result == EXIT_SUCCESS
            mock_handle.assert_called_once_with(mock_args)
            mock_config_class.assert_called_once()

    @patch("bosa_cli.main.create_parser")
    @patch("bosa_cli.main.CLIConfig")
    def test_main_keyboard_interrupt(self, mock_config_class, mock_create_parser):
        """Test main with keyboard interrupt."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "auth"
        mock_parser.parse_args.return_value = mock_args

        available_commands = {"auth": AuthCommands}
        mock_create_parser.return_value = (mock_parser, available_commands)

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with patch.object(AuthCommands, "handle") as mock_handle:
            mock_handle.side_effect = KeyboardInterrupt()

            result = main()

            assert result == EXIT_GENERAL_ERROR

    @patch("bosa_cli.main.create_parser")
    @patch("bosa_cli.main.CLIConfig")
    @patch("bosa_cli.main.print_error")
    def test_main_unexpected_error(self, mock_print_error, mock_config_class, mock_create_parser):
        """Test main with unexpected error."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "auth"
        mock_parser.parse_args.return_value = mock_args

        available_commands = {"auth": AuthCommands}
        mock_create_parser.return_value = (mock_parser, available_commands)

        mock_config = Mock()
        mock_config_class.return_value = mock_config

        with patch.object(AuthCommands, "handle") as mock_handle:
            mock_handle.side_effect = Exception("Test error")

            result = main()

            assert result == EXIT_GENERAL_ERROR

    @patch("bosa_cli.main.import_module")
    def test_discover_commands_import_error(self, mock_import_module):
        """Test command discovery fails fast on import errors."""
        mock_import_module.side_effect = ImportError("Module not found")

        with patch("bosa_cli.main.print_error") as mock_print_error:
            with pytest.raises(SystemExit) as exc_info:
                discover_commands()

            assert exc_info.value.code == EXIT_GENERAL_ERROR
            mock_print_error.assert_called_once_with("Failed to import command module 'auth': Module not found")
