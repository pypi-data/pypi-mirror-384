"""Configuration management for exc2issue using Pydantic Settings.

This module provides simple configuration management for the exc2issue library.
Each component (GitHub, Gemini, Logging) has its own BaseSettings class with
proper environment variable prefixes and aliases for flexibility.
"""

from typing import Literal

from pydantic import AliasChoices, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GitHubConfig(BaseSettings):
    """GitHub API configuration.

    Environment Variables:
        GITHUB_TOKEN or BUG_HUNTER_GITHUB_TOKEN: GitHub personal access token
        GITHUB_URL or BUG_HUNTER_GITHUB_BASE_URL: GitHub API base URL (optional)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    token: SecretStr = Field(
        min_length=1,
        validation_alias=AliasChoices("GITHUB_TOKEN", "BUG_HUNTER_GITHUB_TOKEN"),
        description="GitHub personal access token for API authentication",
    )
    base_url: HttpUrl = Field(
        default=HttpUrl("https://api.github.com"),
        validation_alias=AliasChoices("GITHUB_URL", "BUG_HUNTER_GITHUB_BASE_URL"),
        description="GitHub API base URL (for GitHub Enterprise support)",
    )


class GeminiConfig(BaseSettings):
    """Gemini API configuration.

    Environment Variables:
        GEMINI_API_KEY or BUG_HUNTER_GEMINI_API_KEY: Google Gemini API key
        GEMINI_MODEL_NAME or BUG_HUNTER_GEMINI_MODEL_NAME: Model name (optional)
        GEMINI_TEMPERATURE or BUG_HUNTER_GEMINI_TEMPERATURE: Temperature (optional)
        GEMINI_MAX_OUTPUT_TOKENS or BUG_HUNTER_GEMINI_MAX_OUTPUT_TOKENS: Max tokens (optional)
        GEMINI_MAX_RETRIES or BUG_HUNTER_GEMINI_MAX_RETRIES: Max retries (optional)
        GEMINI_USE_FALLBACK or BUG_HUNTER_GEMINI_USE_FALLBACK: Use fallback (optional)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    api_key: SecretStr | None = Field(
        default=None,
        min_length=1,
        validation_alias=AliasChoices("GEMINI_API_KEY", "BUG_HUNTER_GEMINI_API_KEY"),
        description="Google Gemini API key for AI-powered issue descriptions",
    )
    model_name: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices(
            "GEMINI_MODEL_NAME", "BUG_HUNTER_GEMINI_MODEL_NAME"
        ),
        description="Gemini model name to use for generation",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "GEMINI_TEMPERATURE", "BUG_HUNTER_GEMINI_TEMPERATURE"
        ),
        description="Sampling temperature for response generation (0.0 to 1.0)",
    )
    max_output_tokens: int = Field(
        default=2048,
        gt=0,
        validation_alias=AliasChoices(
            "GEMINI_MAX_OUTPUT_TOKENS", "BUG_HUNTER_GEMINI_MAX_OUTPUT_TOKENS"
        ),
        description="Maximum tokens in generated output",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        validation_alias=AliasChoices(
            "GEMINI_MAX_RETRIES", "BUG_HUNTER_GEMINI_MAX_RETRIES"
        ),
        description="Maximum number of retry attempts for API calls",
    )
    use_fallback: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "GEMINI_USE_FALLBACK", "BUG_HUNTER_GEMINI_USE_FALLBACK"
        ),
        description="Whether to use fallback descriptions when AI generation fails",
    )


class VertexAIConfig(BaseSettings):
    """Vertex AI configuration.

    Environment Variables:
        VERTEXAI_PROJECT or BUG_HUNTER_VERTEXAI_PROJECT: GCP Project ID
        VERTEXAI_LOCATION or BUG_HUNTER_VERTEXAI_LOCATION: GCP Location/Region
        VERTEXAI_MODEL_NAME or BUG_HUNTER_VERTEXAI_MODEL_NAME: Model name (optional)
        VERTEXAI_TEMPERATURE or BUG_HUNTER_VERTEXAI_TEMPERATURE: Temperature (optional)
        VERTEXAI_MAX_OUTPUT_TOKENS or BUG_HUNTER_VERTEXAI_MAX_OUTPUT_TOKENS: Max tokens (optional)
        VERTEXAI_MAX_RETRIES or BUG_HUNTER_VERTEXAI_MAX_RETRIES: Max retries (optional)
        VERTEXAI_USE_FALLBACK or BUG_HUNTER_VERTEXAI_USE_FALLBACK: Use fallback (optional)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project: str | None = Field(
        default=None,
        min_length=1,
        validation_alias=AliasChoices("VERTEXAI_PROJECT", "BUG_HUNTER_VERTEXAI_PROJECT"),
        description="Google Cloud Project ID for Vertex AI",
    )
    location: str = Field(
        default="us-central1",
        validation_alias=AliasChoices("VERTEXAI_LOCATION", "BUG_HUNTER_VERTEXAI_LOCATION"),
        description="Google Cloud location/region for Vertex AI",
    )
    model_name: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices(
            "VERTEXAI_MODEL_NAME", "BUG_HUNTER_VERTEXAI_MODEL_NAME"
        ),
        description="Vertex AI model name to use for generation",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices(
            "VERTEXAI_TEMPERATURE", "BUG_HUNTER_VERTEXAI_TEMPERATURE"
        ),
        description="Sampling temperature for response generation (0.0 to 1.0)",
    )
    max_output_tokens: int = Field(
        default=2048,
        gt=0,
        validation_alias=AliasChoices(
            "VERTEXAI_MAX_OUTPUT_TOKENS", "BUG_HUNTER_VERTEXAI_MAX_OUTPUT_TOKENS"
        ),
        description="Maximum tokens in generated output",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        validation_alias=AliasChoices(
            "VERTEXAI_MAX_RETRIES", "BUG_HUNTER_VERTEXAI_MAX_RETRIES"
        ),
        description="Maximum number of retry attempts for API calls",
    )
    use_fallback: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "VERTEXAI_USE_FALLBACK", "BUG_HUNTER_VERTEXAI_USE_FALLBACK"
        ),
        description="Whether to use fallback descriptions when AI generation fails",
    )


class LoggingConfig(BaseSettings):
    """Logging configuration.

    Environment Variables:
        LOG_LEVEL or BUG_HUNTER_LOGGING_LEVEL: Log level (optional)
        LOG_FORMAT or BUG_HUNTER_LOGGING_FORMAT: Log format string (optional)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="WARNING",
        validation_alias=AliasChoices("LOG_LEVEL", "BUG_HUNTER_LOGGING_LEVEL"),
        description="Log level for exc2issue internal logging",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        validation_alias=AliasChoices("LOG_FORMAT", "BUG_HUNTER_LOGGING_FORMAT"),
        description="Log message format string",
    )
