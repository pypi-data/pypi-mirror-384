"""Shared task types for exc2issue background processing.

This module contains task type definitions used by both the background worker
and issue creation modules. By placing these in a separate module, we avoid
cyclic imports between background_worker.py and issue_creator.py.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from exc2issue.core.error_collection import ErrorCollection


@dataclass
class IssueCreationTask:
    """Represents a task to create a GitHub issue with retry logic.

    This class encapsulates all the information needed to create a GitHub issue
    including the error collection, decorator instance, and retry metadata.

    Note: decorator_instance accepts both BugHunterDecorator and Self types.
    """

    error_collection: ErrorCollection
    decorator_instance: Any  # BugHunterDecorator or compatible type (Self)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    attempts: int = 0
    max_attempts: int = 3
