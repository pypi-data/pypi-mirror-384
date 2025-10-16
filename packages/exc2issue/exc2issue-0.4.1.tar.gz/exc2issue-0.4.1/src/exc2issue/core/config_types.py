"""Configuration dataclasses for exc2issue core components.

This module contains configuration objects used to reduce the number of arguments
passed to functions and constructors, improving code readability and maintainability.
"""

from dataclasses import dataclass
from typing import Any

# Re-export IssueCreationOptions for backward compatibility
# Moved to exc2issue.types to prevent circular imports
from exc2issue.types import IssueCreationOptions


@dataclass
class AuthConfig:
    """Authentication configuration for external services."""

    github_token: str | None = None
    gemini_api_key: str | None = None
    vertexai_project: str | None = None
    vertexai_location: str | None = None


@dataclass
class ProcessingConfig:
    """Configuration for error processing behavior."""

    enable_signal_handling: bool = True
    enable_exit_handling: bool = True
    enable_background_processing: bool = True
    consolidation_threshold: int = 2


@dataclass
class LegacyParams:
    """Legacy parameters for backward compatibility."""

    labels: list[str] | None = None
    assignee: str | None = None
    assignees: list[str] | None = None
    github_token: str | None = None
    gemini_api_key: str | None = None
    vertexai_project: str | None = None
    vertexai_location: str | None = None


@dataclass
class ProcessingParams:
    """Processing behavior parameters."""

    enable_signal_handling: bool = True
    enable_exit_handling: bool = True
    enable_background_processing: bool = True
    consolidation_threshold: int = 2


@dataclass
class BugHunterConfig:
    """Complete configuration for BugHunterDecorator.

    Groups all configuration parameters to reduce constructor complexity.
    Replaces multiple individual parameters with structured configuration.
    """

    # Repository settings
    repository: str
    labels: list[str]
    assignees: list[str]
    # Authentication and processing configs
    auth_config: AuthConfig
    processing_config: ProcessingConfig

    @classmethod
    def create_from_params(
        cls,
        repository: str,
        legacy_params: LegacyParams | None = None,
        /,  # Positional-only to reduce positional args count
        *,
        processing_params: ProcessingParams | None = None,
        configs: tuple[AuthConfig | None, ProcessingConfig | None] | None = None,
    ) -> "BugHunterConfig":
        """Create configuration from individual parameters for backward compatibility."""
        # Use defaults if no parameters provided
        legacy = legacy_params or LegacyParams()
        processing = processing_params or ProcessingParams()

        # Handle assignees from legacy params
        assignees = legacy.assignees or ([legacy.assignee] if legacy.assignee else [])

        # Extract configs from tuple if provided
        auth_config, processing_config = configs or (None, None)
        # Create auth config from legacy params or use provided
        auth = auth_config or AuthConfig(
            github_token=legacy.github_token,
            gemini_api_key=legacy.gemini_api_key,
            vertexai_project=legacy.vertexai_project,
            vertexai_location=legacy.vertexai_location,
        )

        # Create processing config from processing params or use provided
        proc_config = processing_config or ProcessingConfig(
            enable_signal_handling=processing.enable_signal_handling,
            enable_exit_handling=processing.enable_exit_handling,
            enable_background_processing=processing.enable_background_processing,
            consolidation_threshold=processing.consolidation_threshold,
        )
        return cls(
            repository=repository,
            labels=legacy.labels or [],
            assignees=assignees,
            auth_config=auth,
            processing_config=proc_config,
        )

    @classmethod
    def create_legacy(
        cls,
        repository: str,
        **kwargs: Any,
    ) -> "BugHunterConfig":
        """Create configuration from individual legacy parameters."""
        legacy_params = LegacyParams(
            labels=kwargs.get("labels"),
            assignee=kwargs.get("assignee"),
            assignees=kwargs.get("assignees"),
            github_token=kwargs.get("github_token"),
            gemini_api_key=kwargs.get("gemini_api_key"),
            vertexai_project=kwargs.get("vertexai_project"),
            vertexai_location=kwargs.get("vertexai_location"),
        )

        processing_params = ProcessingParams(
            enable_signal_handling=kwargs.get("enable_signal_handling", True),
            enable_exit_handling=kwargs.get("enable_exit_handling", True),
            enable_background_processing=kwargs.get(
                "enable_background_processing", True
            ),
            consolidation_threshold=kwargs.get("consolidation_threshold", 2),
        )

        auth_config = kwargs.get("auth_config")
        processing_config = kwargs.get("processing_config")
        return cls.create_from_params(
            repository,
            legacy_params,
            processing_params=processing_params,
            configs=(auth_config, processing_config),
        )


@dataclass
class DecoratorConfig:
    """Configuration for BugHunterDecorator initialization.

    Groups related configuration parameters to reduce constructor argument count.

    Deprecated: Use BugHunterConfig instead.
    """

    labels: list[str]
    assignees: list[str]
    repository: str
    auth: AuthConfig
    processing: ProcessingConfig


@dataclass
class ErrorContext:
    """Context information for error record creation.

    Groups optional parameters for ErrorRecord.from_exception to reduce argument count.
    """

    function_args: list[Any] | None = None
    function_kwargs: dict[str, Any] | None = None
    context: dict[str, Any] | None = None


__all__ = [
    "AuthConfig",
    "ProcessingConfig",
    "LegacyParams",
    "ProcessingParams",
    "BugHunterConfig",
    "DecoratorConfig",
    "ErrorContext",
    "IssueCreationOptions",  # Re-exported for backward compatibility
]
