"""Registry management for exc2issue decorators and background processing.

This module manages the global state for the exc2issue system including:
- Active decorator registry using weak references for automatic cleanup
- Issue creation task queue for background processing
- Background worker thread management
- Shutdown coordination event

The registry provides thread-safe access patterns and ensures proper cleanup
when decorators are no longer in use.
"""

import weakref
from dataclasses import dataclass, field
from queue import Queue
from threading import Event, Thread
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from exc2issue.core.decorator import BugHunterDecorator


@dataclass
class _RegistryState:
    """Internal registry state holder to avoid global statement usage."""

    active_decorators: weakref.WeakSet["BugHunterDecorator"] = field(
        default_factory=weakref.WeakSet
    )
    issue_queue: Queue[Any] = field(default_factory=Queue)
    background_worker: Thread | None = None
    shutdown_event: Event = field(default_factory=Event)


# Global registry state - single instance to avoid global statements
_registry = _RegistryState()


def get_active_decorators() -> weakref.WeakSet["BugHunterDecorator"]:
    """Get the set of currently active decorators.

    Returns:
        weakref.WeakSet: WeakSet of active BugHunterDecorator instances
    """
    return _registry.active_decorators


def add_active_decorator(decorator: "BugHunterDecorator") -> None:
    """Add a decorator to the active registry.

    Args:
        decorator: BugHunterDecorator instance to register (accepts Self type)
    """
    _registry.active_decorators.add(decorator)


def get_issue_queue() -> Queue[Any]:
    """Get the global issue creation task queue.

    Returns:
        Queue: Global queue for IssueCreationTask objects
    """
    return _registry.issue_queue


def get_background_worker() -> Thread | None:
    """Get the current background worker thread.

    Returns:
        Thread | None: Current background worker thread or None if not running
    """
    return _registry.background_worker


def set_background_worker(worker: Thread) -> None:
    """Set the background worker thread.

    Args:
        worker: New background worker thread
    """
    _registry.background_worker = worker


def get_shutdown_event() -> Event:
    """Get the global shutdown coordination event.

    Returns:
        Event: Event object for coordinating shutdown across threads
    """
    return _registry.shutdown_event


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested.

    Returns:
        bool: True if shutdown has been requested, False otherwise
    """
    return _registry.shutdown_event.is_set()


def request_shutdown() -> None:
    """Request shutdown of background processing."""
    _registry.shutdown_event.set()


def reset_shutdown_event() -> None:
    """Reset the shutdown event (mainly for testing)."""
    _registry.shutdown_event.clear()
