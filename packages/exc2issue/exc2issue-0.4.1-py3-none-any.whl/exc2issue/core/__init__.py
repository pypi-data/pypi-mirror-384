"""Core functionality for exc2issue automatic GitHub issue creation.

This module provides the core decorator functionality split into modular components:

- decorator: Main BugHunterDecorator class and decorator logic
- registry: Global registry management for active decorators and queues
- background_worker: Background processing for issue creation with retry logic
- signal_handling: Signal and exit handlers for graceful shutdown
- issue_creator: GitHub issue creation logic (consolidated and individual)

The core modules provide the foundation for the exc2issue decorator while
maintaining clean separation of concerns and manageable file sizes.
"""

from exc2issue.core.decorator import BugHunterDecorator, exc2issue
from exc2issue.core.models import ErrorRecord, GitHubIssue

__all__ = [
    "BugHunterDecorator",
    "exc2issue",
    "ErrorRecord",
    "GitHubIssue",
]
