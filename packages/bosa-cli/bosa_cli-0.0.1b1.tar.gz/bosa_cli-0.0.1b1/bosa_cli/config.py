"""Configuration management for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import json
import os
import stat
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from bosa_cli.constants import AUTH_NOT_AUTHENTICATED, DEFAULT_API_URL
from bosa_cli.utils import CLIError


@dataclass
class CLISession:
    """CLI authentication session storage."""

    client_api_key: str
    api_url: str
    username: str
    token: str
    token_type: str
    expires_at: str
    user_id: str
    is_revoked: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CLISession":
        """Create from dictionary."""
        return cls(**data)


class CLIConfig:
    """Configuration management for BOSA CLI."""

    DEFAULT_CONFIG_DIR = Path.home() / ".bosa"
    DEFAULT_CONFIG_FILE = "config.json"

    def __init__(self):
        """Initialize CLI configuration."""
        self.config_path = self.DEFAULT_CONFIG_DIR / self.DEFAULT_CONFIG_FILE
        self.config_dir = self.config_path.parent
        self._session: Optional[CLISession] = None

        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._load_config()

        # Use stored session URL or default
        if self._session:
            self.api_url = self._session.api_url
        else:
            self.api_url = DEFAULT_API_URL

    def save_session(  # noqa: PLR0913
        self,
        client_api_key: str,
        api_url: str,
        username: str,
        token: str,
        token_type: str,
        expires_at: str,
        user_id: str,
        is_revoked: bool,
    ) -> None:
        """Save authentication session.

        Args:
            client_api_key: Client API key
            api_url: BOSA API base URL
            username: User identifier
            token: JWT token
            token_type: Token type (usually "Bearer")
            expires_at: Token expiration time
            user_id: User ID
            is_revoked: Is revoked

        """
        self._session = CLISession(
            client_api_key=client_api_key,
            api_url=api_url,
            username=username,
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            user_id=user_id,
            is_revoked=is_revoked,
        )
        self._save_config()

    def get_session(self) -> Optional[CLISession]:
        """Get stored session.

        Returns:
            Stored session or None if not found

        """
        return self._session

    def clear_session(self) -> None:
        """Clear stored session."""
        self._session = None
        self._save_config()

    def is_authenticated(self) -> bool:
        """Check if user is authenticated.

        Returns:
            True if session is stored

        """
        return self._session is not None

    def get_client_key(self) -> str:
        """Get client API key.

        Returns:
            Client API key

        Raises:
            CLIError: If not authenticated

        """
        if not self._session:
            raise CLIError(AUTH_NOT_AUTHENTICATED)
        return self._session.client_api_key

    def get_username(self) -> str:
        """Get username.

        Returns:
            Username

        Raises:
            CLIError: If not authenticated

        """
        if not self._session:
            raise CLIError(AUTH_NOT_AUTHENTICATED)
        return self._session.username

    def get_token(self) -> str:
        """Get JWT token.

        Returns:
            JWT token

        Raises:
            CLIError: If not authenticated

        """
        if not self._session:
            raise CLIError(AUTH_NOT_AUTHENTICATED)
        return self._session.token

    def get_api_url(self) -> str:
        """Get API URL.

        Returns:
            API base URL (uses stored session URL or default)

        """
        return self.api_url

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            if data:
                self._session = CLISession.from_dict(data)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise CLIError(f"Invalid configuration file: {e}") from e

    def _save_config(self) -> None:
        """Save configuration to file."""
        data = {}

        if self._session:
            data = self._session.to_dict()

        # VALIDATE JSON FIRST BEFORE SAVING
        try:
            json_string = json.dumps(data, indent=2)
            json.loads(json_string)
        except (json.JSONDecodeError, TypeError) as e:
            raise CLIError(f"Invalid data cannot be serialized to JSON: {e}") from e

        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            dir_path = os.path.dirname(self.config_path)

            with tempfile.NamedTemporaryFile(mode="w", dir=dir_path, delete=False, suffix=".tmp") as tmp_file:
                json.dump(data, tmp_file, indent=2)
                temp_path = tmp_file.name

            if sys.platform.startswith("win"):
                # Windows permissions
                os.chmod(temp_path, stat.S_IREAD | stat.S_IWRITE)
            else:
                # Unix/Linux/macOS permissions (restrictive)
                os.chmod(temp_path, 0o600)

            os.replace(temp_path, self.config_path)

        except (OSError, IOError) as e:
            raise CLIError(f"Failed to save configuration: {e}") from e
