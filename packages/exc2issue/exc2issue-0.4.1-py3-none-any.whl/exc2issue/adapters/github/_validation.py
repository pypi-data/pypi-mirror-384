"""Validation utilities for the GitHub client.

This module contains validation functions for repository formats and other
GitHub-specific validations. These functions are internal to the GitHub adapter.
"""

import re


def validate_repository_format(repository: str) -> bool:
    """Validate repository format.

    Args:
        repository: Repository string to validate

    Returns:
        True if format is valid

    Raises:
        ValueError: If repository format is invalid
    """
    if not repository or not isinstance(repository, str):
        raise ValueError("Invalid repository format. Expected 'owner/repo'")

    # Check for basic owner/repo pattern
    pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?/[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$"

    if not re.match(pattern, repository):
        raise ValueError("Invalid repository format. Expected 'owner/repo'")

    parts = repository.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError("Invalid repository format. Expected 'owner/repo'")

    return True
