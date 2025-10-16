"""Main GitHub client for exc2issue.

This module provides the main GitHubClient class for interacting with the GitHub
API to create issues automatically when errors are detected.
"""

import time
from typing import TYPE_CHECKING, Any

import requests
from pydantic import HttpUrl, SecretStr
from requests.exceptions import HTTPError

from exc2issue.config import GitHubConfig
from exc2issue.core.models import ErrorRecord, GitHubIssue
from exc2issue.types import IssueCreationOptions

from ._api_utils import get_headers
from ._issue_formatting import convert_error_collection_to_issue, convert_error_to_issue
from ._sanitization import sanitize_issue_data
from ._search import has_existing_open_issue, search_existing_issues
from ._validation import validate_repository_format

if TYPE_CHECKING:
    from exc2issue.core.error_collection import ErrorCollection


class GitHubClient:
    """Client for interacting with the GitHub API.

    This client handles authentication, issue creation, and all the necessary
    error handling and retry logic for robust GitHub API interactions.
    Uses Pydantic configuration for settings management.

    Attributes:
        config: GitHub configuration settings
        token: GitHub personal access token for authentication
        base_url: Base URL for GitHub API (supports GitHub Enterprise)
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://api.github.com",
        *,
        config: GitHubConfig | None = None,
    ):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token. If None, will try to read from
                  GITHUB_TOKEN environment variable.
            base_url: Base URL for GitHub API. Defaults to public GitHub.
            config: GitHub configuration settings (keyword-only, advanced usage).

        Raises:
            ValueError: If no token is provided and GITHUB_TOKEN env var is not set.
        """
        # Priority order: config > parameters > env vars
        if config is not None:
            self.config = config
        elif token is not None:
            # Create config from parameters
            self.config = GitHubConfig(
                token=SecretStr(token), base_url=HttpUrl(base_url)
            )
        else:
            # Use GitHubConfig to load from environment variables (including .env file)
            try:
                # Loads token from env vars
                self.config = GitHubConfig(base_url=HttpUrl(base_url))  # type: ignore[call-arg]
            except Exception as e:
                raise ValueError(
                    "GitHub token is required. Provide it directly or set "
                    f"GITHUB_TOKEN environment variable. Error: {e}"
                ) from e

        # Extract values for internal use
        self.token = self.config.token.get_secret_value()
        self.base_url = self.config.base_url

    @classmethod
    def from_config(cls, config: GitHubConfig) -> "GitHubClient":
        """Create GitHubClient from GitHubConfig.

        Args:
            config: GitHub configuration settings

        Returns:
            GitHubClient: Configured client instance
        """
        return cls(config=config)

    def create_issue(
        self, repository: str, issue: GitHubIssue, max_retries: int = 3
    ) -> dict[str, Any]:
        """Create a GitHub issue with retry mechanism.

        Args:
            repository: Repository in format "owner/repo"
            issue: GitHubIssue object with issue details
            max_retries: Maximum number of retry attempts for transient failures

        Returns:
            Dictionary containing GitHub API response with issue details

        Raises:
            ValueError: If repository format is invalid
            HTTPError: If all retry attempts fail or client error (4xx) occurs
            RequestException: If network request fails after all retries
        """
        validate_repository_format(repository)

        # Sanitize and prepare issue data
        issue_data = sanitize_issue_data(issue)

        base = str(self.base_url).rstrip("/")
        url = f"{base}/repos/{repository}/issues"
        headers = get_headers(self.token)

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, headers=headers, json=issue_data, timeout=30
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except HTTPError as e:
                # Don't retry for client errors (4xx)
                if e.response and 400 <= e.response.status_code < 500:
                    raise

                if attempt == max_retries - 1:
                    raise

                # Exponential backoff for server errors (5xx) and other transient issues
                wait_time = 2**attempt
                time.sleep(wait_time)
            except (requests.RequestException, ValueError, OSError, ConnectionError):
                # For non-HTTP exceptions (network issues, timeouts, etc.)
                if attempt == max_retries - 1:
                    raise

                # Exponential backoff
                wait_time = 2**attempt
                time.sleep(wait_time)

        # This should never be reached, but just in case
        raise HTTPError("All retry attempts failed")

    def convert_error_to_issue(
        self,
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
        return convert_error_to_issue(error_record, labels, assignees)

    def search_existing_issues(
        self, repository: str, title: str, max_results: int = 10
    ) -> list[dict[str, Any]]:
        """Search for existing open issues with the specified title.

        Uses GitHub's search API to find issues by title. Only searches for open issues
        in the specified repository to prevent creation of duplicate issues.

        Args:
            repository: Repository in format "owner/repo"
            title: Issue title to search for (exact match)
            max_results: Maximum number of results to return (default: 10)

        Returns:
            List of issue dictionaries from GitHub API, empty if no matches found

        Raises:
            HTTPError: If GitHub API returns an error
            RequestException: If network request fails

        Note:
            This method is designed to be robust - search failures should not prevent
            issue creation, so calling code should handle exceptions gracefully.
        """
        return search_existing_issues(
            str(self.base_url), self.token, repository, title, max_results
        )

    def has_existing_open_issue(self, repository: str, title: str) -> bool:
        """Check if an open issue with the specified title already exists.

        This is a convenience method that wraps search_existing_issues to provide
        a simple boolean response for duplicate detection.

        Args:
            repository: Repository in format "owner/repo"
            title: Issue title to search for

        Returns:
            True if at least one open issue with the exact title exists, False otherwise

        Note:
            Returns False on any search error to ensure issue creation can proceed
            as a fallback behavior.
        """
        return has_existing_open_issue(
            str(self.base_url), self.token, repository, title
        )

    def create_consolidated_issue(
        self,
        repository: str,
        error_collection: "ErrorCollection",
        options: IssueCreationOptions,
    ) -> dict[str, Any]:
        """Create a consolidated GitHub issue from an error collection.

        Args:
            repository: Repository in format "owner/repo"
            error_collection: Collection of errors from a single function execution
            options: Issue creation options (labels, assignees, Gemini description)

        Returns:
            Dictionary containing GitHub API response with issue details

        Raises:
            ValueError: If repository format is invalid or no errors in collection
            HTTPError: If GitHub API returns an error
            RequestException: If network request fails
        """

        if not error_collection.has_errors():
            raise ValueError("Cannot create issue from empty error collection")

        # Generate consolidated issue
        consolidated_issue = convert_error_collection_to_issue(
            error_collection=error_collection,
            labels=options.labels,
            assignees=options.assignees,
            gemini_description=options.gemini_description,
        )

        # Create the issue using existing logic
        return self.create_issue(repository, consolidated_issue)
