"""Main Gemini client for exc2issue.

This module provides the main GeminiClient class for interacting with the Google
Gemini API to generate intelligent GitHub issue descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from google import genai
from pydantic import SecretStr

from exc2issue.adapters._base_ai_client import BaseAIClient
from exc2issue.config import GeminiConfig

from ._prompt_builder import build_prompt

if TYPE_CHECKING:
    from exc2issue.core.models import ErrorRecord


class GeminiClient(BaseAIClient):
    """Client for interacting with the Gemini API.

    This client handles authentication, prompt generation, and AI-powered
    issue description generation with proper error handling and fallback mechanisms.
    Uses Pydantic configuration for settings management.

    Attributes:
        config: Gemini configuration settings
        api_key: Google Gemini API key for authentication
        model_name: Name of the Gemini model to use
        temperature: Sampling temperature for response generation
        use_fallback: Whether to use fallback descriptions when API fails
        max_retries: Maximum number of retry attempts for API calls
        max_output_tokens: Maximum tokens in generated output
        prompt_template: Custom template for prompt generation
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        config: GeminiConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize Gemini client.

        Args:
            api_key: Google Gemini API key. If None, will try to read from env vars.
            config: Gemini configuration settings (keyword-only, advanced usage).
            **kwargs: Additional configuration parameters (model_name, temperature, etc.).

        Raises:
            ValueError: If no API key is provided and GEMINI_API_KEY env var is not set.

        Note:
            For complete configuration control, use the config parameter with a GeminiConfig object.
            Additional kwargs are used only when config is not provided.
        """
        super().__init__(config=config)
        # Priority order: config > parameters > env vars
        self.config: GeminiConfig
        if config is not None:
            self.config = config
        elif api_key is not None:
            # Create config from simplified parameters with kwargs support
            config_params: dict[str, Any] = {"api_key": SecretStr(api_key)}
            # Add any additional kwargs that are valid GeminiConfig parameters
            # Note: GeminiConfig expects plain types, not SecretStr
            config_params.update(kwargs)
            self.config = GeminiConfig(**config_params)
        else:
            # Use GeminiConfig to load from environment variables (including .env file)
            try:
                config_factory = cast("type[Any]", GeminiConfig)
                self.config = cast("GeminiConfig", config_factory())
            except Exception as e:
                # No API key available - GeminiClient will be None in decorator
                # This allows the system to work with fallback descriptions
                raise ValueError(
                    "Gemini API key not found. Set GEMINI_API_KEY environment "
                    "variable or install with 'pip install exc2issue[ai]' for AI "
                    f"support. Error: {e}"
                ) from e

        # Validate API key is present
        if self.config.api_key is None:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment "
                "variable or provide api_key parameter."
            )

        # Store config and extract critical values for internal use
        # This reduces the number of instance attributes by grouping related settings
        self.prompt_template = kwargs.get("prompt_template")  # Extract from kwargs

        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.config.api_key.get_secret_value())

    def _build_prompt(self, error_record: ErrorRecord) -> str:
        """Build prompt from error record.

        Args:
            error_record: ErrorRecord containing error details

        Returns:
            Formatted prompt string
        """
        return build_prompt(error_record, self.prompt_template)

    def _generate_content(self, prompt: str) -> Any:
        """Generate content using Gemini API.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Response object from Gemini API
        """
        return self.client.models.generate_content(
            model=self.config.model_name, contents=prompt
        )

    def _get_config_use_fallback(self) -> bool:
        """Get the use_fallback configuration value."""
        return self.config.use_fallback

    def _get_config_max_retries(self) -> int:
        """Get the max_retries configuration value."""
        return self.config.max_retries
