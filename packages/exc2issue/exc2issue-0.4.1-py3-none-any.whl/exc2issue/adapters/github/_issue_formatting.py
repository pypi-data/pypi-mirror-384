"""Issue formatting utilities for the GitHub client.

This module contains functions for converting ErrorRecord and ErrorCollection objects
into formatted GitHub issues with proper markdown content.
"""

from typing import TYPE_CHECKING

from exc2issue.core.models import ErrorRecord, GitHubIssue
from exc2issue.core.utils import generate_deterministic_title, sanitize_function_name

if TYPE_CHECKING:
    from exc2issue.core.error_collection import ErrorCollection, ErrorEntry


def convert_error_to_issue(
    error_record: ErrorRecord,
    labels: list[str],
    assignees: list[str] | None = None,
) -> GitHubIssue:
    """Convert ErrorRecord to GitHubIssue.

    Args:
        error_record: ErrorRecord containing error details
        labels: List of labels to apply to the issue
        assignees: List of GitHub usernames to assign the issue to

    Returns:
        GitHubIssue object ready for creation
    """
    # Generate deterministic title from error information

    sanitized_function_name = sanitize_function_name(error_record.function_name)
    title = generate_deterministic_title(
        sanitized_function_name, error_record.error_type, error_record.error_message
    )

    # Truncate title if too long (GitHub has a 256 character limit)
    if len(title) > 256:
        title = title[:253] + "..."

    # Generate body with all available information
    body_parts = [
        "## Error Details",
        f"**Function:** `{error_record.function_name}`",
        f"**Error Type:** {error_record.error_type}",
        f"**Error Message:** {error_record.error_message}",
        f"**Timestamp:** {
            (
                error_record.timestamp.isoformat()
                if error_record.timestamp
                else 'Unknown'
            )
        }",
        "",
        "## Function Arguments",
        f"```\n{error_record.function_args}\n```",
    ]

    if error_record.traceback:
        body_parts.extend(["", "## Stack Trace", f"```\n{error_record.traceback}\n```"])

    body_parts.extend(
        [
            "",
            "---",
            "*This issue was automatically created by "
            "[exc2issue](https://github.com/exc2issue/exc2issue)*",
        ]
    )

    body = "\n".join(body_parts)

    assignees_list = assignees or []
    return GitHubIssue(title=title, body=body, labels=labels, assignees=assignees_list)


def convert_error_collection_to_issue(
    error_collection: "ErrorCollection",
    labels: list[str],
    assignees: list[str] | None = None,
    gemini_description: str | None = None,
) -> GitHubIssue:
    """Convert ErrorCollection to GitHubIssue (single or consolidated).

    Args:
        error_collection: Collection of errors from a single function execution
        labels: List of labels to apply to the issue
        assignees: List of GitHub usernames to assign the issue to
        gemini_description: Optional AI-generated description from Gemini

    Returns:
        GitHubIssue object ready for creation
    """
    # Use imported sanitize_function_name

    error_count = error_collection.get_error_count()
    function_name = error_collection.function_name
    sanitized_function_name = sanitize_function_name(function_name)
    assignees_list = assignees or []

    # HYBRID APPROACH: Single error vs Multiple errors
    if error_count == 1:
        # Single error - use existing deterministic format
        return _create_single_error_issue(
            error_collection,
            sanitized_function_name,
            labels,
            assignees_list,
            gemini_description,
        )

    # Multiple errors - use consolidated format
    return _create_consolidated_error_issue(
        error_collection,
        labels,
        assignees_list,
        gemini_description,
    )


def _create_single_error_issue(
    error_collection: "ErrorCollection",
    sanitized_function_name: str,
    labels: list[str],
    assignees: list[str],
    gemini_description: str | None = None,
) -> GitHubIssue:
    """Create a single error issue using existing deterministic format.

    Args:
        error_collection: Collection with exactly one error
        sanitized_function_name: Sanitized function name
        labels: List of labels to apply
        assignees: List of assignees
        gemini_description: Optional AI-generated description

    Returns:
        GitHubIssue with deterministic title format
    """
    # Use imported generate_deterministic_title

    # Get the single error
    single_error_entry = error_collection.get_chronological_errors()[0]
    error_record = single_error_entry.error_record

    # Generate deterministic title using existing logic
    title = generate_deterministic_title(
        sanitized_function_name,
        error_record.error_type,
        error_record.error_message,
    )

    # Truncate title if too long
    if len(title) > 256:
        title = title[:253] + "..."

    # Generate body - use existing single error format or enhanced version
    if gemini_description:
        body = generate_single_error_body_with_ai(error_record, gemini_description)
    else:
        body = generate_single_error_body_fallback(error_record)

    return GitHubIssue(
        title=title,
        body=body,
        labels=labels,  # No additional consolidated tag
        assignees=assignees,
    )


