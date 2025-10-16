"""Base AI client with shared functionality for Gemini and Vertex AI clients.

This module provides a base class that contains common logic for AI-powered
issue description generation, including retry mechanisms, error handling,
and response validation.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from exc2issue.core.models import ErrorRecord

ClientT_co = TypeVar("ClientT_co", bound="BaseAIClient", covariant=True)

APIError: type[Exception]
ServerError: type[Exception]
GENAI: Any | None

try:
    from google import genai as genai_module
    from google.genai.errors import APIError as GenaiAPIError
    from google.genai.errors import ServerError as GenaiServerError
except ImportError:
    # Google Gemini is an optional dependency
    GENAI = None
    APIError = type("APIError", (Exception,), {})
    ServerError = type("ServerError", (Exception,), {})
else:
    GENAI = genai_module
    APIError = GenaiAPIError
    ServerError = GenaiServerError


class BaseAIClient(ABC):
    """Base class for AI clients with shared retry and validation logic.

    This abstract base class provides common functionality for AI clients,
    including retry mechanisms, error handling, and response validation.
    Subclasses must implement the abstract methods for client-specific logic.
    """

    def __init__(self, *, config: object | None = None, **_: Any) -> None:
        """Accept flexible keyword arguments so subclasses can define rich configs."""
        self._base_config = config


    @abstractmethod
    def _build_prompt(self, error_record: ErrorRecord) -> str:
        """Build prompt from error record.

        Args:
            error_record: ErrorRecord containing error details

        Returns:
            Formatted prompt string
        """

    @abstractmethod
    def _generate_content(self, prompt: str) -> Any:
        """Generate content using the AI provider's API.

        Args:
            prompt: The prompt to send to the AI provider

        Returns:
            Response object from the AI provider

        Raises:
            APIError: If the API call fails
            ServerError: If the server encounters an error
        """

    @abstractmethod
    def _get_config_use_fallback(self) -> bool:
        """Get the use_fallback configuration value.

        Returns:
            True if fallback is enabled, False otherwise
        """

    @abstractmethod
    def _get_config_max_retries(self) -> int:
        """Get the max_retries configuration value.

        Returns:
            Maximum number of retry attempts
        """

    @classmethod
    def from_config(cls: type[ClientT_co], config: object) -> ClientT_co:
        """Create client from configuration.

        Args:
            config: Configuration settings

        Returns:
            Configured client instance
        """
        return cls(config=config)

    @classmethod
    def from_config_optional(cls: type[ClientT_co], config: object | None) -> ClientT_co | None:
        """Create client from configuration if configuration is available.

        Args:
            config: Configuration settings or None

        Returns:
            Configured client instance if config is available, None otherwise
        """
        if config is None:
            return None

        try:
            return cls(config=config)
        except ValueError:
            # If creation fails (e.g., missing required parameters), return None
            return None

    def generate_issue_description_with_retry(self, error_record: ErrorRecord) -> str:
        """Generate issue description with retry mechanism.

        Args:
            error_record: ErrorRecord containing error details

        Returns:
            Generated issue description as a string

        Raises:
            APIError: If all retry attempts fail
        """
        last_error = None
        max_retries = self._get_config_max_retries()
        # Ensure at least one attempt is always made
        total_attempts = max(1, max_retries)

        for attempt in range(total_attempts):
            try:
                # Disable fallback during retries to allow proper retry logic
                return self.generate_issue_description(
                    error_record, _allow_fallback=False
                )
            except (APIError, ServerError, ValueError) as exc:
                last_error = exc
                # Check for ServerError first since it's a subclass of APIError
                if isinstance(exc, ServerError):
                    # Handle server errors with retry
                    if attempt == total_attempts - 1:
                        # Last attempt failed, use fallback if enabled
                        if self._get_config_use_fallback():
                            # pylint: disable=import-outside-toplevel
                            from exc2issue.adapters.gemini._fallback import (
                                create_fallback_description,
                            )

                            return create_fallback_description(error_record)

                        raise

                    # Exponential backoff for server errors
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                elif isinstance(exc, APIError):
                    # Don't retry API errors (usually client errors)
                    # Use fallback if enabled
                    if self._get_config_use_fallback():
                        # pylint: disable=import-outside-toplevel
                        from exc2issue.adapters.gemini._fallback import (
                            create_fallback_description,
                        )

                        return create_fallback_description(error_record)
                    raise
                else:
                    # Handle ValueError and other exceptions
                    if attempt == total_attempts - 1:
                        # Last attempt failed, use fallback if enabled
                        if self._get_config_use_fallback():
                            # pylint: disable=import-outside-toplevel
                            from exc2issue.adapters.gemini._fallback import (
                                create_fallback_description,
                            )

                            return create_fallback_description(error_record)

                        raise

                    # Exponential backoff for other errors
                    wait_time = 2**attempt
                    time.sleep(wait_time)

        # This should never be reached, but just in case
        if last_error:
            raise last_error

        raise ValueError("All retry attempts failed")

    def validate_response(self, response: Any) -> bool:
        """Validate API response.

        Args:
            response: Response object from AI provider API

        Returns:
            True if response is valid, False otherwise
        """
        if not response:
            return False

        if not hasattr(response, "text"):
            return False

        if response.text is None:
            return False
        return bool(response.text.strip())

    def generate_issue_description(
        self, error_record: ErrorRecord, _allow_fallback: bool = True
    ) -> str:
        """Generate a description for a GitHub issue based on an error record.

        Args:
            error_record: ErrorRecord containing error details
            _allow_fallback: Internal parameter to control fallback behavior for retry logic

        Returns:
            Generated issue description as a string

        Raises:
            APIError: If AI API call fails and use_fallback is False
        """
        try:
            prompt = self._build_prompt(error_record)

            # Generate content using AI provider API
            response = self._generate_content(prompt)

            if self.validate_response(response):
                if response.text is not None:
                    response_text = str(response.text)
                    return response_text.strip()

                if self._get_config_use_fallback() and _allow_fallback:
                    # pylint: disable=import-outside-toplevel
                    from exc2issue.adapters.gemini._fallback import (
                        create_fallback_description,
                    )

                    return create_fallback_description(error_record)

                raise ValueError("Empty response from AI API")

            if self._get_config_use_fallback() and _allow_fallback:
                # pylint: disable=import-outside-toplevel
                from exc2issue.adapters.gemini._fallback import (
                    create_fallback_description,
                )

                return create_fallback_description(error_record)

            raise ValueError("Invalid response from AI API")

        except (APIError, ServerError):
            # Don't use fallback during retry attempts for proper retry logic
            if _allow_fallback and self._get_config_use_fallback():
                # pylint: disable=import-outside-toplevel
                from exc2issue.adapters.gemini._fallback import (
                    create_fallback_description,
                )

                return create_fallback_description(error_record)

            raise
