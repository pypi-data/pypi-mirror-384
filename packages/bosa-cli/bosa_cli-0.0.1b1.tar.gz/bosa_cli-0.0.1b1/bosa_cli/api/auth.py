"""Authentication API client for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

from bosa_cli.api.base import BaseAPIClient
from bosa_cli.api.models import BosaToken
from bosa_cli.constants import API_KEY_HEADER, HTTP_POST
from bosa_cli.utils import CLIError


class AuthAPIClient(BaseAPIClient):
    """Authentication API client."""

    def authenticate_user(self, client_key: str, identifier: str, secret: str) -> BosaToken:
        """Authenticate user and get JWT token.

        Args:
            client_key: Client API key
            identifier: User identifier
            secret: User secret

        Returns:
            Authentication token information

        Raises:
            CLIError: If authentication fails

        """
        headers = {
            API_KEY_HEADER: client_key,
        }

        data = {"identifier": identifier, "secret": secret}

        try:
            response = self._make_request(HTTP_POST, "/clients/oauth-token", headers=headers, data=data)
            token_data = response.get("data", None)

            if not token_data:
                raise CLIError("Authentication error. Please check your credentials and try again.")

            return BosaToken(**token_data)

        except Exception as e:
            raise CLIError(str(e)) from e