def _create_consolidated_error_issue(
    error_collection: "ErrorCollection",
    labels: list[str],
    assignees: list[str],
    gemini_description: str | None = None,
) -> GitHubIssue:
    """Create a consolidated error issue for multiple errors.

    Args:
        error_collection: Collection with multiple errors
        labels: List of labels to apply
        assignees: List of assignees
        gemini_description: Optional AI-generated description

    Returns:
        GitHubIssue with consolidated format
    """
    # Generate consolidated title
    sanitized_function_name = sanitize_function_name(error_collection.function_name)
    error_count = error_collection.get_error_count()
    title = f"[CONSOLIDATED] {sanitized_function_name} - {error_count} Issues Detected"

    # Truncate title if too long
    if len(title) > 256:
        title = title[:253] + "..."

    # Generate comprehensive body with timeline
    body = generate_consolidated_issue_body(error_collection, gemini_description)

    return GitHubIssue(
        title=title,
        body=body,
        labels=labels + ["consolidated-error"],  # Add consolidated tag
        assignees=assignees,
    )


def generate_single_error_body_with_ai(
    error_record: "ErrorRecord", gemini_description: str
) -> str:
    """Generate single error issue body with AI description.

    Args:
        error_record: The single error record
        gemini_description: AI-generated description

    Returns:
        Formatted issue body with AI analysis
    """
    body_parts = [
        "## Error Details",
        f"**Function:** `{error_record.function_name}`",
        f"**Error Type:** {error_record.error_type}",
        f"**Error Message:** {error_record.error_message}",
        f"**Timestamp:** {
            (
                error_record.timestamp.isoformat()
                if error_record.timestamp
                else 'Unknown'
            )
        }",
        "",
        "## AI Analysis",
        gemini_description,
        "",
    ]

    if error_record.function_args or error_record.function_kwargs:
        body_parts.extend(["## Function Context", ""])
        if error_record.function_args:
            body_parts.append(f"**Arguments:** `{error_record.function_args}`")
        if error_record.function_kwargs:
            body_parts.append(
                f"**Keyword Arguments:** `{error_record.function_kwargs}`"
            )
        body_parts.append("")

    if error_record.traceback:
        body_parts.extend(["## Stack Trace", f"```\n{error_record.traceback}\n```", ""])

    body_parts.extend(
        [
            "---",
            "*This issue was automatically created by "
            "[exc2issue](https://github.com/exc2issue/exc2issue)*",
        ]
    )

    return "\n".join(body_parts)


def _generate_header(error_collection: "ErrorCollection") -> list[str]:
    """Generate header section for consolidated issue."""
    return [
        f"# Consolidated Error Report: {error_collection.function_name}",
        "",
        f"**Function:** `{error_collection.function_name}`",
        f"**Execution Time:** {error_collection.start_time.isoformat()}",
        f"**Total Issues Detected:** {error_collection.get_error_count()}",
        "",
    ]


def _add_function_context(
    body_parts: list[str], error_collection: "ErrorCollection"
) -> None:
    """Add function context section if arguments are available."""
    if not (error_collection.function_args or error_collection.function_kwargs):
        return

    body_parts.extend(["## Function Context", ""])

    if error_collection.function_args:
        args_str = ", ".join(repr(arg) for arg in error_collection.function_args)
        body_parts.append(f"**Arguments:** `({args_str})`")

    if error_collection.function_kwargs:
        kwargs_str = ", ".join(
            f"{k}={repr(v)}" for k, v in error_collection.function_kwargs.items()
        )
        body_parts.append(f"**Keyword Arguments:** `{{{kwargs_str}}}`")

    body_parts.append("")


def _add_error_timeline(
    body_parts: list[str], error_collection: "ErrorCollection"
) -> None:
    """Add chronological error timeline section."""
    body_parts.extend(["## Issue Timeline", ""])

    chronological_errors = error_collection.get_chronological_errors()
    for i, error_entry in enumerate(chronological_errors, 1):
        timestamp = error_entry.timestamp.strftime("%H:%M:%S.%f")[
            :-3
        ]  # Format to milliseconds
        body_parts.extend(
            [f"### {i}. {error_entry.error_record.error_type} ({timestamp})", ""]
        )

        if error_entry.error_type == "exception":
            _add_exception_details(body_parts, error_entry)
        elif error_entry.error_type == "log":
            _add_log_details(body_parts, error_entry)

        body_parts.append("")


def _add_exception_details(body_parts: list[str], error_entry: "ErrorEntry") -> None:
    """Add exception error details to body."""
    body_parts.extend(
        [
            f"- **Type:** {error_entry.error_record.error_type}",
            f"- **Message:** {error_entry.error_record.error_message}",
        ]
    )

    if error_entry.error_record.traceback:
        body_parts.extend(
            [
                "- **Stack Trace:**",
                "```",
                error_entry.error_record.traceback,
                "```",
            ]
        )


