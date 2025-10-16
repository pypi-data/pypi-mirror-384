"""Client factory for creating GitHub and AI clients.

This module provides factory functions for creating client instances
while avoiding circular import issues in the decorator module.

Note: Imports are done inside functions to prevent circular import issues.
Pylint import-outside-toplevel warning is intentionally accepted here as
moving imports to module level would recreate the circular dependency.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from exc2issue.adapters.gemini import GeminiClient
    from exc2issue.adapters.github import GitHubClient
    from exc2issue.adapters.vertexai import VertexAIClient

logger = logging.getLogger(__name__)


def _get_github_client_class() -> type["GitHubClient"]:
    """Get GitHub client class.

    Import is done here to prevent circular dependencies.
    """
    # pylint: disable=import-outside-toplevel
    from exc2issue.adapters.github import GitHubClient as _GitHubClient

    return _GitHubClient


def _get_gemini_client_class() -> type["GeminiClient"] | None:
    """Get Gemini client class if available.

    Import is done here to prevent circular dependencies.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from exc2issue.adapters.gemini import GeminiClient as _GeminiClient

        return _GeminiClient
    except ImportError:
        return None


def _get_vertexai_client_class() -> type["VertexAIClient"] | None:
    """Get Vertex AI client class if available.

    Import is done here to prevent circular dependencies.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from exc2issue.adapters.vertexai import VertexAIClient as _VertexAIClient

        return _VertexAIClient
    except ImportError:
        return None


def _has_gemini_config() -> bool:
    """Check if Gemini configuration is available.

    Returns:
        True if Gemini API key is configured, False otherwise
    """
    try:
        # pylint: disable=import-outside-toplevel
        from exc2issue.config import GeminiConfig

        # Instantiate the settings class to trigger environment loading.
        # Pydantic BaseSettings pulls values from env vars and .env files.
        # A missing required field returns None, which we check below.
        config = GeminiConfig()
        return config.api_key is not None
    except (ValueError, ImportError):
        return False


def _has_vertexai_config() -> bool:
    """Check if Vertex AI configuration is available.

    Returns:
        True if Vertex AI project is configured, False otherwise
    """
    try:
        # pylint: disable=import-outside-toplevel
        from exc2issue.config import VertexAIConfig

        # Instantiate the settings class to trigger environment loading.
        # Missing required fields return None, which we check below.
        config = VertexAIConfig()
        return config.project is not None
    except (ValueError, ImportError):
        return False


def create_github_client(token: str | None = None) -> "GitHubClient":
    """Create GitHub client instance.

    Args:
        token: GitHub API token (optional)

    Returns:
        GitHubClient: Configured GitHub client
    """
    github_client_class = _get_github_client_class()
    if token:
        return github_client_class(token=token)
    return github_client_class()


def create_gemini_client(api_key: str | None = None) -> "GeminiClient | None":
    """Create Gemini client instance if available.

    Args:
        api_key: Gemini API key (optional)

    Returns:
        GeminiClient: Configured Gemini client or None if unavailable
    """
    gemini_client_class = _get_gemini_client_class()

    if gemini_client_class is None:
        # Gemini client is optional - system works with fallback descriptions
        return None
    if api_key:
        try:
            return gemini_client_class(api_key=api_key)
        except ValueError:
            return None
    else:
        try:
            return gemini_client_class()
        except ValueError:
            return None


def create_vertexai_client(
    project: str | None = None, location: str | None = None
) -> "VertexAIClient | None":
    """Create Vertex AI client instance if available.

    Args:
        project: Google Cloud Project ID (optional)
        location: Google Cloud location/region (optional)

    Returns:
        VertexAIClient: Configured Vertex AI client or None if unavailable

    Note:
        Catches all exceptions during client creation to ensure graceful fallback.
        This includes ValueError, google.auth.exceptions.DefaultCredentialsError,
        networking errors, and other runtime exceptions from google.genai.Client.
    """
    vertexai_client_class = _get_vertexai_client_class()

    if vertexai_client_class is None:
        # Vertex AI client is optional - system works with fallback descriptions
        return None

    try:
        if project and location:
            return vertexai_client_class(project=project, location=location)
        if project:
            return vertexai_client_class(project=project)
        if location:
            # Project will come from env, but respect location override
            return vertexai_client_class(location=location)
        return vertexai_client_class()
    except Exception as e:  # pylint: disable=broad-except
        # Catch all exceptions to ensure graceful fallback:
        # - ValueError: Missing required configuration
        # - google.auth.exceptions.DefaultCredentialsError: ADC credentials missing
        # - OSError/RuntimeError: Network/auth errors from google.genai.Client constructor
        # - Any other runtime exceptions
        # Log at debug level since this is expected when VertexAI is not configured
        logger.debug(
            "Failed to create VertexAI client, will fall back to Gemini or plain text: %s",
            str(e),
            exc_info=True,
        )
        return None


def create_ai_client(
    gemini_api_key: str | None = None,
    vertexai_project: str | None = None,
    vertexai_location: str | None = None,
) -> "GeminiClient | VertexAIClient | None":
    """Create AI client with provider priority: VertexAI > Gemini > None.

    Priority Order:
        1. Vertex AI (if vertexai_project is provided or BUG_HUNTER_VERTEXAI_PROJECT is set)
        2. Gemini API (if gemini_api_key is provided or BUG_HUNTER_GEMINI_API_KEY is set)
        3. None (fallback descriptions will be used)

    Conflict Handling:
        If both Vertex AI and Gemini configurations are present, uses Vertex AI
        and logs a warning about the conflicting configuration.

    Args:
        gemini_api_key: Gemini API key (optional, falls back to environment)
        vertexai_project: Google Cloud Project ID (optional, falls back to environment)
        vertexai_location: Google Cloud location/region (optional, falls back to environment)

    Returns:
        AI client instance (VertexAI or Gemini) or None if no provider is available
    """
    # Try Vertex AI first
    vertexai_client = create_vertexai_client(
        project=vertexai_project, location=vertexai_location
    )
    if vertexai_client is not None:
        # Log warning if Gemini is also configured
        if gemini_api_key or _has_gemini_config():
            logger.warning(
                "Both Vertex AI and Gemini configurations found. Using Vertex AI."
            )
        return vertexai_client

    # Fall back to Gemini API
    return create_gemini_client(api_key=gemini_api_key)
