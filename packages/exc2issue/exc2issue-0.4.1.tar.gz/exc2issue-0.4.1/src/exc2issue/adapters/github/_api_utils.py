"""API utilities for the GitHub client.

This module contains helper functions for GitHub API interactions,
including header generation and request handling.
"""


def get_headers(token: str) -> dict[str, str]:
    """Get HTTP headers for GitHub API requests.

    Args:
        token: GitHub personal access token

    Returns:
        Dictionary of HTTP headers
    """
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "exc2issue-client/1.0",
    }
