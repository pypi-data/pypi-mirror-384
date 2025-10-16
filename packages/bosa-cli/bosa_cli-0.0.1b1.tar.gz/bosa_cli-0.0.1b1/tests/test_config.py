"""Tests for CLIConfig.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import json
import stat
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from bosa_cli.config import CLIConfig, CLISession
from bosa_cli.constants import DEFAULT_API_URL
from bosa_cli.utils import CLIError


class TestCLISession:
    """Test CLISession dataclass."""

    def test_cli_session_creation(self):
        """Test CLISession creation with all fields."""
        session = CLISession(
            client_api_key="sk-client-test123",
            api_url="https://api.test.com",
            username="test_user",
            token="jwt.test.token",
            token_type="Bearer",
            expires_at="2024-12-31T23:59:59",
            user_id="user123",
            is_revoked=False,
        )

        assert session.client_api_key == "sk-client-test123"
        assert session.api_url == "https://api.test.com"
        assert session.username == "test_user"
        assert session.token == "jwt.test.token"
        assert session.token_type == "Bearer"
        assert session.expires_at == "2024-12-31T23:59:59"
        assert session.user_id == "user123"
        assert session.is_revoked is False

    def test_to_dict(self):
        """Test converting session to dictionary."""
        session = CLISession(
            client_api_key="sk-client-test123",
            api_url="https://api.test.com",
            username="test_user",
            token="jwt.test.token",
            token_type="Bearer",
            expires_at="2024-12-31T23:59:59",
            user_id="user123",
            is_revoked=False,
        )

        result = session.to_dict()

        assert result["client_api_key"] == "sk-client-test123"
        assert result["api_url"] == "https://api.test.com"
        assert result["username"] == "test_user"
        assert result["token"] == "jwt.test.token"

    def test_from_dict(self):
        """Test creating session from dictionary."""
        data = {
            "client_api_key": "sk-client-test123",
            "api_url": "https://api.test.com",
            "username": "test_user",
            "token": "jwt.test.token",
            "token_type": "Bearer",
            "expires_at": "2024-12-31T23:59:59",
            "user_id": "user123",
            "is_revoked": False,
        }

        session = CLISession.from_dict(data)

        assert session.client_api_key == "sk-client-test123"
        assert session.api_url == "https://api.test.com"
        assert session.username == "test_user"
        assert session.token == "jwt.test.token"


class TestCLIConfig:
    """Test CLIConfig class."""

    def test_init_no_existing_config(self):
        """Test CLIConfig initialization with no existing config."""
        with patch("pathlib.Path.mkdir") as mock_mkdir, patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            assert config.config_path == Path.home() / ".bosa" / "config.json"
            assert config.config_dir == Path.home() / ".bosa"
            assert config._session is None
            assert config.api_url == DEFAULT_API_URL
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_init_with_existing_config(self):
        """Test CLIConfig initialization with existing config."""
        config_dict = {
            "client_api_key": "sk-client-test123",
            "api_url": "https://api.test.com",
            "username": "test_user",
            "token": "jwt.test.token",
            "token_type": "Bearer",
            "expires_at": "2024-12-31T23:59:59",
            "user_id": "user123",
            "is_revoked": False,
        }
        config_data = json.dumps(config_dict)

        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=config_data)),
        ):
            config = CLIConfig()

            assert config._session is not None
            assert config._session.client_api_key == "sk-client-test123"
            assert config.api_url == "https://api.test.com"

    def test_init_with_invalid_config(self):
        """Test CLIConfig initialization with invalid config file."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="invalid json")),
        ):
            with pytest.raises(CLIError, match="Invalid configuration file"):
                CLIConfig()

    def test_save_session(self):
        """Test saving session data."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("os.makedirs") as mock_makedirs,
            patch("os.chmod") as mock_chmod,
            patch("os.replace") as mock_replace,
            patch("json.dump") as mock_json_dump,
            patch("json.dumps", return_value='{"test": "data"}') as _,
            patch("json.loads") as _,
        ):
            # Setup temp file mock
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.tmp"

            config = CLIConfig()

            config.save_session(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )

            assert config._session is not None
            assert config._session.client_api_key == "sk-client-test123"
            mock_makedirs.assert_called_once()
            mock_temp_file.assert_called_once()
            mock_json_dump.assert_called_once()
            mock_chmod.assert_called_once()
            mock_replace.assert_called_once()

    def test_save_session_os_error(self):
        """Test save_session with OSError during file operations."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("tempfile.NamedTemporaryFile") as _,
            patch("os.makedirs", side_effect=OSError("Permission denied")),
            patch("json.dumps", return_value='{"test": "data"}'),
            patch("json.loads"),
        ):
            config = CLIConfig()

            with pytest.raises(CLIError, match="Failed to save configuration:"):
                config.save_session(
                    client_api_key="sk-client-test123",
                    api_url="https://api.test.com",
                    username="test_user",
                    token="jwt.test.token",
                    token_type="Bearer",
                    expires_at="2024-12-31T23:59:59",
                    user_id="user123",
                    is_revoked=False,
                )

    def test_save_session_windows_permissions(self):
        """Test save_session with Windows permissions (covers line 215)."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("os.makedirs") as mock_makedirs,
            patch("os.chmod") as mock_chmod,
            patch("os.replace") as mock_replace,
            patch("json.dump") as mock_json_dump,
            patch("json.dumps", return_value='{"test": "data"}') as _,
            patch("json.loads") as _,
            patch("sys.platform", "win32"),  # Mock Windows platform
        ):
            # Setup temp file mock
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.tmp"

            config = CLIConfig()

            config.save_session(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )

            # Verify Windows permissions were set (line 215)
            mock_chmod.assert_called_with("/tmp/test.tmp", stat.S_IREAD | stat.S_IWRITE)
            mock_makedirs.assert_called_once()
            mock_temp_file.assert_called_once()
            mock_json_dump.assert_called_once()
            mock_replace.assert_called_once()

    def test_save_session_json_validation_error(self):
        """Test save_session with JSON serialization error."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("json.dumps", side_effect=TypeError("Object not serializable")),
        ):
            config = CLIConfig()

            with pytest.raises(CLIError, match="Invalid data cannot be serialized to JSON"):
                config.save_session(
                    client_api_key="sk-client-test123",
                    api_url="https://api.test.com",
                    username="test_user",
                    token="jwt.test.token",
                    token_type="Bearer",
                    expires_at="2024-12-31T23:59:59",
                    user_id="user123",
                    is_revoked=False,
                )

    def test_get_session(self):
        """Test getting session."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            assert config.get_session() is None

            session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )
            config._session = session

            assert config.get_session() == session

    def test_clear_session(self):
        """Test clearing session."""
        with (
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.exists", return_value=False),
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("os.makedirs") as _,
            patch("os.chmod") as _,
            patch("os.replace") as mock_replace,
            patch("json.dump") as mock_json_dump,
            patch("json.dumps", return_value="{}") as _,
            patch("json.loads") as _,
        ):
            # Setup temp file mock
            mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.tmp"

            config = CLIConfig()

            config._session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )

            config.clear_session()

            assert config._session is None
            mock_temp_file.assert_called_once()
            mock_json_dump.assert_called_once()
            mock_replace.assert_called_once()

    def test_is_authenticated(self):
        """Test authentication check."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            assert config.is_authenticated() is False

            config._session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )
            assert config.is_authenticated() is True

    def test_get_client_key(self):
        """Test getting client API key."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            with pytest.raises(CLIError, match="Not authenticated"):
                config.get_client_key()

            config._session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )
            assert config.get_client_key() == "sk-client-test123"

    def test_get_username(self):
        """Test getting username."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            with pytest.raises(CLIError, match="Not authenticated"):
                config.get_username()

            config._session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )
            assert config.get_username() == "test_user"

    def test_get_token(self):
        """Test getting JWT token."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            with pytest.raises(CLIError, match="Not authenticated"):
                config.get_token()

            config._session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )
            assert config.get_token() == "jwt.test.token"

    def test_get_api_url(self):
        """Test getting API URL."""
        with patch("pathlib.Path.mkdir"), patch("pathlib.Path.exists", return_value=False):
            config = CLIConfig()

            assert config.get_api_url() == DEFAULT_API_URL

            config._session = CLISession(
                client_api_key="sk-client-test123",
                api_url="https://api.test.com",
                username="test_user",
                token="jwt.test.token",
                token_type="Bearer",
                expires_at="2024-12-31T23:59:59",
                user_id="user123",
                is_revoked=False,
            )
            config.api_url = "https://api.test.com"
            assert config.get_api_url() == "https://api.test.com"
