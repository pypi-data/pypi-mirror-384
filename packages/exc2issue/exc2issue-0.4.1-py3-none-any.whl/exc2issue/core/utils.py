"""Utility functions for exc2issue.

This module contains helper functions used throughout the exc2issue library,
including deterministic title generation for GitHub issues.
"""

import re


def generate_deterministic_title(
    function_name: str, error_type: str, error_message: str | None = None
) -> str:
    """Generate a deterministic GitHub issue title.

    Creates a consistent title format that prevents duplicate issues for the same
    error type and function combination. For exceptions, uses the exception type.
    For logs, extracts a static pattern from the log message.

    Args:
        function_name: Name of the function where the error occurred
        error_type: Type of error (e.g., "ValueError", "Log")
        error_message: Original error message (used for pattern extraction for logs)

    Returns:
        Formatted title string in format:
        - [EXCEPTION]-[FUNCTION_NAME]-[EXCEPTION_TYPE] for exceptions
        - [LOG-ERROR]-[FUNCTION_NAME]-[MESSAGE_PATTERN] for log errors

    Examples:
        >>> generate_deterministic_title("divide", "ZeroDivisionError", "division by zero")
        '[EXCEPTION]-[divide]-[ZeroDivisionError]'

        >>> generate_deterministic_title("connect_db", "Log", "Connection failed after 30 seconds")
        '[LOG-ERROR]-[connect_db]-[Connection_failed_after_{timeout}_seconds]'
    """
    # Sanitize function name
    clean_function_name = sanitize_function_name(function_name)

    if error_type == "Log":
        # For log errors, extract pattern from message
        pattern = _extract_log_pattern(error_message or "unknown_log_message")
        return f"[LOG-ERROR]-[{clean_function_name}]-[{pattern}]"

    # For exceptions, use the exception type directly
    clean_error_type = _sanitize_error_type(error_type)
    return f"[EXCEPTION]-[{clean_function_name}]-[{clean_error_type}]"


def _extract_log_pattern(log_message: str) -> str:
    """Extract a static pattern from a log message.

    Replaces variable values with placeholders to create a consistent pattern
    for deduplication while preserving the message structure.

    Args:
        log_message: Original log message

    Returns:
        Static pattern with variables replaced by placeholders

    Examples:
        >>> _extract_log_pattern("Connection failed after 30 seconds")
        'Connection_failed_after_{timeout}_seconds'

        >>> _extract_log_pattern("User john.doe@example.com not found")
        'User_{email}_not_found'
    """
    if not log_message or log_message.strip() == "":
        return "unknown_log_message"

    # Start with the original message
    pattern = log_message.strip()

    # Common patterns to replace with placeholders
    # Order matters: more specific patterns first
    replacements = [
        # Time-related patterns (must come before individual numbers)
        (r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM))?\b", "{time}"),
        (r"\b\d{4}-\d{2}-\d{2}\b", "{date}"),
        # Email addresses
        (r"\b[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}\b", "{email}"),
        # URLs and paths
        (r"https?://[^\s]+", "{url}"),
        (r"/[^\s]*(?:/[^\s]*)*", "{path}"),
        # UUIDs and similar long identifiers
        (
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
            "{uuid}",
        ),
        (r"\b[0-9a-fA-F]{16,}\b", "{id}"),
        # IP addresses
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "{ip}"),
        # Numbers (including decimals, percentages, etc.) - after time patterns
        (r"\b\d+\.\d+%?\b", "{number}"),
        (r"\b\d+%?\b", "{number}"),
        # Quoted strings
        (r'"[^"]*"', "{quoted_text}"),
        (r"'[^']*'", "{quoted_text}"),
        # Common variable-like patterns at word boundaries
        (r"\b[a-zA-Z]\w*\d+\w*\b", "{variable}"),  # e.g., user123, temp_file_1
    ]

    # Apply replacements
    for regex_pattern, replacement in replacements:
        pattern = re.sub(regex_pattern, replacement, pattern, flags=re.IGNORECASE)

    # Clean up the pattern for GitHub title compatibility
    # Replace spaces and special chars with underscores
    pattern = re.sub(r"[\s\-\.]+", "_", pattern)
    # Remove multiple underscores
    pattern = re.sub(r"_{2,}", "_", pattern)
    # Remove leading/trailing underscores
    pattern = pattern.strip("_")

    # Ensure it's not too long for GitHub titles
    if len(pattern) > 50:  # Leave room for [LOG-ERROR]-[function_name]-
        pattern = pattern[:47] + "..."

    return pattern or "unknown_pattern"


def _sanitize_error_type(error_type: str) -> str:
    """Sanitize error type for use in GitHub issue titles.

    Args:
        error_type: Raw error type name

    Returns:
        Sanitized error type suitable for GitHub issue titles
    """
    if not error_type or error_type.strip() == "":
        return "UnknownError"

    # Remove common prefixes and clean up
    clean_type = error_type.strip()

    # Remove module paths (e.g., "builtins.ValueError" -> "ValueError")
    if "." in clean_type:
        clean_type = clean_type.split(".")[-1]

    # Remove angle brackets and other problematic characters
    clean_type = re.sub(r'[<>"\']', "", clean_type)

    # Ensure it starts with a letter and contains only valid characters
    clean_type = re.sub(r"[^a-zA-Z0-9_]", "", clean_type)

    # If it becomes empty, use a default
    if not clean_type:
        return "UnknownError"

    # Truncate if too long
    if len(clean_type) > 30:
        clean_type = clean_type[:30]

    return clean_type


def sanitize_function_name(function_name: str | None) -> str:
    """Sanitize function name for use in issue titles.

    Args:
        function_name: Raw function name (can be None)

    Returns:
        Sanitized function name suitable for GitHub issue titles
    """
    if not function_name or function_name.strip() == "":
        return "unknown"

    # Remove or replace problematic characters
    sanitized = re.sub(r"[<>]", "", function_name)  # Remove angle brackets
    sanitized = sanitized.strip()

    # Handle special cases
    if sanitized == "<module>":
        return "module"

    return sanitized or "unknown"


def validate_title_format(title: str) -> bool:
    """Validate that a title follows the expected deterministic format.

    Args:
        title: Title string to validate

    Returns:
        True if title matches expected format, False otherwise

    Examples:
        >>> validate_title_format("[EXCEPTION]-[my_func]-[ValueError]")
        True

        >>> validate_title_format(
        ...     "[LOG-ERROR]-[connect_db]-[Connection_failed_after_{number}_seconds]"
        ... )
        True

        >>> validate_title_format("Exception in my_func: some error")
        False
    """
    # Pattern for new format: [CATEGORY]-[function_name]-[type_or_pattern]
    pattern = r"^\[(LOG-ERROR|EXCEPTION)\]-\[.+\]-\[.+\]$"
    return bool(re.match(pattern, title))
