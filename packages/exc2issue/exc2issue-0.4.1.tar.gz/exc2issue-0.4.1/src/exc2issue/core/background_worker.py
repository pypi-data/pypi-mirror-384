"""Background worker for asynchronous GitHub issue creation.

This module provides the background processing system for creating GitHub issues
with retry logic and proper error handling. The worker runs in a separate thread
and processes tasks from a queue to ensure reliable issue creation even when
the main application thread terminates unexpectedly.

Key components:
- BackgroundIssueWorker: Worker class that processes tasks from the queue
- Worker thread management and lifecycle functions
- Task queue management functions
"""

import logging
from queue import Empty
from threading import Thread

import requests

from exc2issue.core.issue_creator import create_consolidated_issue
from exc2issue.core.registry import (
    get_background_worker,
    get_issue_queue,
    is_shutdown_requested,
    set_background_worker,
)


class BackgroundIssueWorker:
    """Background worker that processes consolidated issue creation tasks.

    This worker runs in a separate daemon thread and continuously processes
    issue creation tasks from the global queue. It handles retries and
    proper error logging when issue creation fails.
    """

    @staticmethod
    def is_running() -> bool:
        """Check if a background worker is currently running.

        Returns:
            True if a background worker thread is alive, False otherwise
        """
        current_worker = get_background_worker()
        return current_worker is not None and current_worker.is_alive()

    @staticmethod
    def process_issues() -> None:
        """Process issue creation tasks from the queue in background.

        This is the main worker loop that runs in the background thread.
        It processes tasks until shutdown is requested.
        """
        logger = logging.getLogger(__name__)
        logger.debug("Enhanced background issue worker started")

        while not is_shutdown_requested():
            try:
                # Wait for task with timeout
                task = get_issue_queue().get(timeout=1.0)
                logger.debug(
                    "Processing consolidated issue creation task: %s", task.task_id
                )

                try:
                    task.attempts += 1

                    create_consolidated_issue(
                        task.decorator_instance, task.error_collection
                    )
                    logger.debug(
                        "Successfully created consolidated issue for task: %s",
                        task.task_id,
                    )

                except (requests.RequestException, ValueError, ImportError) as e:
                    logger.warning(
                        "Failed to create consolidated issue (attempt %s/%s): %s",
                        task.attempts,
                        task.max_attempts,
                        e,
                    )

                    # Retry if under max attempts
                    if task.attempts < task.max_attempts:
                        get_issue_queue().put(task)
                    else:
                        logger.error(
                            "Exhausted all attempts for consolidated task %s: %s",
                            task.task_id,
                            e,
                        )

                finally:
                    get_issue_queue().task_done()

            except Empty:
                # Timeout occurred, continue loop
                continue
            except (RuntimeError, ValueError, AttributeError, TypeError, OSError) as e:
                # Catch common exceptions to prevent background thread from crashing
                logger.error("Unexpected error in enhanced background worker: %s", e)

        logger.debug("Enhanced background issue worker stopped")


def ensure_background_worker() -> None:
    """Ensure background worker thread is running.

    This function checks if the background worker is alive and starts a new
    one if needed. It's called automatically when background processing is enabled.
    """
    current_worker = get_background_worker()

    if current_worker is None or not current_worker.is_alive():
        worker = Thread(
            target=BackgroundIssueWorker.process_issues,
            daemon=True,
            name="BugHunterWorker",
        )
        set_background_worker(worker)
        worker.start()


def shutdown_background_worker(timeout: float = 5.0) -> None:
    """Shutdown the background worker and wait for completion.

    Args:
        timeout: Maximum time to wait for worker shutdown in seconds
    """
    current_worker = get_background_worker()
    if current_worker and current_worker.is_alive():
        current_worker.join(timeout=timeout)
