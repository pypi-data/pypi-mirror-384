"""Main bug hunter decorator class with comprehensive error handling.

This module provides the core BugHunterDecorator class that wraps functions
to automatically create GitHub issues when errors occur. The decorator handles:

- Function wrapping with error collection context
- Exception and SystemExit handling
- Integration with consolidated handlers for log errors
- Signal and exit termination handling
- Configuration management for resilience features

The decorator coordinates with other core modules for background processing,
signal handling, issue creation, and registry management.
"""

import contextlib
import functools
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from exc2issue.core.background_worker import ensure_background_worker
from exc2issue.core.client_factory import create_ai_client, create_github_client
from exc2issue.core.config_types import AuthConfig, BugHunterConfig, ProcessingConfig
from exc2issue.core.error_collection import ErrorCollection, ErrorCollectionContext
from exc2issue.core.error_handling import (
    handle_exit_cleanup,
    handle_signal_termination,
    handle_system_exit,
)
from exc2issue.core.handlers import ConsolidatedHandlers
from exc2issue.core.issue_creator import process_error_collection
from exc2issue.core.registry import add_active_decorator
from exc2issue.core.signal_handling import setup_exit_handler, setup_signal_handlers
from exc2issue.observability import get_metrics_collector

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from exc2issue.adapters.gemini import GeminiClient
    from exc2issue.adapters.github import GitHubClient
    from exc2issue.adapters.vertexai import VertexAIClient
    from exc2issue.observability.metrics_collector import MetricsCollector


@dataclass
class _ExecutionState:
    """Track execution outcome for metrics and logging decisions."""

    start_time: float
    duration: float | None = None
    outcome: str | None = None
    exception: BaseException | None = None


