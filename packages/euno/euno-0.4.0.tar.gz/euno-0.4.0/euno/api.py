"""
API client for communicating with the Euno backend.

This module handles HTTP requests to the Euno API endpoints.
"""

import requests
from typing import Dict, Any, List, Optional
from .config import config


class EunoAPIClient:
    """Client for making requests to the Euno API."""

    def __init__(self, backend_url: Optional[str] = None):
        self.backend_url = backend_url or config.get_backend_url()
        self.session = requests.Session()

    def _get_headers(self, token: str) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "euno-sdk/0.4.0",
        }

    def search_resources(self, token: str, account_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search resources in the Euno data model.

        Args:
            token (str): The Euno API token.
            account_id (str): The account ID to search in.
            params (Dict[str, Any]): Search parameters including eql, properties,
                pagination, etc.

        Returns:
            Dict[str, Any]: Search results with resources and count.

        Raises:
            requests.exceptions.HTTPError: If the token is invalid or an API error
                occurs.
        """
        headers = self._get_headers(token)
        response = self.session.get(
            f"{self.backend_url}/v1/accounts/{account_id}/data_model/list",
            headers=headers,
            params=params,
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # type: ignore

    def get_account_permissions(self, token: str, account_id: str) -> Dict[str, Any]:
        """
        Get account permissions for the given account ID.

        Args:
            token (str): The Euno API token.
            account_id (str): The account ID to check permissions for.

        Returns:
            Dict[str, Any]: Account permissions information.

        Raises:
            requests.exceptions.HTTPError: If the token is invalid or an API error
                occurs.
        """
        headers = self._get_headers(token)
        response = self.session.get(f"{self.backend_url}/v1/accounts/{account_id}/permissions", headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # type: ignore

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a token by making a request to the /user endpoint.

        Args:
            token: The API token to validate

        Returns:
            User information if token is valid

        Raises:
            requests.HTTPError: If the token is invalid or request fails
        """
        url = f"{self.backend_url}/v1/user"
        headers = self._get_headers(token)

        response = self.session.get(url, headers=headers)
        response.raise_for_status()

        return response.json()  # type: ignore

    def get_user(self, token: str) -> Dict[str, Any]:
        """
        Get current user information.

        Args:
            token: The API token

        Returns:
            User information

        Raises:
            requests.HTTPError: If the request fails
        """
        return self.validate_token(token)

    def list_metadata_tags(self, token: str, account_id: str) -> List[Dict[str, Any]]:
        """
        List metadata tags (custom properties) for the given account.

        Args:
            token (str): The Euno API token.
            account_id (str): The account ID to list metadata tags for.

        Returns:
            List[Dict[str, Any]]: List of metadata tags.

        Raises:
            requests.exceptions.HTTPError: If the token is invalid or an API error
                occurs.
        """
        headers = self._get_headers(token)
        response = self.session.get(f"{self.backend_url}/v1/accounts/{account_id}/metadata_tags", headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # type: ignore

    def set_metadata_tag_value(self, token: str, account_id: str, cp_id: int, value_updates: list) -> Dict[str, Any]:
        """
        Set values for a metadata tag (custom property).

        Args:
            token (str): The Euno API token.
            account_id (str): The account ID.
            cp_id (int): The custom property ID.
            value_updates (list): List of value updates to apply.

        Returns:
            Dict[str, Any]: Response from the API.

        Raises:
            requests.exceptions.HTTPError: If the token is invalid or an API error
                occurs.
        """
        headers = self._get_headers(token)
        response = self.session.post(
            f"{self.backend_url}/v1/accounts/{account_id}/metadata_tags/{cp_id}/values",
            headers=headers,
            json=value_updates,
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # type: ignore


# Global API client instance
api_client = EunoAPIClient()
