"""Tests for CLI utilities.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest

from bosa_cli.utils import (
    CLIError,
    confirm_action,
    format_connector_status,
    format_datetime,
    mask_string,
    mask_client_key,
    mask_token,
    print_error,
    print_header,
    print_info,
    print_success,
    print_table,
    print_warning,
    prompt_for_input,
)


class TestCLIError:
    """Test CLIError exception."""

    def test_cli_error_creation(self):
        """Test CLIError creation with message."""
        error = CLIError("Test error message")
        assert str(error) == "Test error message"

    def test_cli_error_with_data(self):
        """Test CLIError creation with additional data."""
        data = {"key": "value", "code": 404}
        error = CLIError("Test error", data)
        assert str(error) == "Test error"
        assert error.data == data

    def test_cli_error_inheritance(self):
        """Test CLIError inherits from Exception."""
        error = CLIError("Test error")
        assert isinstance(error, Exception)


class TestPrintFunctions:
    """Test print utility functions."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_success(self, mock_stdout):
        """Test print_success function."""
        print_success("Operation completed successfully")

        output = mock_stdout.getvalue()
        assert "✓" in output
        assert "Operation completed successfully" in output
        assert "\033[92m" in output  # Green color
        assert "\033[0m" in output  # Reset color

    @patch("sys.stderr", new_callable=StringIO)
    def test_print_error(self, mock_stderr):
        """Test print_error function."""
        print_error("An error occurred")

        output = mock_stderr.getvalue()
        assert "✗" in output
        assert "An error occurred" in output
        assert "\033[91m" in output  # Red color
        assert "\033[0m" in output  # Reset color

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_info(self, mock_stdout):
        """Test print_info function."""
        print_info("Information message")

        output = mock_stdout.getvalue()
        assert "ℹ" in output
        assert "Information message" in output
        assert "\033[94m" in output  # Blue color
        assert "\033[0m" in output  # Reset color

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_warning(self, mock_stdout):
        """Test print_warning function."""
        print_warning("Warning message")

        output = mock_stdout.getvalue()
        assert "⚠" in output
        assert "Warning message" in output
        assert "\033[93m" in output  # Yellow color
        assert "\033[0m" in output  # Reset color

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_header(self, mock_stdout):
        """Test print_header function."""
        print_header("Section Header")

        output = mock_stdout.getvalue()
        assert "Section Header" in output
        assert "=" in output  # Header separator
        assert "\033[1m" in output  # Bold
        assert "\033[0m" in output  # Reset


