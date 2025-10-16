"""Bug hunter decorator for automatic GitHub issue creation.

This module provides the main decorator interface that wraps functions to
automatically create GitHub issues when errors occur.

All implementation is located in the exc2issue.core modules.
"""

from exc2issue.core.decorator import exc2issue

__all__ = ["exc2issue"]
