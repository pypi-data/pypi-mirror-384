"""
Resources commands for the Euno SDK.

This module provides commands for interacting with Euno data model resources.
"""

from typing import Optional, Dict, Any
from .config import config
from .api import api_client


def list_resources(
    eql: Optional[str] = None,
    properties: str = "uri,type,name",
    page: int = 1,
    page_size: int = 50,
    sorting: Optional[str] = None,
    relationships: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List resources from the Euno data model (Python API).

    Args:
        eql: Euno Query Language expression
        properties: Comma-separated list of properties (default: uri,type,name)
        page: Page number (default: 1)
        page_size: Number of resources per page (default: 50)
        sorting: Sorting specification
        relationships: Comma-separated list of relationships

    Returns:
        Dictionary containing the API response with resources and metadata

    Raises:
        Exception: If the SDK is not configured or API call fails

    Example:
        >>> import euno
        >>> resources = euno.list_resources()
        >>> print(f"Found {resources['count']} resources")
        >>> for resource in resources['resources']:
        ...     print(f"{resource['uri']}: {resource['name']}")
    """
    if not config.is_configured():
        raise Exception("Euno SDK is not configured. Run 'euno init' to get started.")

    token = config.get_token()
    account_id = config.get_account_id()

    if not account_id:
        raise Exception("No account ID configured. Run 'euno init' to set up your account.")

    if not token:
        raise Exception("No token configured. Run 'euno init' to set up your account.")

    # Prepare parameters
    params: Dict[str, Any] = {
        "page": page,
        "page_size": page_size,
        "include_count": True,
    }

    # Add optional parameters if provided
    if eql:
        params["eql"] = [eql]

    # Always add properties (now has default value)
    params["properties"] = properties.split(",")

    if sorting:
        params["sorting"] = sorting.split(",")
    if relationships:
        params["relationships"] = relationships.split(",")

    return api_client.search_resources(token, account_id, params)
