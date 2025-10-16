"""GitHub issue creation logic for exc2issue.

This module handles the creation of GitHub issues from error collections,
supporting both consolidated issues (multiple errors) and individual issues
(single errors). It includes:

- Consolidated issue creation with AI-powered descriptions
- Individual issue creation with deterministic titles
- Duplicate detection and prevention
- Error handling and fallback mechanisms
- Integration with Gemini AI for enhanced descriptions
"""

import logging
from typing import TYPE_CHECKING, Protocol

import requests

from exc2issue.adapters.gemini._fallback import create_fallback_description
from exc2issue.core.error_collection import ErrorCollection
from exc2issue.core.models import ErrorRecord, GitHubIssue
from exc2issue.core.task_queue import queue_issue_creation_task
from exc2issue.core.task_types import IssueCreationTask
from exc2issue.core.utils import generate_deterministic_title, sanitize_function_name
from exc2issue.types import IssueCreationOptions

if TYPE_CHECKING:
    from exc2issue.adapters.gemini import GeminiClient
    from exc2issue.adapters.github import GitHubClient
    from exc2issue.adapters.vertexai import VertexAIClient


class DecoratorProtocol(Protocol):
    """Protocol defining the interface for decorator instances.

    This protocol allows both BugHunterDecorator and Self types to be used.
    """

    @property
    def repository(self) -> str:
        """Get GitHub repository identifier."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def labels(self) -> list[str]:
        """Get labels to apply to created issues."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def assignees(self) -> list[str]:
        """Get assignees for created issues."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def consolidation_threshold(self) -> int:
        """Get threshold for consolidating errors."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def enable_background_processing(self) -> bool:
        """Determine whether background processing is enabled."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def gemini_client(self) -> "GeminiClient | VertexAIClient | None":
        """Get the AI client instance (Gemini or VertexAI) for AI-powered descriptions."""
        ...  # pylint: disable=unnecessary-ellipsis

    @property
    def github_client(self) -> "GitHubClient":
        """Get the GitHub client instance for issue creation."""
        ...  # pylint: disable=unnecessary-ellipsis


def _generate_gemini_description(
    decorator_instance: DecoratorProtocol, error_collection: ErrorCollection
) -> str | None:
    """Generate Gemini AI description for consolidated issue.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type) with Gemini client
        error_collection: Collection of errors to generate description for

    Returns:
        str | None: Generated description or None if generation fails
    """
    if decorator_instance.gemini_client is None:
        return None

    logger = logging.getLogger(__name__)

    try:
        chronological_errors = error_collection.get_chronological_errors()
        if chronological_errors:
            primary_error = chronological_errors[-1].error_record
            description = decorator_instance.gemini_client.generate_issue_description(
                primary_error
            )
            return description
    except (requests.RequestException) as e:
        logger.warning("Gemini API failed for consolidated issue: %s", e)
    except (ValueError, RuntimeError, AttributeError, ImportError) as e:
        logger.warning("Gemini API failed for consolidated issue: %s", e)
    except (KeyError, TypeError, OSError) as e:
        logger.warning("Gemini API failed for consolidated issue: %s", e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch any unexpected exceptions to ensure decorator robustness
        logger.warning("Unexpected error in Gemini API for consolidated issue: %s", e)

    return None


def _check_for_duplicate_consolidated_issue(
    decorator_instance: DecoratorProtocol, consolidated_title: str
) -> bool:
    """Check if a duplicate consolidated issue already exists.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type) with GitHub client
        consolidated_title: Title of the consolidated issue to check

    Returns:
        bool: True if duplicate exists, False otherwise
    """
    if not decorator_instance.repository:
        return False

    logger = logging.getLogger(__name__)

    try:
        if decorator_instance.github_client.has_existing_open_issue(
            decorator_instance.repository, consolidated_title
        ):
            logger.info(
                "Skipping duplicate consolidated issue creation for '%s' - "
                "an open issue with this title already exists in %s",
                consolidated_title,
                decorator_instance.repository,
            )
            return True
    except (requests.HTTPError, requests.RequestException) as e:
        logger.warning(
            "Failed to check for duplicate consolidated issues, "
            "proceeding with creation: %s",
            e,
        )

    return False


def _create_github_consolidated_issue(
    decorator_instance: DecoratorProtocol,
    error_collection: ErrorCollection,
    gemini_description: str | None,
) -> None:
    """Create the consolidated GitHub issue.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type) with GitHub client
        error_collection: Collection of errors to create issue for
        gemini_description: AI-generated description or None
    """
    if not decorator_instance.repository:
        return

    logger = logging.getLogger(__name__)

    try:
        options = IssueCreationOptions(
            labels=decorator_instance.labels,
            assignees=decorator_instance.assignees,
            gemini_description=gemini_description,
        )
        decorator_instance.github_client.create_consolidated_issue(
            repository=decorator_instance.repository,
            error_collection=error_collection,
            options=options,
        )

        logger.info(
            "Created consolidated GitHub issue for %s with %s errors",
            error_collection.function_name,
            error_collection.get_error_count(),
        )
    except (requests.RequestException, ValueError, ImportError) as e:
        logger.warning("Failed to create consolidated GitHub issue: %s", e)
    except (RuntimeError, AttributeError, KeyError, TypeError, OSError) as e:
        logger.warning("Failed to create consolidated GitHub issue: %s", e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch any unexpected exceptions to ensure decorator robustness
        logger.warning("Unexpected error creating consolidated GitHub issue: %s", e)


def create_consolidated_issue(
    decorator_instance: DecoratorProtocol, error_collection: ErrorCollection
) -> None:
    """Create consolidated GitHub issue synchronously.

    Creates a single GitHub issue for multiple errors collected from a single
    function execution. Uses AI-powered descriptions when available and includes
    comprehensive error context.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type) with GitHub/Gemini clients
        error_collection: Collection of errors to consolidate into single issue
    """
    if not error_collection.has_errors():
        return

    logger = logging.getLogger(__name__)

    try:
        # Generate AI description if Gemini client is available
        gemini_description = _generate_gemini_description(
            decorator_instance, error_collection
        )

        # Generate consolidated title
        sanitized_function_name = sanitize_function_name(error_collection.function_name)
        error_count = error_collection.get_error_count()
        consolidated_title = (
            f"[CONSOLIDATED] {sanitized_function_name} - {error_count} Issues Detected"
        )

        # Check for duplicates and create issue
        if not _check_for_duplicate_consolidated_issue(
            decorator_instance, consolidated_title
        ):
            _create_github_consolidated_issue(
                decorator_instance, error_collection, gemini_description
            )

    except (requests.RequestException, ValueError, ImportError) as e:
        logger.warning("Failed to create consolidated GitHub issue: %s", e)
    except (RuntimeError, AttributeError, KeyError, TypeError, OSError) as e:
        logger.warning("Failed to create consolidated GitHub issue: %s", e)
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch any unexpected exceptions to ensure decorator robustness
        logger.warning("Unexpected error in consolidated issue creation: %s", e)


def create_individual_issue(
    decorator_instance: DecoratorProtocol, error_record: ErrorRecord
) -> None:
    """Create individual GitHub issue for single errors.

    Creates a GitHub issue for a single error with deterministic titles for
    consistent duplicate detection. Uses AI-powered descriptions when available
    or falls back to structured descriptions.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type) with GitHub/Gemini clients
        error_record: Single error record to create issue for
    """
    logger = logging.getLogger(__name__)

    try:
        # Generate issue description using Gemini (if available) or fallback
        if decorator_instance.gemini_client is not None:
            try:
                description = (
                    decorator_instance.gemini_client.generate_issue_description(
                        error_record
                    )
                )
            except (requests.RequestException, ImportError) as e:
                logger.warning("Gemini API failed, using fallback: %s", e)
                description = _create_fallback_description(error_record)
            except (ValueError, RuntimeError, AttributeError) as e:
                # Fallback for any other exceptions during Gemini API calls
                logger.warning("Gemini API failed, using fallback: %s", e)
                description = _create_fallback_description(error_record)
            except (KeyError, TypeError, OSError) as e:
                # Catch other common exceptions to prevent decorator failure
                logger.warning("Gemini API failed, using fallback: %s", e)
                description = _create_fallback_description(error_record)
        else:
            description = _create_fallback_description(error_record)

        # Generate deterministic title from error information
        sanitized_function_name = sanitize_function_name(error_record.function_name)
        title = generate_deterministic_title(
            sanitized_function_name,
            error_record.error_type,
            error_record.error_message,
        )

        # Check for duplicates
        if decorator_instance.repository:
            try:
                if decorator_instance.github_client.has_existing_open_issue(
                    decorator_instance.repository, title
                ):
                    logger.info(
                        "Skipping duplicate issue creation for '%s' - "
                        "an open issue with this title already exists in %s",
                        title,
                        decorator_instance.repository,
                    )
                    return
            except (requests.HTTPError, requests.RequestException) as e:
                logger.warning(
                    "Failed to check for duplicate issues, "
                    "proceeding with creation: %s",
                    e,
                )

        # Create GitHub issue
        github_issue = GitHubIssue(
            title=title,
            body=description,
            labels=decorator_instance.labels,
            assignees=decorator_instance.assignees,
        )

        if decorator_instance.repository:
            try:
                decorator_instance.github_client.create_issue(
                    decorator_instance.repository, github_issue
                )
                logger.info("Created individual GitHub issue: %s", title)
            except (
                requests.RequestException,
                ValueError,
                ImportError,
                RuntimeError,
                AttributeError,
            ) as e:
                logger.warning("Failed to create individual GitHub issue: %s", e)
            except (KeyError, TypeError, OSError) as e:
                # Catch other common exceptions to prevent decorator failure
                logger.warning("Failed to create individual GitHub issue: %s", e)

    except (
        requests.RequestException,
        ValueError,
        ImportError,
        RuntimeError,
        AttributeError,
    ) as e:
        logger.warning("Failed to create individual GitHub issue: %s", e)


def _create_fallback_description(error_record: ErrorRecord) -> str:
    """Create fallback description when Gemini AI is not available.

    Args:
        error_record: Error record to create description for

    Returns:
        str: Structured fallback description
    """
    # Use the fallback description creator (always available now)
    return create_fallback_description(error_record)


def process_error_collection(
    decorator_instance: DecoratorProtocol, error_collection: ErrorCollection
) -> None:
    """Process error collection using HYBRID logic (single vs consolidated).

    Determines whether to create individual issues or consolidated issues based
    on the number of errors and the consolidation threshold. Uses background
    processing when enabled.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type) with configuration
        error_collection: Collection of errors to process
    """
    if not error_collection.has_errors():
        return

    # HYBRID LOGIC: Determine single vs consolidated approach
    error_count = error_collection.get_error_count()

    if error_count >= decorator_instance.consolidation_threshold:
        # Multiple errors -> Use consolidated approach
        if decorator_instance.enable_background_processing:
            _queue_consolidated_issue(decorator_instance, error_collection)
        else:
            create_consolidated_issue(decorator_instance, error_collection)
    else:
        # Single error -> Use individual deterministic titles
        chronological_errors = error_collection.get_chronological_errors()
        if chronological_errors:
            primary_error = chronological_errors[-1].error_record  # Last error
            create_individual_issue(decorator_instance, primary_error)


def _queue_consolidated_issue(
    decorator_instance: DecoratorProtocol, error_collection: ErrorCollection
) -> None:
    """Queue consolidated GitHub issue creation for background processing.

    Args:
        decorator_instance: BugHunterDecorator instance (or Self type)
        error_collection: Collection of errors to process
    """
    task = IssueCreationTask(error_collection, decorator_instance)
    queue_issue_creation_task(task)
