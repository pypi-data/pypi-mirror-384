"""Utility functions for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import getpass
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from bosa_cli.constants import EXIT_GENERAL_ERROR, EXIT_SUCCESS


# ANSI Color Constants
class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"  # Success messages
    RED = "\033[91m"  # Error messages
    YELLOW = "\033[93m"  # Warning messages
    BLUE = "\033[94m"  # Info messages
    BOLD = "\033[1m"  # Bold text
    RESET = "\033[0m"  # Reset to default


class CLIError(Exception):
    """Custom exception for CLI errors."""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Initialize CLIError.

        Args:
            message: Error message
            data: Optional error data

        """
        super().__init__(message)
        self.data = data


def print_success(message: str) -> None:
    """Print success message in green.

    Args:
        message: Success message to print

    """
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print error message in red.

    Args:
        message: Error message to print

    """
    print(f"{Colors.RED}✗ {message}{Colors.RESET}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message in yellow.

    Args:
        message: Warning message to print

    """
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print info message in blue.

    Args:
        message: Info message to print

    """
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_header(title: str) -> None:
    """Print section header.

    Args:
        title: Header title

    """
    print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
    print("=" * len(title))


def print_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> None:
    """Print a formatted table.

    Args:
        headers: Table headers
        rows: Table rows
        title: Optional table title

    """
    if title:
        print_header(title)

    if not rows:
        print("No data to display.")
        return

    # Calculate column widths
    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    # Print header
    header_row = " | ".join(f"{header:<{widths[i]}}" for i, header in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))

    # Print rows
    for row in rows:
        row_str = " | ".join(f"{str(cell):<{widths[i]}}" for i, cell in enumerate(row))
        print(row_str)


def prompt_for_input(prompt: str, default: Optional[str] = None, hide: bool = False, required: bool = True) -> str:
    """Prompt user for input.

    Args:
        prompt (str): Input prompt
        default (Optional[str]): Default value
        hide (bool): Whether to hide input
        required (bool): Whether input is required

    Returns:
        str: User input

    Raises:
        CLIError: If required input is not provided

    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    try:
        if hide:
            value = getpass.getpass(full_prompt).strip()
        else:
            value = input(full_prompt).strip()

        if not value and default:
            return default

        if not value and required:
            raise CLIError("Input is required")

        return value

    except KeyboardInterrupt as e:
        raise CLIError("Operation cancelled by user") from e


def confirm_action(message: str, default: bool = False) -> bool:
    """Confirm user action.

    Args:
        message: Confirmation message
        default: Default response

    Returns:
        True if user confirms

    """
    suffix = " [Y/n]" if default else " [y/N]"

    try:
        response = input(f"{message}{suffix}: ").strip().lower()

        if not response:
            return default

        return response in ["y", "yes"]

    except KeyboardInterrupt:
        return False


def mask_string(  # noqa: PLR0911
    api_key: str, visible_rear: int = 4, visible_front: int = 0, preserve_prefix: str = None, min_mask_length: int = 12
) -> str:
    """Mask API key for display with flexible front/rear visibility.

    Args:
        api_key: API key to mask
        visible_rear: Number of characters to show at the end (default: 4)
        visible_front: Number of characters to show at the front (default: 0)
        preserve_prefix: If provided, preserve this prefix if key starts with it (e.g., "sk-client-")
        min_mask_length: Minimum length before masking is applied (default: 12)

    Returns:
        Masked API key in various formats:
        - With prefix: "sk-client-...XXXX"
        - Front+rear: "XXXX...YYYY"
        - Rear only: "...XXXX"

    Examples:
        mask_api_key("sk-client-abc123def456", preserve_prefix="sk-client-") -> "sk-client-...f456"
        mask_api_key("jwt.token.here", visible_front=4, visible_rear=4) -> "jwt....here"
        mask_api_key("longtoken123456", visible_rear=4) -> "...3456"

    """
    if len(api_key) <= min_mask_length:
        return api_key

    if preserve_prefix and api_key.startswith(preserve_prefix):
        suffix = api_key[-visible_rear:] if visible_rear > 0 else ""
        return f"{preserve_prefix}...{suffix}"

    # Front + rear
    if visible_front > 0 and visible_rear > 0:
        if visible_front + visible_rear >= len(api_key):
            return api_key  # Would show everything anyway
        front = api_key[:visible_front]
        rear = api_key[-visible_rear:]
        return f"{front}...{rear}"

    # Front only visibility
    if visible_front > 0 and visible_rear == 0:
        front = api_key[:visible_front]
        return f"{front}..."

    # Rear only visibility (default behavior)
    if visible_rear > 0:
        rear = api_key[-visible_rear:]
        return f"...{rear}"

    # No visibility (fully masked)
    return "..."


def mask_client_key(api_key: str, visible_rear: int = 4) -> str:
    """Mask BOSA client keys (sk-client-...).

    Args:
        api_key: Client key to mask
        visible_rear: Number of characters to show at the end

    Returns:
        Masked key in format: sk-client-...XXXX

    """
    return mask_string(api_key, visible_rear=visible_rear, preserve_prefix="sk-client-")


def mask_token(token: str, visible_front: int = 4, visible_rear: int = 4) -> str:
    """Mask JWT tokens showing front and rear.

    Args:
        token: JWT token to mask
        visible_front: Number of characters to show at the front
        visible_rear: Number of characters to show at the rear

    Returns:
        Masked token in format: XXXX...YYYY

    """
    return mask_string(token, visible_front=visible_front, visible_rear=visible_rear, min_mask_length=10)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display.

    Args:
        dt: Datetime to format

    Returns:
        Formatted datetime string

    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_connector_status(has_integration: bool) -> str:
    """Format connector status for display.

    Args:
        has_integration: Whether connector has integration

    Returns:
        Formatted status string

    """
    if has_integration:
        return f"{Colors.GREEN}✓ Active{Colors.RESET}"
    else:
        return f"{Colors.RED}✗ Inactive{Colors.RESET}"


def fail(message: str, exit_code: int = EXIT_GENERAL_ERROR) -> int:
    """Print error and return with specified code.

    Args:
        message: Error message to display
        exit_code: Exit code to use (auto-detects if None)

    """
    print_error(message)
    return exit_code


def succeed(message: Optional[str] = None) -> int:
    """Print success message and return with code 0.

    Args:
        message: Optional success message to display

    """
    if message:
        print_success(message)
    return EXIT_SUCCESS
