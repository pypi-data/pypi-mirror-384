"""Task queue management for exc2issue.

This module provides task queuing functionality to break circular dependencies
between issue_creator and background_worker modules.
"""

from exc2issue.core.registry import get_issue_queue
from exc2issue.core.task_types import IssueCreationTask


def queue_issue_creation_task(task: IssueCreationTask) -> None:
    """Queue an issue creation task for background processing.

    Args:
        task: IssueCreationTask to be processed by the background worker
    """
    get_issue_queue().put(task)
