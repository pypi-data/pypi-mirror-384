"""Data models for exc2issue.

This module defines the core data models used throughout the exc2issue library:
- ErrorRecord: Captures details about errors and exceptions
- GitHubIssue: Represents the structure of a GitHub issue to be created

All models use Pydantic for validation, serialization, and type safety.
"""

import json
import traceback as tb
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from exc2issue.core.config_types import ErrorContext


class ErrorRecord(BaseModel):
    """Represents a captured error or exception with all relevant context.

    This Pydantic model stores all the information needed to create a meaningful
    GitHub issue from an error that occurred in a decorated function.

    Attributes:
        function_name: Name of the function where the error occurred
        error_type: The type of error (e.g., "ValueError", "RuntimeError")
        error_message: The error message or description
        timestamp: When the error was captured
        traceback: Stack trace information
        function_args: Function arguments (optional)
        function_kwargs: Function keyword arguments (optional)
        context: Additional context information (optional)
    """

    function_name: str = Field(
        description="Name of the function where the error occurred", min_length=1
    )
    error_type: str = Field(
        description="The type of error (e.g., 'ValueError', 'RuntimeError')",
        min_length=1,
    )
    error_message: str = Field(
        description="The error message or description", min_length=1
    )
    timestamp: datetime = Field(description="When the error was captured")
    traceback: str = Field(description="Stack trace information")
    function_args: list[Any] | None = Field(
        default=None, description="Function arguments (optional)"
    )
    function_kwargs: dict[str, Any] | None = Field(
        default=None, description="Function keyword arguments (optional)"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Additional context information (optional)"
    )

    @field_validator("function_name")
    @classmethod
    def validate_function_name(cls, v: str) -> str:
        """Validate function name format."""
        if not v.strip():
            raise ValueError("function_name must be non-empty")
        return v

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, v: str) -> str:
        """Validate error type is non-empty."""
        if not v.strip():
            raise ValueError("error_type must be non-empty")
        return v

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v: str) -> str:
        """Validate error message is non-empty."""
        if not v.strip():
            raise ValueError("error_message must be non-empty")
        return v

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        function_name: str,
        *,
        error_context: ErrorContext | None = None,
    ) -> "ErrorRecord":
        """Create ErrorRecord from an exception.

        Args:
            exception: The caught exception
            function_name: Name of the function where error occurred
            error_context: Optional context information (function args, kwargs, extra context)

        Returns:
            ErrorRecord: New error record instance
        """
        ctx = error_context or ErrorContext()
        return cls(
            function_name=function_name,
            error_type=type(exception).__name__,
            error_message=str(exception),
            timestamp=datetime.now(),
            traceback=tb.format_exc(),
            function_args=ctx.function_args,
            function_kwargs=ctx.function_kwargs,
            context=ctx.context,
        )

    def get_summary(self) -> str:
        """Get a short summary of the error record.

        Returns:
            str: Brief summary of the error
        """
        return f"{self.error_type} in {self.function_name}: {self.error_message}"

    def _format_timestamp(self) -> str | None:
        """Format timestamp for serialization.

        Returns:
            str | None: ISO formatted timestamp or None if not available
        """
        try:
            # Access timestamp attribute safely
            timestamp_val: object | None = getattr(self, "timestamp", None)
            if isinstance(timestamp_val, datetime):
                return timestamp_val.isoformat()
        except AttributeError:
            pass
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert ErrorRecord to dictionary for serialization.

        Maintains backward compatibility with existing code.
        """
        return {
            "function_name": self.function_name,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self._format_timestamp(),
            "traceback": self.traceback,
            "function_args": self.function_args,
            "function_kwargs": self.function_kwargs,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ErrorRecord":
        """Create ErrorRecord from dictionary.

        Maintains backward compatibility with existing code.
        """
        timestamp_str = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        )

        return cls(
            function_name=data["function_name"],
            error_type=data["error_type"],
            error_message=data["error_message"],
            timestamp=timestamp,
            traceback=data.get("traceback", ""),
            function_args=data.get("function_args"),
            function_kwargs=data.get("function_kwargs"),
            context=data.get("context"),
        )

    def __repr__(self) -> str:
        """String representation of ErrorRecord."""
        return (
            f"ErrorRecord(function_name='{self.function_name}', "
            f"error_type='{self.error_type}', "
            f"error_message='{self.error_message[:50]}...')"
        )


class GitHubIssue(BaseModel):
    """Represents the structure of a GitHub issue to be created.

    This Pydantic model encapsulates all the data needed to create a GitHub issue
    through the GitHub API, including title, body, labels, and assignees.

    Attributes:
        title: Issue title (will be truncated if too long)
        body: Issue description/body content
        labels: List of labels to apply to the issue
        assignees: List of GitHub usernames to assign the issue to
    """

    title: str = Field(
        description="Issue title (will be truncated if too long)",
        min_length=1,
        max_length=256,
    )
    body: str = Field(description="Issue description/body content", min_length=1)
    labels: list[str] = Field(
        default_factory=list, description="List of labels to apply to the issue"
    )
    assignees: list[str] = Field(
        default_factory=list,
        description="List of GitHub usernames to assign the issue to",
    )

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, v: str) -> str:
        """Validate and truncate title if necessary."""
        v = v.strip()
        if not v:
            raise ValueError("Issue title cannot be empty")
        # GitHub has a 256 character limit for titles
        # The max_length constraint handles this automatically
        return v

    @field_validator("body")
    @classmethod
    def validate_body_not_empty(cls, v: str) -> str:
        """Validate body is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Issue body cannot be empty")
        return v

    @field_validator("labels")
    @classmethod
    def validate_labels_are_strings(cls, v: list[str]) -> list[str]:
        """Validate all labels are non-empty strings."""
        if not isinstance(v, list):
            raise ValueError("Labels must be a list")
        for label in v:
            if not isinstance(label, str):
                raise ValueError(f"All labels must be strings, got {type(label)}")
            if not label.strip():
                raise ValueError("Labels cannot be empty strings")
        return v

    @field_validator("assignees")
    @classmethod
    def validate_assignees_format(cls, v: list[str]) -> list[str]:
        """Validate assignees are valid GitHub username formats."""
        if not isinstance(v, list):
            raise ValueError("Assignees must be a list")
        for assignee in v:
            if not isinstance(assignee, str):
                raise ValueError(f"All assignees must be strings, got {type(assignee)}")
            if not assignee.strip():
                raise ValueError("Assignees cannot be empty strings")
            # Basic GitHub username validation
            clean_assignee = assignee.strip()
            if not clean_assignee.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f"Assignee '{clean_assignee}' is not a valid GitHub username format"
                )
            if len(clean_assignee) > 39:  # GitHub username max length
                raise ValueError(
                    f"Assignee '{clean_assignee}' exceeds GitHub username length limit"
                )
        return [assignee.strip() for assignee in v]

    @classmethod
    def from_error_record(
        cls,
        error_record: "ErrorRecord",
        ai_description: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> "GitHubIssue":
        """Create GitHubIssue from an ErrorRecord.

        Args:
            error_record: The error record to create issue from
            ai_description: AI-generated description (optional)
            labels: List of labels to apply (optional)
            assignees: List of assignees (optional)

        Returns:
            GitHubIssue: New GitHub issue instance
        """
        # Create title from error information
        title = f"{error_record.error_type} in {error_record.function_name}"

        # Create body with error details and AI description
        body_parts = [
            f"**Error Type:** {error_record.error_type}",
            f"**Function:** {error_record.function_name}",
            f"**Message:** {error_record.error_message}",
            f"**Timestamp:** {error_record.timestamp.isoformat()}",
        ]

        if error_record.function_args:
            body_parts.append(f"**Arguments:** {error_record.function_args}")

        if error_record.function_kwargs:
            body_parts.append(f"**Keyword Arguments:** {error_record.function_kwargs}")

        if error_record.context:
            body_parts.append(
                f"**Context:** {json.dumps(error_record.context, indent=2)}"
            )

        if ai_description:
            body_parts.append(f"\n**Analysis:** {ai_description}")

        if error_record.traceback:
            body_parts.append(f"\n**Traceback:**\n```\n{error_record.traceback}\n```")

        body = "\n\n".join(body_parts)

        return cls(
            title=title,
            body=body,
            labels=labels or [],
            assignees=assignees or [],
        )

    def to_github_format(self) -> dict[str, Any]:
        """Convert GitHubIssue to GitHub API format.

        Returns:
            dict: GitHub API compatible format
        """
        return {
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
            "assignees": self.assignees,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert GitHubIssue to dictionary suitable for GitHub API.

        Maintains backward compatibility with existing code.
        """
        return {
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
            "assignees": self.assignees,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GitHubIssue":
        """Create GitHubIssue from dictionary.

        Maintains backward compatibility with existing code.
        """
        # Handle both old 'assignee' (singular) and new 'assignees' (plural) formats
        assignees = data.get("assignees", [])
        if "assignee" in data and data["assignee"]:
            assignees = [data["assignee"]]

        return cls(
            title=data["title"],
            body=data["body"],
            labels=data.get("labels", []),
            assignees=assignees,
        )

    def validate_data(self) -> None:
        """Validate the issue data (legacy compatibility method).

        This method is maintained for backward compatibility.
        Pydantic validation occurs automatically during model creation.
        Use this method if you need explicit validation in legacy code.

        Raises:
            ValueError: If title is empty or body is empty
        """
        # Pydantic handles validation automatically, but we keep this method
        # for backward compatibility
        title_value = str(self.title) if self.title else ""
        if not title_value or not title_value.strip():
            raise ValueError("Issue title cannot be empty")

        body_value = str(self.body) if self.body else ""
        if not body_value or not body_value.strip():
            raise ValueError("Issue body cannot be empty")

    def __repr__(self) -> str:
        """String representation of GitHubIssue."""
        return (
            f"GitHubIssue(title='{self.title[:30]}...', "
            f"labels={self.labels}, assignees={self.assignees})"
        )
