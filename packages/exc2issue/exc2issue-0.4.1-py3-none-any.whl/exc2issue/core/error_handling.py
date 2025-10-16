"""Error handling utilities for decorator termination scenarios.

This module provides utilities for handling special error cases that occur
during decorated function execution, particularly related to:

- SystemExit handling when functions call sys.exit()
- Signal termination error record creation
- Exit cleanup error record creation
- Error collection integration for termination events

These utilities are used by the main decorator to ensure comprehensive
error capture even during abnormal termination scenarios.
"""

import logging
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from exc2issue.core.error_collection import ErrorCollection, ErrorEntry
from exc2issue.core.issue_creator import create_consolidated_issue
from exc2issue.core.models import ErrorRecord
from exc2issue.core.signal_handling import (
    create_exit_error_record,
    create_signal_error_record,
)


def handle_system_exit(
    exit_exception: SystemExit,
    func: Callable[..., Any],
    error_collection: ErrorCollection,
) -> None:
    """Handle sys.exit() scenarios by adding to error collection.

    This function creates an error record when a decorated function calls
    sys.exit() and adds it to the current error collection for processing.

    Args:
        exit_exception: The SystemExit exception that was raised
        func: Function that called sys.exit()
        error_collection: Collection to add the error record to
    """
    logger = logging.getLogger(__name__)
    logger.warning("SystemExit detected in %s", func.__name__)

    # Create error record for sys.exit and add to collection
    error_record = ErrorRecord(
        function_name=func.__name__,
        error_type="SystemExit",
        error_message=f"Function called sys.exit() with code: {exit_exception.code}",
        timestamp=datetime.now(UTC),
        traceback=traceback.format_exc(),
        function_args=(
            list(error_collection.function_args)
            if error_collection.function_args
            else None
        ),
        function_kwargs=(
            dict(error_collection.function_kwargs)
            if error_collection.function_kwargs
            else None
        ),
    )

    # Add to error collection manually
    entry = ErrorEntry(
        error_type="exception",
        timestamp=datetime.now(UTC),
        error_record=error_record,
        source_info={
            "termination_type": "SystemExit",
            "exit_code": exit_exception.code,
        },
    )
    error_collection.errors.append(entry)


def handle_signal_termination(
    decorator_instance: Any, signum: int, _frame: Any
) -> None:
    """Handle signal-based termination by creating consolidated issue.

    This function is called when a signal is received while a decorator
    is active. It creates an error record for the signal and processes
    it immediately since we may not have time for background processing.

    Args:
        decorator_instance: The active decorator instance (BugHunterDecorator)
        signum: Signal number that was received
        frame: Current stack frame (unused)
    """
    if (
        not decorator_instance.is_active()
        or not decorator_instance.get_current_error_collection()
    ):
        return

    logger = logging.getLogger(__name__)
    logger.warning("Signal %s received while decorator active", signum)

    # Create error record for signal termination
    current_collection = decorator_instance.get_current_error_collection()
    error_record = create_signal_error_record(
        signum,
        current_collection.function_name,
        current_collection.function_args,
        current_collection.function_kwargs,
    )

    # Add to current error collection
    entry = ErrorEntry(
        error_type="exception",
        timestamp=datetime.now(UTC),
        error_record=error_record,
        source_info={"termination_type": "signal", "signal_number": signum},
    )
    current_collection.errors.append(entry)

    # Process consolidated errors synchronously (we might not have time for background processing)
    create_consolidated_issue(decorator_instance, current_collection)


def handle_exit_cleanup(decorator_instance: Any) -> None:
    """Handle exit cleanup for sys.exit() scenarios.

    This function is called during process exit to handle any decorator
    that was active when the process began termination. It creates an
    error record and processes it synchronously.

    Args:
        decorator_instance: The active decorator instance (BugHunterDecorator)
    """
    if (
        not decorator_instance.is_active()
        or not decorator_instance.get_current_error_collection()
    ):
        return

    logger = logging.getLogger(__name__)
    logger.warning("Bug hunter exit handler triggered while decorator active")

    # Create error record for exit cleanup
    current_collection = decorator_instance.get_current_error_collection()
    error_record = create_exit_error_record(
        current_collection.function_name,
        current_collection.function_args,
        current_collection.function_kwargs,
    )

    # Add to current error collection
    entry = ErrorEntry(
        error_type="exception",
        timestamp=datetime.now(UTC),
        error_record=error_record,
        source_info={"termination_type": "process_exit"},
    )
    current_collection.errors.append(entry)

    # Process consolidated errors synchronously
    create_consolidated_issue(decorator_instance, current_collection)
