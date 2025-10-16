"""Integrations API client for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

from typing import Any, Dict, List

from bosa_cli.api.base import BaseAPIClient
from bosa_cli.api.models import IntegrationDetail
from bosa_cli.constants import API_KEY_HEADER, AUTHORIZATION_HEADER, BEARER_PREFIX, HTTP_DELETE, HTTP_GET, HTTP_POST
from bosa_cli.utils import CLIError


class IntegrationsAPIClient(BaseAPIClient):
    """Integrations API client."""

    def get_connectors(self, client_key: str) -> List[str]:
        """Get all available connectors.

        Args:
            client_key: Client API key

        Returns:
            List of available connectors

        Raises:
            CLIError: If request fails

        """
        headers = {AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {client_key}"}

        try:
            response = self._make_request(HTTP_GET, "/connectors", headers=headers)

            return list(response.keys())

        except Exception as e:
            raise CLIError(f"Failed to get connectors: {str(e)}") from e

    def check_integration_status(self, client_key: str, connector_name: str, token: str) -> bool:
        """Check if integration exists for a connector.

        Args:
            client_key: Client API key
            connector_name: Name of the connector
            token: User JWT token

        Returns:
            Integration status information (True if integration exists, False otherwise)

        Raises:
            CLIError: If request fails

        """
        headers = {API_KEY_HEADER: client_key, AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {token}"}

        try:
            response = self._make_request(HTTP_GET, f"/connectors/{connector_name}/integration-exists", headers=headers)
            return response.get("data", {}).get("has_integration", False)

        except Exception as e:
            raise CLIError(f"Failed to check integration status: {str(e)}") from e

    def initiate_integration(self, client_key: str, connector_name: str, token: str) -> str:
        """Initiate OAuth integration for a connector.

        Args:
            client_key: Client API key
            connector_name: Name of the connector
            token: User JWT token

        Returns:
            str: Integration initiation response (contains OAuth URL)

        Raises:
            CLIError: If request fails

        """
        headers = {
            API_KEY_HEADER: client_key,
            AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {token}",
        }

        callback_url = f"{self.base_url}/connectors/{connector_name}/success-authorize-callback"

        data = {"callback_url": callback_url}

        try:
            response = self._make_request(
                HTTP_POST, f"/connectors/{connector_name}/integrations", headers=headers, data=data
            )

            if not response.get("data", {}).get("url"):
                raise CLIError("Failed to initiate integration.")

            return response.get("data", {}).get("url", "")

        except Exception as e:
            raise CLIError(f"Failed to initiate integration: {str(e)}") from e

    def remove_integration(
        self, client_key: str, connector_name: str, user_identifier: str, token: str
    ) -> Dict[str, Any]:
        """Remove integration for a connector and specific user identifier.

        Args:
            client_key: Client API key
            connector_name: Name of the connector
            user_identifier: User identifier to specify which integration to remove
            token: User JWT token

        Returns:
            Removal response

        Raises:
            CLIError: If request fails

        """
        headers = {API_KEY_HEADER: client_key, AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {token}"}

        try:
            response = self._make_request(
                HTTP_DELETE, f"/connectors/{connector_name}/integrations/{user_identifier}", headers=headers
            )
            return response.get("data", {})

        except Exception as e:
            raise CLIError(f"Failed to remove integration: {str(e)}") from e

    def get_integration_details_by_identifier(
        self, client_key: str, connector: str, user_identifier: str, token: str
    ) -> IntegrationDetail:
        """Get a specific integration by user identifier.

        Args:
            client_key: Client API key
            connector: Connector name
            user_identifier: The third-party service user identifier (e.g., GitHub username, Google email)
            token: User token

        Returns:
            Integration details including access token

        Raises:
            CLIError: If request fails or integration not found

        """
        headers = {API_KEY_HEADER: client_key, AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {token}"}

        try:
            response = self._make_request(
                HTTP_GET, f"/connectors/{connector}/integrations/{user_identifier}", headers=headers
            )
            data = response.get("data", {})
            if data.get("success") is False:
                raise CLIError({data.get("error", "Unknown error")})

            return IntegrationDetail(**response.get("data", {}))

        except Exception as e:
            raise CLIError(f"Failed to get integration for {user_identifier} in {connector}: {str(e)}") from e

    def set_selected_integration(
        self, client_key: str, connector_name: str, user_identifier: str, token: str
    ) -> Dict[str, Any]:
        """Set integration as selected/unselected.

        Args:
            client_key: Client API key
            connector_name: Name of the connector
            user_identifier: User identifier for the integration
            token: User JWT token

        Returns:
            Update response

        Raises:
            CLIError: If request fails

        """
        headers = {API_KEY_HEADER: client_key, AUTHORIZATION_HEADER: f"{BEARER_PREFIX} {token}"}
        data = {"selected": True}

        try:
            response = self._make_request(
                HTTP_POST, f"/connectors/{connector_name}/integrations/{user_identifier}", headers=headers, data=data
            )
            return response.get("data", {})

        except Exception as e:
            raise CLIError(f"Failed to update integration selection: {str(e)}") from e
