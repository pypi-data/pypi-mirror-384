"""Prompt building functionality for the Gemini client.

This module contains functions for building prompts to send to the Gemini API
based on error records and templates.
"""

from exc2issue.core.models import ErrorRecord

from ._format_functions import format_function_args, sanitize_for_prompt


def build_prompt(error_record: ErrorRecord, prompt_template: str | None = None) -> str:
    """Build prompt for Gemini API based on error record.

    Args:
        error_record: ErrorRecord containing error details
        prompt_template: Optional custom template for prompt generation

    Returns:
        Formatted prompt string
    """
    if prompt_template:
        # Use custom template
        return prompt_template.format(
            function_name=error_record.function_name,
            error_message=error_record.error_message,
            error_type=error_record.error_type,
            function_args=format_function_args(error_record.function_args),
            traceback=error_record.traceback or "No traceback available",
        )

    # Build standard prompt
    prompt_parts = [
        "You are an expert software engineer helping to create a "
        "comprehensive GitHub issue description.",
        "Based on the following error information, generate a clear, "
        "detailed GitHub issue description that will help developers "
        "understand and fix the problem.",
        "",
        "## Error Information:",
    ]

    # Add error details
    if error_record.error_type == "Log":
        prompt_parts.extend(
            [
                "**Type**: Log Error (from logger.error call)",
                f"**Function**: {error_record.function_name}",
                f"**Message**: {sanitize_for_prompt(error_record.error_message)}",
                f"**Function Arguments**: {format_function_args(error_record.function_args)}",
                "",
                "Note: This is a logged error, so no traceback is available.",
            ]
        )
    else:
        prompt_parts.extend(
            [
                f"**Type**: Exception ({error_record.error_type})",
                f"**Function**: {error_record.function_name}",
                f"**Error Message**: {sanitize_for_prompt(error_record.error_message)}",
                f"**Function Arguments**: {format_function_args(error_record.function_args)}",
            ]
        )

        if error_record.traceback:
            prompt_parts.extend(
                [
                    "",
                    "**Stack Trace**:",
                    f"```\n{sanitize_for_prompt(error_record.traceback)}\n```",
                ]
            )

    prompt_parts.extend(
        [
            "",
            "## Instructions:",
            "Generate a well-structured GitHub issue description with analysis including:",
            "1. A clear summary of what went wrong",
            "2. Steps to reproduce (if applicable)",
            "3. Expected vs actual behavior",
            "4. Technical details from the error",
            "5. Potential impact or severity",
            "",
            "Format the response in Markdown with appropriate headers and code blocks.",
            "Be technical but accessible to other developers.",
        ]
    )

    return "\n".join(prompt_parts)
