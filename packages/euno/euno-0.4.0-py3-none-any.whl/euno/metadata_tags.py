"""
Metadata tags (custom properties) functionality for the Euno SDK.

This module provides functions for listing and managing metadata tags.
"""

from typing import Dict, Any, List
from .config import config
from .api import api_client


def list_metadata_tags() -> List[Dict[str, Any]]:
    """
    List all metadata tags (custom properties) for the configured account.

    Returns:
        List[Dict[str, Any]]: List of metadata tags with their properties.

    Raises:
        ValueError: If not configured with token and account_id.
        requests.exceptions.HTTPError: If the API request fails.
    """
    token = config.get_token()
    account_id = config.get_account_id()

    if not token:
        raise ValueError("No API token configured. Run 'euno init' first.")
    if not account_id:
        raise ValueError("No account ID configured. Run 'euno init' first.")

    response = api_client.list_metadata_tags(token, account_id)
    return response


def set_metadata_tag_value(cp_id: int, value_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Set values for a metadata tag (custom property).

    Args:
        cp_id (int): The custom property ID.
        value_updates (List[Dict[str, Any]]): List of value updates to apply.

    Returns:
        Dict[str, Any]: Response from the API.

    Raises:
        ValueError: If not configured with token and account_id.
        requests.exceptions.HTTPError: If the API request fails.
    """
    token = config.get_token()
    account_id = config.get_account_id()

    if not token:
        raise ValueError("No API token configured. Run 'euno init' first.")
    if not account_id:
        raise ValueError("No account ID configured. Run 'euno init' first.")

    response = api_client.set_metadata_tag_value(token, account_id, cp_id, value_updates)
    return response