def _add_log_details(body_parts: list[str], error_entry: "ErrorEntry") -> None:
    """Add log error details to body."""
    logger_name = error_entry.source_info.get("logger_name", "unknown")
    log_level = error_entry.source_info.get("log_level", "ERROR")

    body_parts.extend(
        [
            f"- **Type:** Log {log_level}",
            f"- **Message:** {error_entry.error_record.error_message}",
            f"- **Logger:** {logger_name}",
        ]
    )

    # Add module and line info if available
    module = error_entry.source_info.get("module")
    line_number = error_entry.source_info.get("line_number")
    if module and line_number:
        body_parts.append(f"- **Location:** {module}:{line_number}")


def _add_error_summary(
    body_parts: list[str], error_collection: "ErrorCollection"
) -> None:
    """Add error summary by type section."""
    error_types = error_collection.get_errors_by_type()

    if not (error_types["exception"] or error_types["log"]):
        return

    body_parts.extend(["## Summary by Type", ""])

    if error_types["exception"]:
        _add_exception_summary(body_parts, error_types["exception"])

    if error_types["log"]:
        _add_log_summary(body_parts, error_types["log"])


def _add_exception_summary(
    body_parts: list[str], exceptions: list["ErrorEntry"]
) -> None:
    """Add exception summary to body."""
    body_parts.append(f"**Exceptions:** {len(exceptions)}")
    exception_summary: dict[str, int] = {}
    for error in exceptions:
        exc_type = error.error_record.error_type
        exception_summary[exc_type] = exception_summary.get(exc_type, 0) + 1
    for exc_type, count in exception_summary.items():
        body_parts.append(f"  - {exc_type}: {count}")
    body_parts.append("")


def _add_log_summary(body_parts: list[str], logs: list["ErrorEntry"]) -> None:
    """Add log summary to body."""
    body_parts.append(f"**Log Errors:** {len(logs)}")
    log_summary: dict[str, int] = {}
    for error in logs:
        log_level = error.source_info.get("log_level", "ERROR")
        log_summary[log_level] = log_summary.get(log_level, 0) + 1
    for log_level, count in log_summary.items():
        body_parts.append(f"  - {log_level}: {count}")
    body_parts.append("")


def generate_single_error_body_fallback(error_record: "ErrorRecord") -> str:
    """Generate single error issue body without AI (fallback).

    Args:
        error_record: The single error record

    Returns:
        Formatted issue body without AI analysis
    """
    body_parts = [
        f"# Error in function: {error_record.function_name}",
        "",
        f"**Error Type:** {error_record.error_type}",
        f"**Error Message:** {error_record.error_message}",
        f"**Timestamp:** {
            (
                error_record.timestamp.isoformat()
                if error_record.timestamp
                else 'Unknown'
            )
        }",
        "",
    ]

    if error_record.function_args or error_record.function_kwargs:
        body_parts.extend(["## Function Context", ""])
        if error_record.function_args:
            body_parts.append(f"**Arguments:** `{error_record.function_args}`")
        if error_record.function_kwargs:
            body_parts.append(
                f"**Keyword Arguments:** `{error_record.function_kwargs}`"
            )
        body_parts.append("")

    if error_record.traceback and error_record.traceback.strip():
        body_parts.extend(["## Stack Trace", f"```\n{error_record.traceback}\n```", ""])

    body_parts.extend(
        [
            "---",
            "*This issue was automatically generated by exc2issue (fallback mode - install with "
            "`pip install exc2issue[ai]` for AI-powered descriptions)*",
        ]
    )

    return "\n".join(body_parts)


def generate_consolidated_issue_body(
    error_collection: "ErrorCollection", gemini_description: str | None = None
) -> str:
    """Generate comprehensive issue body from error collection.

    Args:
        error_collection: Collection of errors from function execution
        gemini_description: Optional AI-generated description

    Returns:
        Formatted markdown body for the GitHub issue
    """
    body_parts = _generate_header(error_collection)

    # Add function context if available
    _add_function_context(body_parts, error_collection)

    # Add AI-generated description if available
    if gemini_description:
        body_parts.extend(["## AI Analysis", "", gemini_description, ""])

    # Add chronological error timeline
    _add_error_timeline(body_parts, error_collection)

    # Add summary by error type
    _add_error_summary(body_parts, error_collection)

    # Add footer
    body_parts.extend(
        [
            "---",
            "*This consolidated issue was automatically generated by "
            "[exc2issue](https://github.com/exc2issue/exc2issue)*",
        ]
    )

    return "\n".join(body_parts)
