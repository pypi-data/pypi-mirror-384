"""Base API client for BOSA CLI.

Author:
    I Gusti Ngurah Gana Untaran (i.gusti.n.g.untaran@gdplabs.id)
"""

import json
from typing import Any, Dict, Optional

import requests

from bosa_cli.constants import HTTP_DELETE, HTTP_GET, HTTP_POST, HTTP_PUT
from bosa_cli.utils import CLIError


class BaseAPIClient:
    """Base API client with shared request functionality."""

    def __init__(self, base_url: str):
        """Initialize base API client.

        Args:
            base_url: BOSA API base URL

        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to BOSA API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            headers: Request headers
            data: Request body data
            params: URL parameters

        Returns:
            Response JSON data

        Raises:
            CLIError: If request fails

        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == HTTP_GET:
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == HTTP_POST:
                response = self.session.post(url, headers=headers, json=data, params=params)
            elif method.upper() == HTTP_DELETE:
                response = self.session.delete(url, headers=headers, params=params)
            elif method.upper() == HTTP_PUT:
                response = self.session.put(url, headers=headers, json=data, params=params)
            else:
                raise CLIError(f"Unsupported HTTP method: {method}")

            response_data = response.json()
            if not response.ok or ("success" in response_data and response_data["success"] is False):
                error_data = response_data.get("error", {})
                error_message = error_data.get("message", response.status_code)
                raise CLIError(f"API error: {error_message}")

            return response_data

        except requests.exceptions.ConnectionError as e:
            raise CLIError(f"Failed to connect to {self.base_url}: {str(e)}") from e
        except requests.exceptions.Timeout as e:
            raise CLIError(f"Request timeout: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise CLIError(f"Request failed: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise CLIError(f"Invalid JSON response from server: {str(e)}") from e
        except CLIError as e:
            raise e
        except Exception as e:
            raise CLIError(f"An unexpected error occurred: {str(e)}") from e
