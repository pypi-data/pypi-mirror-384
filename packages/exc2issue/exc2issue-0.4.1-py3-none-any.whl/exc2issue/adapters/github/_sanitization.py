"""Data sanitization utilities for the GitHub client.

This module contains functions for sanitizing issue data before sending to the
GitHub API, including title and body sanitization.
"""

import html
import re
from typing import Any

from exc2issue.core.models import GitHubIssue


def sanitize_issue_data(issue: GitHubIssue) -> dict[str, Any]:
    """Sanitize issue data for API submission.

    Args:
        issue: GitHubIssue to sanitize

    Returns:
        Dictionary with sanitized data ready for API
    """
    # Start with the basic issue data
    data = issue.to_dict()

    # Sanitize title - remove/escape potentially dangerous characters
    title = data["title"]
    title = html.escape(title, quote=False)  # Escape HTML entities
    title = title.replace("\x00", "")  # Remove null bytes
    title = re.sub(r"[\x01-\x1f\x7f-\x9f]", "", title)  # Remove control characters

    # Ensure title length doesn't exceed GitHub's limit
    if len(title) > 256:
        title = title[:253] + "..."

    data["title"] = title

    # Sanitize body
    body = data["body"]
    body = body.replace("\x00", "")  # Remove null bytes
    body = re.sub(
        r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", body
    )  # Remove most control chars, keep \t, \n, \r
    data["body"] = body

    # Remove assignees if empty
    if not data.get("assignees"):
        data.pop("assignees", None)

    return data
