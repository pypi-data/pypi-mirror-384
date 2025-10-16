"""Users API client for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

from bosa_cli.api.base import BaseAPIClient
from bosa_cli.api.models import BosaUser, CreatedBosaUser
from bosa_cli.constants import API_KEY_HEADER, AUTHORIZATION_HEADER, BEARER_PREFIX, HTTP_GET, HTTP_POST
from bosa_cli.utils import CLIError


class UsersAPIClient(BaseAPIClient):
    """Users API client."""

    def create_user(self, client_key: str, username: str) -> CreatedBosaUser:
        """Create a new user.

        Args:
            client_key: Client API key
            username: Username for the new user

        Returns:
            BosaUser: User creation response data

        Raises:
            CLIError: If user creation fails

        """
        headers = {
            API_KEY_HEADER: client_key,
        }

        data = {"identifier": username}

        try:
            response = self._make_request(HTTP_POST, "/clients/register-user", headers=headers, data=data)
            user_data = response.get("data", {})
            return CreatedBosaUser(**user_data)

        except Exception as e:
            raise CLIError(f"Failed to create user: {str(e)}") from e

    def get_user_info(self, client_key: str, token: str) -> BosaUser:
        """Get current user information.

        Args:
            client_key: Client API key
            token: User JWT token

        Returns:
            BosaUser: User information

        Raises:
            CLIError: If request fails

        """
        headers = {AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {token}", API_KEY_HEADER: client_key}

        try:
            response = self._make_request(HTTP_GET, "/clients/user", headers=headers)
            user_data = response.get("data", {})
            return BosaUser(**user_data)

        except Exception as e:
            raise CLIError(f"Failed to get user info: {str(e)}") from e
