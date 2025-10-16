"""Bug Hunter: Automatic GitHub issue creation for Python errors.

This library provides decorators that automatically create GitHub issues
when functions encounter errors or log critical messages using AI-powered
descriptions.

Main exports:
- exc2issue: Comprehensive decorator with consolidated error handling and resilience
- ErrorRecord: Data model for captured error information
- GitHubIssue: Data model for GitHub issue creation
- GitHubClient: Client for GitHub API integration
- GeminiClient: Client for Gemini AI integration

Basic Example:
    >>> from exc2issue import exc2issue
    >>>
    >>> # Set environment variables:
    >>> # export GITHUB_TOKEN="your_github_token"
    >>> # export GEMINI_API_KEY="your_gemini_api_key"
    >>>
    >>> @exc2issue(labels=["bug", "auto"], repository="owner/repo")
    ... def risky_function():
    ...     raise ValueError("Something went wrong!")
    ...
    >>> risky_function()  # This will create a GitHub issue automatically

Comprehensive Example (All Features):
    >>> from exc2issue import exc2issue
    >>> import logging
    >>>
    >>> @exc2issue(
    ...     labels=["bug", "auto"],
    ...     repository="owner/repo",
    ...     consolidation_threshold=2,      # Consolidate 2+ errors
    ...     enable_signal_handling=True,    # Catch signals (default: True)
    ...     enable_exit_handling=True,      # Catch sys.exit() (default: True)
    ...     enable_background_processing=True  # Background retry logic (default: True)
    ... )
    ... def comprehensive_function():
    ...     logging.error("Database connection failed")  # Captured
    ...     sys.exit(1)                                   # Also captured!
    ...     # Both errors → Single consolidated GitHub issue
    ...
    >>> comprehensive_function()
"""

__version__ = "0.1.0"

from typing import TYPE_CHECKING

from exc2issue.adapters.github import GitHubClient
from exc2issue.core.error_collection import ErrorCollection, ErrorEntry
from exc2issue.core.handlers import ConsolidatedHandlers, ExceptionHandler, LogHandler
from exc2issue.core.models import ErrorRecord, GitHubIssue
from exc2issue.decorator import exc2issue
from exc2issue.observability import (
    MetricsCollector,
    get_metrics_collector,
    set_metrics_collector,
)

if TYPE_CHECKING:
    from exc2issue.adapters.gemini import GeminiClient as GeminiClientType
    from exc2issue.adapters.vertexai import VertexAIClient as VertexAIClientType
else:

    class GeminiClientType:  # pragma: no cover - runtime placeholder
        """Runtime placeholder used when Gemini dependency is unavailable."""

        def __init__(self, *args, **kwargs):
            """Placeholder init."""
            raise ImportError("Gemini dependency not available")

        def generate_issue_description(self, *args, **kwargs):
            """Placeholder method."""
            raise ImportError("Gemini dependency not available")

        def generate_issue_description_with_retry(self, *args, **kwargs):
            """Placeholder method."""
            raise ImportError("Gemini dependency not available")

    class VertexAIClientType:  # pragma: no cover - runtime placeholder
        """Runtime placeholder used when VertexAI dependency is unavailable."""

        def __init__(self, *args, **kwargs):
            """Placeholder init."""
            raise ImportError("VertexAI dependency not available")

        def generate_issue_description(self, *args, **kwargs):
            """Placeholder method."""
            raise ImportError("VertexAI dependency not available")

        def generate_issue_description_with_retry(self, *args, **kwargs):
            """Placeholder method."""
            raise ImportError("VertexAI dependency not available")


try:
    from exc2issue.adapters.gemini import GeminiClient as _GeminiClient  # noqa: I001
except ImportError:
    GeminiClient: type[GeminiClientType] | None = None
else:
    GeminiClient = _GeminiClient

try:
    from exc2issue.adapters.vertexai import VertexAIClient as _VertexAIClient  # noqa: I001
except ImportError:
    VertexAIClient: type[VertexAIClientType] | None = None
else:
    VertexAIClient = _VertexAIClient

__all__ = [
    "exc2issue",
    "ErrorRecord",
    "GitHubIssue",
    "GitHubClient",
    "GeminiClient",
    "VertexAIClient",
    "ErrorCollection",
    "ErrorEntry",
    "ConsolidatedHandlers",
    "ExceptionHandler",
    "LogHandler",
    "MetricsCollector",
    "set_metrics_collector",
    "get_metrics_collector",
]
