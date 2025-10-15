"""
Core functionality for the Euno SDK.

This module contains the main library functions that users can import
and use programmatically.
"""


def hello_world(name: str = "World") -> str:
    """
    A simple hello world function to demonstrate the SDK.

    Args:
        name: The name to greet (default: "World")

    Returns:
        A greeting message

    Example:
        >>> hello_world("Euno")
        'Hello, Euno! Welcome to the Euno SDK!'
    """
    return f"Hello, {name}! Welcome to the Euno SDK!"


def get_version() -> str:
    """
    Get the current version of the Euno SDK.

    Returns:
        The version string
    """
    from .version import __version__

    return __version__
