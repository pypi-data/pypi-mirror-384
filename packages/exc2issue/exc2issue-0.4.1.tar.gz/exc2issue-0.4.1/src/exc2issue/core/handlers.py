"""Clean handler classes for exceptions and log errors.

This module provides the ExceptionHandler and LogHandler classes that capture
errors and add them to the error collection instead of immediately creating
GitHub issues. This enables consolidated error handling and issue creation.
"""

import contextlib
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from exc2issue.core.error_collection import (
    get_current_error_collection,
    get_current_function_context,
)

if TYPE_CHECKING:
    from exc2issue.core.decorator import BugHunterDecorator

logger = logging.getLogger(__name__)


class ExceptionHandler:
    """Handler for exceptions that adds them to the current error collection."""

    def __init__(self, decorator_instance: "BugHunterDecorator"):
        """Initialize exception handler.

        Args:
            decorator_instance: Reference to the decorator instance
        """
        self.decorator_instance = decorator_instance

    def handle_exception(self, exception: Exception, func: Callable[..., Any]) -> None:
        """Handle an exception by adding it to the current error collection.

        Args:
            exception: The caught exception
            func: Function where the exception occurred
        """
        # Get the current error collection from thread-local storage
        error_collection = get_current_error_collection()

        if error_collection is not None:
            logger.debug(
                "Adding exception to error collection",
                extra={
                    "function": func.__name__,
                    "error_type": type(exception).__name__
                }
            )
            # Add exception to the collection with additional context
            source_info = self._create_source_info(exception, func)
            error_collection.add_exception(
                exception=exception, func=func, source_info=source_info
            )
        else:
            # Fallback: log a warning if no error collection is active
            # This shouldn't happen in normal operation
            logger.warning(
                "ExceptionHandler called but no error collection active",
                extra={
                    "function": func.__name__,
                    "error_type": type(exception).__name__,
                    "error_message": str(exception)
                }
            )

    def _create_source_info(
        self, exception: Exception, func: Callable[..., Any]
    ) -> dict[str, Any]:
        """Create source info dictionary for exception context.

        Args:
            exception: The caught exception
            func: Function where the exception occurred

        Returns:
            dict: Source information dictionary
        """
        return {
            "decorator_instance": self.decorator_instance,
            "exception_class": exception.__class__.__module__
            + "."
            + exception.__class__.__name__,
            "function_module": getattr(func, "__module__", "unknown"),
            "function_file": getattr(func, "__code__", None)
            and func.__code__.co_filename,
            "function_line": getattr(func, "__code__", None)
            and func.__code__.co_firstlineno,
        }

    def is_error_collection_active(self) -> bool:
        """Check if there is an active error collection.

        Returns:
            bool: True if error collection is active, False otherwise
        """
        return get_current_error_collection() is not None


class LogHandler(logging.Handler):
    """Logging handler that adds log errors to the current error collection."""

    def __init__(self, decorator_instance: "BugHunterDecorator"):
        """Initialize log handler.

        Args:
            decorator_instance: Reference to the decorator instance
        """
        super().__init__()
        self.decorator_instance = decorator_instance
        self.setLevel(logging.ERROR)

    def emit(self, record: logging.LogRecord) -> None:
        """Called when a log record is emitted.

        Args:
            record: The logging record
        """
        # Only process ERROR and CRITICAL level logs
        if record.levelno < logging.ERROR:
            return

        # Ignore logs from exc2issue.core modules to prevent circular logging
        # This prevents the decorator's internal error logging from being
        # captured as additional errors in the collection
        if record.name.startswith('exc2issue.core'):
            return

        # Get the current error collection and function context
        error_collection = get_current_error_collection()
        function_context = get_current_function_context()

        if error_collection is not None and function_context is not None:
            # Create a mock function object to match the interface
            mock_func = self._create_mock_function(function_context["name"])

            # Add log error to the collection with additional context
            source_info = {
                "decorator_instance": self.decorator_instance,
                "record_pathname": record.pathname,
                "record_funcName": record.funcName,
                "record_thread": record.thread,
                "record_threadName": record.threadName,
                "record_process": record.process,
                "record_processName": record.processName,
            }

            error_collection.add_log_error(
                log_record=record, func=mock_func, source_info=source_info
            )
        else:
            # This is normal - log errors outside of decorated functions are ignored
            pass

    def _create_mock_function(self, function_name: str) -> Any:
        """Create a mock function object to represent log source.

        Args:
            function_name: Name of the function to mock

        Returns:
            Mock function object with __name__ attribute
        """

        class MockFunction:
            """Mock function class to represent log source for error collection."""

            def __init__(self, name: str):
                self.__name__ = name

            def __call__(self, *args: Any, **kwargs: Any) -> Any:
                pass  # Mock function does nothing

            def get_name(self) -> str:
                """Get the function name."""
                return self.__name__

        return MockFunction(function_name)

    def get_decorator_instance(self) -> "BugHunterDecorator":
        """Get the decorator instance associated with this handler.

        Returns:
            BugHunterDecorator: The decorator instance
        """
        return self.decorator_instance

    def handle(self, record: logging.LogRecord) -> bool:
        """Override handle to prevent recursion issues.

        Args:
            record: The logging record

        Returns:
            bool: True to indicate the record was handled
        """
        with contextlib.suppress(Exception):
            # Silently ignore errors in log handling to prevent recursion
            # and interference with the original function execution
            self.emit(record)
        return True


class ConsolidatedHandlers:
    """Container for both exception and log handlers with shared configuration."""

    def __init__(self, decorator_instance: "BugHunterDecorator"):
        """Initialize both handlers.

        Args:
            decorator_instance: Reference to the decorator instance
        """
        self.decorator_instance = decorator_instance
        self.exception_handler = ExceptionHandler(decorator_instance)
        self.log_handler = LogHandler(decorator_instance)

        # Add the log handler to the root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)

    def handle_exception(self, exception: Exception, func: Callable[..., Any]) -> None:
        """Handle an exception using the exception handler.

        Args:
            exception: The caught exception
            func: Function where the exception occurred
        """
        self.exception_handler.handle_exception(exception, func)

    def cleanup(self) -> None:
        """Clean up handlers and remove from logging system."""
        # Remove the log handler from the root logger
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.log_handler)

    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        with contextlib.suppress(Exception):
            self.cleanup()
