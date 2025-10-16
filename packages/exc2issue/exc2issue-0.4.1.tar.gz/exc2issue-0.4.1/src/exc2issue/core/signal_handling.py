"""Signal and exit handlers for graceful exc2issue shutdown.

This module handles system signals and exit scenarios to ensure GitHub issues
are created even when the application terminates unexpectedly. It provides:

- Global signal handlers for SIGTERM, SIGINT, and SIGHUP
- Exit handlers for sys.exit() scenarios
- Graceful shutdown coordination with background workers
- Error collection for termination events

The handlers ensure that any active decorated functions get their errors
processed and converted to GitHub issues before the process terminates.
"""

import atexit
import logging
import os
import signal
import time
from datetime import UTC, datetime
from typing import Any

from exc2issue.core.background_worker import shutdown_background_worker
from exc2issue.core.models import ErrorRecord
from exc2issue.core.registry import get_active_decorators, request_shutdown


def setup_signal_handlers() -> None:
    """Setup global signal handlers for graceful shutdown.

    Registers handlers for SIGTERM, SIGINT, and SIGHUP (if available).
    These handlers will process any active decorators before allowing
    the process to terminate.
    """
    try:
        signal.signal(signal.SIGTERM, _global_signal_handler)
        signal.signal(signal.SIGINT, _global_signal_handler)
        # SIGHUP might not be available on all platforms
        if hasattr(signal, "SIGHUP"):
            signal.signal(signal.SIGHUP, _global_signal_handler)
    except (OSError, ValueError) as e:
        logging.getLogger(__name__).warning("Could not register signal handlers: %s", e)


def setup_exit_handler() -> None:
    """Setup exit handler for sys.exit() scenarios.

    Registers an atexit handler that will process any active decorators
    when the Python process exits normally or via sys.exit().
    """
    atexit.register(_global_exit_handler)


def _global_signal_handler(signum: int, frame: Any) -> None:
    """Global signal handler for all active bug hunter decorators.

    This handler is called when the process receives SIGTERM, SIGINT, or SIGHUP.
    It processes all active decorators to ensure their errors are captured
    before the process terminates.

    Args:
        signum: Signal number that was received
        frame: Current stack frame (unused)
    """
    logger = logging.getLogger(__name__)
    logger.warning("Signal %s received, processing bug hunter decorators", signum)

    # Process all active decorators
    active_decorators = list(get_active_decorators())
    for decorator in active_decorators:
        try:
            decorator.handle_signal_termination(signum, frame)
        except (OSError, RuntimeError, ValueError, KeyError, TypeError) as e:
            # Catch common exceptions during signal handling to prevent handler crashes
            logger.error("Error handling signal in bug hunter decorator: %s", e)

    # Wait briefly for issue creation
    time.sleep(2)

    # Original signal behavior - restore default handler and re-raise signal
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


def _global_exit_handler() -> None:
    """Global exit handler for sys.exit() scenarios.

    This handler is called when the Python process exits normally or via
    sys.exit(). It ensures any active decorators have their errors processed
    and shuts down the background worker gracefully.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Bug hunter exit handler triggered, processing active decorators")

    # Process all active decorators
    active_decorators = list(get_active_decorators())
    for decorator in active_decorators:
        try:
            decorator.handle_exit_cleanup()
        except (OSError, RuntimeError, ValueError, KeyError, TypeError) as e:
            # Catch common exceptions during exit cleanup to prevent handler crashes
            logger.error("Error in bug hunter exit cleanup: %s", e)

    # Shutdown background worker
    request_shutdown()
    shutdown_background_worker(timeout=5)


def create_signal_error_record(
    signum: int,
    function_name: str,
    function_args: tuple[Any, ...] | None,
    function_kwargs: dict[str, Any] | None,
) -> ErrorRecord:
    """Create an error record for signal termination.

    Args:
        signum: Signal number that caused termination
        function_name: Name of the function that was active
        function_args: Arguments of the active function
        function_kwargs: Keyword arguments of the active function

    Returns:
        ErrorRecord: Error record representing the signal termination
    """

    # Map common signal numbers to names
    signal_names = {
        getattr(signal, "SIGTERM", 15): "SIGTERM",
        getattr(signal, "SIGINT", 2): "SIGINT",
        getattr(signal, "SIGHUP", 1): "SIGHUP",
    }

    signal_name = signal_names.get(signum, f"Signal{signum}")

    return ErrorRecord(
        function_name=function_name,
        error_type=signal_name,
        error_message=f"Process terminated by {signal_name}",
        timestamp=datetime.now(UTC),
        traceback="",  # No traceback available for signals
        function_args=list(function_args) if function_args else None,
        function_kwargs=dict(function_kwargs) if function_kwargs else None,
    )


def create_exit_error_record(
    function_name: str, function_args: tuple[Any, ...] | None, function_kwargs: dict[str, Any] | None
) -> ErrorRecord:
    """Create an error record for process exit.

    Args:
        function_name: Name of the function that was active
        function_args: Arguments of the active function
        function_kwargs: Keyword arguments of the active function

    Returns:
        ErrorRecord: Error record representing the process exit
    """

    return ErrorRecord(
        function_name=function_name,
        error_type="ProcessExit",
        error_message="Process exiting while decorated function was active",
        timestamp=datetime.now(UTC),
        traceback="",
        function_args=list(function_args) if function_args else None,
        function_kwargs=dict(function_kwargs) if function_kwargs else None,
    )
