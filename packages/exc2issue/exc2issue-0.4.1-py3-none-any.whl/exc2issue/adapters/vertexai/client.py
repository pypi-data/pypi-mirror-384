"""Main Vertex AI client for exc2issue.

This module provides the main VertexAIClient class for interacting with Google
Cloud Vertex AI to generate intelligent GitHub issue descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from google import genai
from google.genai import types

from exc2issue.adapters._base_ai_client import BaseAIClient

# Import shared utilities from gemini adapter
from exc2issue.adapters.gemini._prompt_builder import build_prompt
from exc2issue.config import VertexAIConfig

if TYPE_CHECKING:
    from exc2issue.core.models import ErrorRecord


class VertexAIClient(BaseAIClient):
    """Client for interacting with Vertex AI.

    This client handles authentication, prompt generation, and AI-powered
    issue description generation with proper error handling and fallback mechanisms.
    Uses Pydantic configuration for settings management.

    Attributes:
        config: VertexAI configuration settings (VertexAIConfig instance)
            Contains: project, location, model_name, temperature, max_output_tokens,
            max_retries, use_fallback
        prompt_template: Custom template for prompt generation (optional)
        client: Google GenAI client instance configured for Vertex AI
    """

    def __init__(
        self,
        project: str | None = None,
        location: str | None = None,
        *,
        config: VertexAIConfig | None = None,
        prompt_template: str | None = None,
        **kwargs: Any,
    ):
        """Initialize Vertex AI client.

        Args:
            project: Google Cloud Project ID. If None, will try to read from env vars.
            location: Google Cloud location/region. If None, will try to read from env vars.
            config: Vertex AI configuration settings (keyword-only, advanced usage).
            prompt_template: Custom template for prompt generation (keyword-only, optional).
            **kwargs: Additional configuration parameters (model_name, temperature, etc.).

        Raises:
            ValueError: If no project is provided and VERTEXAI_PROJECT env var is not set.

        Note:
            For complete configuration control, use the config parameter with a VertexAIConfig object.
            Additional kwargs are used only when config is not provided.
        """
        super().__init__(config=config)
        # Priority order: config > parameters > env vars
        self.config: VertexAIConfig
        if config is not None:
            self.config = config
        elif project is not None:
            # Create config from simplified parameters with kwargs support
            config_params: dict[str, Any] = {"project": project}
            if location is not None:
                config_params["location"] = location
            # Add any additional kwargs that are valid VertexAIConfig parameters
            config_params.update(kwargs)
            self.config = VertexAIConfig(**config_params)
        else:
            # Use VertexAIConfig to load from environment variables (including .env file)
            # But still respect any explicitly provided location parameter
            try:
                config_params = {}
                if location is not None:
                    config_params["location"] = location
                # Add any additional kwargs that are valid VertexAIConfig parameters
                config_params.update(kwargs)
                self.config = VertexAIConfig(**config_params)
            except Exception as e:
                # No project available - VertexAIClient will be None in decorator
                # This allows the system to work with fallback descriptions
                raise ValueError(
                    "Vertex AI project not found. Set VERTEXAI_PROJECT environment "
                    "variable or install with 'pip install exc2issue[ai]' for AI "
                    f"support. Error: {e}"
                ) from e

        # Validate project is present
        if self.config.project is None:
            raise ValueError(
                "Vertex AI project not found. Set VERTEXAI_PROJECT environment "
                "variable or provide project parameter."
            )

        # Store prompt template for custom prompt generation
        self.prompt_template = prompt_template

        # Initialize the Vertex AI client
        self.client = genai.Client(
            vertexai=True, project=self.config.project, location=self.config.location
        )

    def _build_prompt(self, error_record: ErrorRecord) -> str:
        """Build prompt from error record.

        Args:
            error_record: ErrorRecord containing error details

        Returns:
            Formatted prompt string
        """
        return build_prompt(error_record, self.prompt_template)

    def _generate_content(self, prompt: str) -> Any:
        """Generate content using Vertex AI API.

        Args:
            prompt: The prompt to send to Vertex AI

        Returns:
            Response object from Vertex AI API
        """
        return self.client.models.generate_content(
            model=self.config.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
            ),
        )

    def _get_config_use_fallback(self) -> bool:
        """Get the use_fallback configuration value."""
        return self.config.use_fallback

    def _get_config_max_retries(self) -> int:
        """Get the max_retries configuration value."""
        return self.config.max_retries
