"""Shared types for exc2issue.

This module contains types that are shared across different modules
to prevent circular import issues. These types have no dependencies
on core or adapter modules.
"""

from dataclasses import dataclass


@dataclass
class IssueCreationOptions:
    """Options for GitHub issue creation.

    Groups parameters for consolidated issue creation.
    Moved to this module to prevent circular imports between
    core.config_types and adapters.github modules.
    """

    labels: list[str]
    assignees: list[str] | None = None
    gemini_description: str | None = None