class _ExecutionMonitor:
    """Context manager that orchestrates execution outcomes."""

    def __init__(
        self,
        decorator: "BugHunterDecorator",
        func: Callable[..., Any],
        collection: ErrorCollection,
        state: _ExecutionState,
    ) -> None:
        self._decorator = decorator
        self._func = func
        self._collection = collection
        self._state = state

    def __enter__(self) -> "_ExecutionMonitor":
        return self

    def on_success(self, result: Any) -> Any:
        """Handle successful execution and process collected errors."""
        self._state.duration = time.perf_counter() - self._state.start_time
        self._state.outcome = "success"

        if self._collection.has_errors():
            logger.warning(
                "Function completed with collected errors",
                extra={
                    "function": self._func.__name__,
                    "error_count": len(self._collection.errors),
                },
            )
            process_error_collection(self._decorator, self._collection)
        else:
            logger.debug(
                "Function completed successfully",
                extra={"function": self._func.__name__},
            )

        return result

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        _traceback: Any,
    ) -> Literal[False]:
        if exc is None:
            return False

        self._state.duration = time.perf_counter() - self._state.start_time
        self._state.exception = exc

        if isinstance(exc, SystemExit):
            self._state.outcome = "system_exit"
            logger.critical(
                "SystemExit caught",
                extra={
                    "function": self._func.__name__,
                    "exit_code": exc.code,
                },
            )
            handle_system_exit(exc, self._func, self._collection)
            process_error_collection(self._decorator, self._collection)
            return False

        if isinstance(exc, Exception):
            self._state.outcome = "error"
            logger.error(
                "Exception caught",
                extra={
                    "function": self._func.__name__,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
                exc_info=True,
            )
            self._decorator.consolidated_handlers.handle_exception(exc, self._func)
            process_error_collection(self._decorator, self._collection)

        return False


class _MetricsGuard:
    """Context manager that logs and suppresses metrics collector errors."""

    def __init__(self, func_name: str, collector_method: str) -> None:
        self._func_name = func_name
        self._collector_method = collector_method
        self.success = True

    def __enter__(self) -> "_MetricsGuard":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        _traceback: Any,
    ) -> bool:
        if exc is None:
            return False

        self.success = False
        logger.warning(
            "Metrics collection failed",
            extra={
                "function": self._func_name,
                "collector_method": self._collector_method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True,
        )
        return True


class BugHunterDecorator:
    """Bug hunter decorator with comprehensive error handling and resilience.

    This decorator provides complete error handling capabilities:
    1. Consolidated error handling for multiple related errors
    2. Multi-layered resilience for termination scenarios
    3. Configurable behavior through feature flags
    """

    def __init__(
        self,
        config: BugHunterConfig | None = None,
        repository: str | None = None,
        **kwargs: Any,
    ):
        """Initialize bug hunter decorator with comprehensive error handling.

        Args:
            config: Complete configuration object (preferred)
            repository: GitHub repository in format "owner/repo" (required if config not provided)
            **kwargs: Legacy parameters for backward compatibility
        """
        # Use provided config or create from legacy parameters
        if config is not None:
            self.config = config
        elif repository:
            # Create from repository and kwargs
            all_params = {"repository": repository, **kwargs}
            self.config = BugHunterConfig.create_legacy(**all_params)
        elif kwargs.get("repository"):
            # Create from kwargs only
            self.config = BugHunterConfig.create_legacy(**kwargs)
        else:
            raise ValueError("Repository is required for exc2issue decorator")

        # Initialize client attributes to avoid W0201, but don't create actual clients yet
        # Clients are created lazily when first accessed
        self._github_client: GitHubClient | None = None
        self._ai_client: GeminiClient | VertexAIClient | None = None

        # Instance tracking
        self._instance_id = str(uuid.uuid4())
        self._is_active = False
        self._current_error_collection: ErrorCollection | None = None

        # Setup consolidated handlers
        self.consolidated_handlers = ConsolidatedHandlers(self)

        # Setup resilience mechanisms
        self._setup_resilience_mechanisms()

    # Backward compatibility properties
    @property
    def repository(self) -> str:
        """Get repository from config."""
        return self.config.repository

    @property
    def labels(self) -> list[str]:
        """Get labels from config."""
        return self.config.labels

    @property
    def assignees(self) -> list[str]:
        """Get assignees from config."""
        return self.config.assignees

    @property
    def auth_config(self) -> AuthConfig:
        """Get auth config."""
        return self.config.auth_config

    @property
    def processing_config(self) -> ProcessingConfig:
        """Get processing config."""
        return self.config.processing_config

    @property
    def consolidation_threshold(self) -> int:
        """Get consolidation threshold from processing config."""
        return self.config.processing_config.consolidation_threshold

    @property
    def enable_signal_handling(self) -> bool:
        """Get signal handling setting from processing config."""
        return self.config.processing_config.enable_signal_handling

    @property
    def enable_exit_handling(self) -> bool:
        """Get exit handling setting from processing config."""
        return self.config.processing_config.enable_exit_handling

    @property
    def enable_background_processing(self) -> bool:
        """Get background processing setting from processing config."""
        return self.config.processing_config.enable_background_processing

    @property
    def github_client(self) -> "GitHubClient":
        """Get GitHub client, creating it lazily if needed."""
        if self._github_client is None:
            self._github_client = create_github_client(
                self.config.auth_config.github_token
            )
        return self._github_client

    @property
    def ai_client(self) -> "GeminiClient | VertexAIClient | None":
        """Get AI client (VertexAI or Gemini), creating it lazily if needed.

        Uses create_ai_client() which prioritizes VertexAI over Gemini based on
        configuration. Returns None if no AI provider is configured.
        """
        if self._ai_client is None:
            self._ai_client = create_ai_client(
                gemini_api_key=self.config.auth_config.gemini_api_key,
                vertexai_project=self.config.auth_config.vertexai_project,
                vertexai_location=self.config.auth_config.vertexai_location,
            )
        return self._ai_client

    @property
    def gemini_client(self) -> "GeminiClient | VertexAIClient | None":
        """Get AI client (deprecated: use ai_client instead).

        This property is maintained for backward compatibility but now returns
        either a VertexAI or Gemini client based on configuration priority.
        """
        return self.ai_client

    # Public accessors for state management
    def is_active(self) -> bool:
        """Check if decorator is currently active."""
        return self._is_active

    def get_current_error_collection(self) -> ErrorCollection | None:
        """Get current error collection if available."""
        return self._current_error_collection

    def _setup_resilience_mechanisms(self) -> None:
        """Setup signal handlers and exit handlers."""
        # Register this decorator
        add_active_decorator(self)

        # Setup global signal handlers (only once)
        if self.config.processing_config.enable_signal_handling:
            setup_signal_handlers()

        # Setup global exit handler (only once)
        if self.config.processing_config.enable_exit_handling:
            setup_exit_handler()

        # Ensure background worker is running
        if self.config.processing_config.enable_background_processing:
            ensure_background_worker()

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorate the function with comprehensive error handling and resilience."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute decorated function with error handling, logging, and metrics.

            Metrics are collected for:
            - Duration (function execution time only, excludes error processing overhead)
            - Success (on successful completion)
            - Errors (on exceptions and SystemExit)
            """
            collector = get_metrics_collector()
            start_time = time.perf_counter()

            logger.debug(
                "Function execution started",
                extra={"function": func.__name__},
            )

            error_collection = ErrorCollection(
                function_name=func.__name__, args=args, kwargs=kwargs
            )

            self._is_active = True
            self._current_error_collection = error_collection
            state = _ExecutionState(start_time=start_time)

            try:
                with ErrorCollectionContext(error_collection) as collection, \
                     _ExecutionMonitor(self, func, collection, state) as monitor:
                    result = func(*args, **kwargs)
                    return monitor.on_success(result)
            finally:
                self._finalize_execution(func.__name__, collector, state)
                self._is_active = False
                self._current_error_collection = None

        return wrapper

    def _finalize_execution(
        self,
        func_name: str,
        collector: "MetricsCollector | None",
        state: _ExecutionState,
    ) -> None:
        """Record metrics and log failures without interrupting execution."""
        if collector is None or state.duration is None or state.outcome is None:
            return

        with _MetricsGuard(func_name, "record_duration") as guard:
            collector.record_duration(func_name, state.duration)
        if not guard.success:
            return

        if state.outcome == "success":
            with _MetricsGuard(func_name, "record_success"):
                collector.record_success(func_name)
        elif state.outcome == "error" and state.exception is not None:
            with _MetricsGuard(func_name, "record_error"):
                collector.record_error(
                    func_name,
                    type(state.exception).__name__,
                    state.exception,
                )
        elif state.outcome == "system_exit" and state.exception is not None:
            with _MetricsGuard(func_name, "record_error"):
                collector.record_error(
                    func_name,
                    "SystemExit",
                    state.exception,
                )

    def handle_signal_termination(self, signum: int, frame: Any) -> None:
        """Handle signal-based termination by delegating to error handling module."""
        handle_signal_termination(self, signum, frame)

    def handle_exit_cleanup(self) -> None:
        """Handle exit cleanup by delegating to error handling module."""
        handle_exit_cleanup(self)

    def cleanup(self) -> None:
        """Clean up handlers and resources."""
        if hasattr(self, "consolidated_handlers"):
            self.consolidated_handlers.cleanup()

    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        with contextlib.suppress(Exception):
            self.cleanup()


def exc2issue(
    config: BugHunterConfig | None = None,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Bug hunter decorator with comprehensive error handling and resilience.

    This decorator provides comprehensive error handling and resilience:

    **Consolidated Error Handling:**
    - Collects multiple errors from single function execution
    - Creates single comprehensive GitHub issues for related errors
    - HYBRID logic: single errors use deterministic titles, multiple errors use consolidated format

    **Multi-Layered Resilience:**
    - Catches sys.exit() calls and creates GitHub issues
    - Handles signal termination (SIGTERM, SIGINT, SIGHUP)
    - Background processing with retry logic for reliable issue creation
    - Graceful cleanup and shutdown handling

    **Configurable Behavior:**
    - Feature flags to enable/disable specific resilience features
    - Adjustable consolidation threshold
    - Full backward compatibility

    Args:
        config: Complete configuration object (preferred)
        **kwargs: Legacy parameters for backward compatibility including:
            repository, labels, assignee, assignees, github_token, gemini_api_key,
            enable_signal_handling, enable_exit_handling, enable_background_processing,
            consolidation_threshold, auth_config, processing_config

    Returns:
        Decorated function that creates GitHub issues on various error/termination types

    Raises:
        ValueError: If neither config nor repository is provided
    """
    decorator_instance = BugHunterDecorator(
        config,
        **kwargs,
    )

    return decorator_instance