class TestTableFunctions:
    """Test table formatting functions."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_table_with_data(self, mock_stdout):
        """Test print_table with data."""
        headers = ["Name", "Age", "City"]
        rows = [["Alice", "25", "New York"], ["Bob", "30", "London"]]

        print_table(headers, rows)

        output = mock_stdout.getvalue()
        assert "Name" in output
        assert "Age" in output
        assert "City" in output
        assert "Alice" in output
        assert "Bob" in output
        assert "25" in output
        assert "30" in output
        assert "New York" in output
        assert "London" in output
        assert "|" in output  # Column separator
        assert "-" in output  # Row separator

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_table_empty_rows(self, mock_stdout):
        """Test print_table with empty rows."""
        headers = ["Name", "Age"]
        rows = []

        print_table(headers, rows)

        output = mock_stdout.getvalue()
        assert "No data to display." in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_table_with_title(self, mock_stdout):
        """Test print_table with title."""
        headers = ["Name", "Age"]
        rows = [["Alice", "25"]]

        print_table(headers, rows, "User List")

        output = mock_stdout.getvalue()
        assert "User List" in output
        assert "Name" in output
        assert "Alice" in output
        assert "\033[1m" in output  # Bold title
        assert "=" in output  # Title separator


class TestInputFunctions:
    """Test input utility functions."""

    @patch("builtins.input", return_value="test_input")
    def test_prompt_for_input_basic(self, mock_input):
        """Test basic prompt_for_input."""
        result = prompt_for_input("Enter value")

        assert result == "test_input"
        mock_input.assert_called_once_with("Enter value: ")

    @patch("builtins.input", return_value="")
    def test_prompt_for_input_with_default(self, mock_input):
        """Test prompt_for_input with default value."""
        result = prompt_for_input("Enter value", default="default_value")

        assert result == "default_value"
        mock_input.assert_called_once_with("Enter value [default_value]: ")

    @patch("builtins.input", return_value="")
    def test_prompt_for_input_required_empty(self, mock_input):
        """Test prompt_for_input with required=True and empty input."""
        with pytest.raises(CLIError, match="Input is required"):
            prompt_for_input("Enter value", required=True)

    @patch("builtins.input", return_value="")
    def test_prompt_for_input_not_required_empty(self, mock_input):
        """Test prompt_for_input with required=False and empty input."""
        result = prompt_for_input("Enter value", required=False)

        assert result == ""

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_prompt_for_input_keyboard_interrupt(self, mock_input):
        """Test prompt_for_input with keyboard interrupt."""
        with pytest.raises(CLIError, match="Operation cancelled by user"):
            prompt_for_input("Enter value")

    @patch("getpass.getpass", return_value="secret_password")
    def test_prompt_for_input_with_hide(self, mock_getpass):
        """Test prompt_for_input with hide=True (password input)."""
        result = prompt_for_input("Enter password", hide=True)

        assert result == "secret_password"
        mock_getpass.assert_called_once_with("Enter password: ")

    @patch("getpass.getpass", return_value="")
    def test_prompt_for_input_with_hide_and_default(self, mock_getpass):
        """Test prompt_for_input with hide=True and default value."""
        result = prompt_for_input("Enter password", default="default_pass", hide=True)

        assert result == "default_pass"
        mock_getpass.assert_called_once_with("Enter password [default_pass]: ")

    @patch("getpass.getpass", return_value="")
    def test_prompt_for_input_with_hide_required_empty(self, mock_getpass):
        """Test prompt_for_input with hide=True, required=True and empty input."""
        with pytest.raises(CLIError, match="Input is required"):
            prompt_for_input("Enter password", hide=True, required=True)

    @patch("getpass.getpass", side_effect=KeyboardInterrupt())
    def test_prompt_for_input_with_hide_keyboard_interrupt(self, mock_getpass):
        """Test prompt_for_input with hide=True and keyboard interrupt."""
        with pytest.raises(CLIError, match="Operation cancelled by user"):
            prompt_for_input("Enter password", hide=True)

    @patch("builtins.input", return_value="y")
    def test_confirm_action_yes(self, mock_input):
        """Test confirm_action with 'y' response."""
        result = confirm_action("Continue?")

        assert result is True
        mock_input.assert_called_once_with("Continue? [y/N]: ")

    @patch("builtins.input", return_value="Y")
    def test_confirm_action_yes_uppercase(self, mock_input):
        """Test confirm_action with 'Y' response."""
        result = confirm_action("Continue?")

        assert result is True

    @patch("builtins.input", return_value="yes")
    def test_confirm_action_yes_full(self, mock_input):
        """Test confirm_action with 'yes' response."""
        result = confirm_action("Continue?")

        assert result is True

    @patch("builtins.input", return_value="n")
    def test_confirm_action_no(self, mock_input):
        """Test confirm_action with 'n' response."""
        result = confirm_action("Continue?")

        assert result is False

    @patch("builtins.input", return_value="")
    def test_confirm_action_empty_default_false(self, mock_input):
        """Test confirm_action with empty response and default=False."""
        result = confirm_action("Continue?")

        assert result is False

    @patch("builtins.input", return_value="")
    def test_confirm_action_empty_default_true(self, mock_input):
        """Test confirm_action with empty response and default=True."""
        result = confirm_action("Continue?", default=True)

        assert result is True
        mock_input.assert_called_once_with("Continue? [Y/n]: ")

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_confirm_action_keyboard_interrupt(self, mock_input):
        """Test confirm_action with keyboard interrupt."""
        result = confirm_action("Continue?")

        assert result is False


class TestUtilityFunctions:
    """Test utility formatting functions."""

    def test_mask_string_short(self):
        """Test mask_api_key with short key."""
        api_key = "short"
        result = mask_string(api_key)
        assert result == "short"

    def test_mask_string_default_rear_only(self):
        """Test mask_api_key with default rear-only visibility."""
        api_key = "very-long-api-key-123456789"
        result = mask_string(api_key)
        assert result == "...6789"

    def test_mask_string_custom_rear(self):
        """Test mask_api_key with custom rear visibility."""
        api_key = "very-long-api-key-123456789"
        result = mask_string(api_key, visible_rear=6)
        assert result == "...456789"

    def test_mask_string_preserve_prefix(self):
        """Test mask_api_key with prefix preservation."""
        api_key = "sk-client-very-long-api-key-123456789"
        result = mask_string(api_key, preserve_prefix="sk-client-")
        assert result == "sk-client-...6789"

    def test_mask_string_preserve_prefix_custom_rear(self):
        """Test mask_api_key with prefix preservation and custom rear."""
        api_key = "sk-client-very-long-api-key-123456789"
        result = mask_string(api_key, visible_rear=6, preserve_prefix="sk-client-")
        assert result == "sk-client-...456789"

    def test_mask_string_front_and_rear(self):
        """Test mask_api_key with front and rear visibility."""
        api_key = "jwt.token.very.long.here"
        result = mask_string(api_key, visible_front=4, visible_rear=4)
        assert result == "jwt....here"

    def test_mask_string_front_only(self):
        """Test mask_api_key with front-only visibility."""
        api_key = "very-long-api-key-123456789"
        result = mask_string(api_key, visible_front=4, visible_rear=0)
        assert result == "very..."

    def test_mask_string_no_visibility(self):
        """Test mask_api_key with no visibility (fully masked)."""
        api_key = "very-long-api-key-123456789"
        result = mask_string(api_key, visible_front=0, visible_rear=0)
        assert result == "..."

    def test_mask_string_front_rear_too_long(self):
        """Test mask_api_key when front+rear would show everything."""
        api_key = "shortkey123"
        result = mask_string(api_key, visible_front=5, visible_rear=6, min_mask_length=10)
        assert result == "shortkey123"  # Would show everything, so return as-is

    def test_mask_string_preserve_prefix_no_match(self):
        """Test mask_api_key with prefix preservation but key doesn't match."""
        api_key = "different-prefix-long-key-123456789"
        result = mask_string(api_key, preserve_prefix="sk-client-")
        assert result == "...6789"  # Falls back to rear-only

    def test_mask_string_custom_min_length(self):
        """Test mask_api_key with custom minimum mask length."""
        api_key = "short123"
        result = mask_string(api_key, min_mask_length=5)
        assert result == "...t123"  # Long enough with custom min_length

    def test_mask_client_key(self):
        """Test mask_client_key convenience function."""
        api_key = "sk-client-abc123.def456.ghi789"
        result = mask_client_key(api_key)
        assert result == "sk-client-...i789"

    def test_mask_client_key_custom_rear(self):
        """Test mask_client_key with custom rear visibility."""
        api_key = "sk-client-abc123.def456.ghi789"
        result = mask_client_key(api_key, visible_rear=6)
        assert result == "sk-client-...ghi789"


    def test_mask_token(self):
        """Test mask_token convenience function."""
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        result = mask_token(token)
        assert result == "eyJ0...7HgQ"

    def test_mask_token_custom_visibility(self):
        """Test mask_token with custom front/rear visibility."""
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        result = mask_token(token, visible_front=6, visible_rear=6)
        assert result == "eyJ0eX...Fh7HgQ"

    def test_format_datetime(self):
        """Test format_datetime function."""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        result = format_datetime(dt)
        assert result == "2024-01-15 14:30:45"

    def test_format_connector_status_true(self):
        """Test format_connector_status with True (active)."""
        result = format_connector_status(True)
        assert "✓ Active" in result
        assert "\033[92m" in result  # Green color
        assert "\033[0m" in result  # Reset color

    def test_format_connector_status_false(self):
        """Test format_connector_status with False (inactive)."""
        result = format_connector_status(False)
        assert "✗ Inactive" in result
        assert "\033[91m" in result  # Red color
        assert "\033[0m" in result  # Reset color
