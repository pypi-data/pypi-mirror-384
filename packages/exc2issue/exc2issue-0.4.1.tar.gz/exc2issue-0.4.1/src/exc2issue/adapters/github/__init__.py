"""GitHub adapter for exc2issue.

This package provides integration with the GitHub API for creating
issues automatically when errors are detected.
"""

from .client import GitHubClient

__all__ = ["GitHubClient"]
