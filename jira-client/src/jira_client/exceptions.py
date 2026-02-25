class JiraClientError(Exception):
    """Base exception for all Jira client errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class JiraAuthError(JiraClientError):
    """Raised when authentication or authorization fails (401/403)."""


class JiraNotFoundError(JiraClientError):
    """Raised when the requested resource does not exist (404)."""


class JiraValidationError(JiraClientError):
    """Raised when the request payload is invalid (400)."""


class JiraRateLimitError(JiraClientError):
    """Raised when the API rate limit is exceeded (429)."""
