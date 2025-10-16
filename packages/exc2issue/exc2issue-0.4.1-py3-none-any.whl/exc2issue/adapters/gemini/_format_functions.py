"""Private formatting functions for the Gemini client.

This module contains helper functions for formatting data for use in Gemini prompts
and fallback descriptions. These functions are internal to the Gemini adapter.
"""

import re
from typing import Any


def format_function_args(args: list[Any] | None) -> str:
    """Format function arguments for display.

    Args:
        args: List of function arguments or None

    Returns:
        Formatted arguments string
    """
    if not args:
        return "No arguments"

    # Convert list to string representation
    args_str = str(args)

    # Truncate very long argument strings
    if len(args_str) > 1000:
        return args_str[:985] + "...[truncated]"

    return args_str


def sanitize_for_prompt(text: str) -> str:
    """Sanitize text for use in prompts.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove actual null bytes and control characters (not escaped literals)
    text = text.replace("\x00", "")
    # Remove actual control characters, not escaped string representations
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    # Also remove escaped representation of null bytes from string literals
    text = text.replace("\\x00", "")

    # Remove potentially dangerous HTML/script tags
    text = re.sub(
        r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags

    return text
