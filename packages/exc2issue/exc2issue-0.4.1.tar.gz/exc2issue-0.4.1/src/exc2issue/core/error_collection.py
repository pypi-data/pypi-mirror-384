"""Error collection system for consolidated error handling.

This module provides the ErrorCollection class that aggregates multiple errors
(exceptions and log errors) from a single function execution into a consolidated
timeline. This enables creating single comprehensive GitHub issues instead of
multiple separate issues.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import local
from typing import Any

from exc2issue.core.config_types import ErrorContext
from exc2issue.core.models import ErrorRecord


@dataclass
class ErrorEntry:
    """Individual error entry in the error collection.

    Attributes:
        error_type: Type of error ("exception" or "log")
        timestamp: When the error occurred
        error_record: The underlying ErrorRecord with full details
        source_info: Additional information about the error source
    """

    error_type: str  # "exception" or "log"
    timestamp: datetime
    error_record: ErrorRecord
    source_info: dict[str, Any]  # Additional context like logger name, level, etc.


class ErrorCollection:
    """Thread-safe collection of errors from a single function execution.

    This class aggregates multiple errors that occur during a single function
    call, allowing them to be processed together into a consolidated GitHub issue.
    """

    def __init__(
        self, function_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ):
        """Initialize error collection for a function execution.

        Args:
            function_name: Name of the function being monitored
            args: Function arguments
            kwargs: Function keyword arguments
        """
        self.function_name = function_name
        self.function_args = args
        self.function_kwargs = kwargs
        self.start_time = datetime.now()
        self.errors: list[ErrorEntry] = []

    def add_exception(
        self,
        exception: Exception,
        func: Callable[..., Any],
        source_info: dict[str, Any] | None = None,
    ) -> None:
        """Add an exception to the error collection.

        Args:
            exception: The caught exception
            func: Function where the exception occurred
            source_info: Additional context information
        """
        error_context = ErrorContext(
            function_args=list(self.function_args) if self.function_args else None,
            function_kwargs=(
                dict(self.function_kwargs) if self.function_kwargs else None
            ),
            context=source_info,
        )
        error_record = ErrorRecord.from_exception(
            exception=exception,
            function_name=func.__name__,
            error_context=error_context,
        )

        entry = ErrorEntry(
            error_type="exception",
            timestamp=datetime.now(),
            error_record=error_record,
            source_info=source_info or {},
        )

        self.errors.append(entry)

    def add_log_error(
        self,
        log_record: logging.LogRecord,
        func: Callable[..., Any],
        source_info: dict[str, Any] | None = None,
    ) -> None:
        """Add a log error to the error collection.

        Args:
            log_record: The logging record
            func: Function where the log occurred
            source_info: Additional context information
        """
        # Create ErrorRecord from log record with full function context
        error_record = ErrorRecord(
            function_name=func.__name__,
            error_type="Log",  # Use "Log" to match utils.generate_deterministic_title expectation
            error_message=log_record.getMessage(),
            timestamp=datetime.fromtimestamp(log_record.created),
            traceback="",  # Log errors don't have tracebacks
            function_args=list(self.function_args) if self.function_args else None,
            function_kwargs=(
                dict(self.function_kwargs) if self.function_kwargs else None
            ),
            context={
                "logger_name": log_record.name,
                "log_level": log_record.levelname,
                "module": log_record.module,
                "line_number": log_record.lineno,
                **(source_info or {}),
            },
        )

        entry = ErrorEntry(
            error_type="log",
            timestamp=datetime.fromtimestamp(log_record.created),
            error_record=error_record,
            source_info={
                "logger_name": log_record.name,
                "log_level": log_record.levelname,
                "module": log_record.module,
                "line_number": log_record.lineno,
                **(source_info or {}),
            },
        )

        self.errors.append(entry)

    def has_errors(self) -> bool:
        """Check if any errors have been collected.

        Returns:
            bool: True if errors exist, False otherwise
        """
        return len(self.errors) > 0

    def get_error_count(self) -> int:
        """Get the total number of errors collected.

        Returns:
            int: Number of errors in the collection
        """
        return len(self.errors)

    def get_errors_by_type(self) -> dict[str, list[ErrorEntry]]:
        """Group errors by type (exception vs log).

        Returns:
            dict: Errors grouped by type
        """
        grouped: dict[str, list[ErrorEntry]] = {"exception": [], "log": []}
        for error in self.errors:
            grouped[error.error_type].append(error)
        return grouped

    def get_chronological_errors(self) -> list[ErrorEntry]:
        """Get all errors sorted by timestamp.

        Returns:
            list[ErrorEntry]: Errors sorted chronologically
        """
        return sorted(self.errors, key=lambda e: e.timestamp)

    def clear(self) -> None:
        """Clear all collected errors."""
        self.errors.clear()

    def get_summary(self) -> str:
        """Get a brief summary of collected errors.

        Returns:
            str: Summary string
        """
        if not self.errors:
            return "No errors collected"

        error_types = self.get_errors_by_type()
        exception_count = len(error_types["exception"])
        log_count = len(error_types["log"])

        parts = []
        if exception_count > 0:
            parts.append(
                f"{exception_count} exception{'s' if exception_count != 1 else ''}"
            )
        if log_count > 0:
            parts.append(f"{log_count} log error{'s' if log_count != 1 else ''}")

        return f"Collected {' and '.join(parts)} from {self.function_name}"


# Thread-local storage for error collection and function context
_thread_local = local()


class ErrorCollectionContext:
    """Context manager for error collection in thread-local storage."""

    def __init__(self, collection: ErrorCollection):
        """Initialize context with error collection.

        Args:
            collection: The error collection to store in thread-local storage
        """
        self.collection = collection
        self.previous_collection = None

    def __enter__(self) -> ErrorCollection:
        """Enter context and set up thread-local storage."""
        # Store any previous collection (for nested calls)
        self.previous_collection = getattr(_thread_local, "error_collection", None)

        # Set the current collection
        _thread_local.error_collection = self.collection
        _thread_local.function_context = {
            "name": self.collection.function_name,
            "args": self.collection.function_args,
            "kwargs": self.collection.function_kwargs,
        }

        return self.collection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context and clean up thread-local storage."""
        # Restore previous collection or clear
        if self.previous_collection is not None:
            _thread_local.error_collection = self.previous_collection
        else:
            if hasattr(_thread_local, "error_collection"):
                delattr(_thread_local, "error_collection")

        if hasattr(_thread_local, "function_context"):
            delattr(_thread_local, "function_context")


def get_current_error_collection() -> ErrorCollection | None:
    """Get the current error collection from thread-local storage.

    Returns:
        ErrorCollection | None: Current error collection, or None if not active
    """
    return getattr(_thread_local, "error_collection", None)


def get_current_function_context() -> dict[str, Any] | None:
    """Get the current function context from thread-local storage.

    Returns:
        dict | None: Current function context, or None if not active
    """
    return getattr(_thread_local, "function_context", None)
