from abc import ABC

import requests

from jira_client.config import JiraConfig
from jira_client.exceptions import (
    JiraAuthError,
    JiraClientError,
    JiraNotFoundError,
    JiraRateLimitError,
    JiraValidationError,
)


class BaseAPI(ABC):
    """Abstract base class for all Jira API resource groups."""

    def __init__(self, config: JiraConfig, session: requests.Session) -> None:
        self._config = config
        self._session = session

    def _url(self, path: str) -> str:
        return f"{self._config.base_url}/{path.lstrip('/')}"

    def _handle_response(self, response: requests.Response) -> dict:
        if response.status_code == 204:
            return {}
        if response.ok:
            return response.json() if response.content else {}
        self._raise_for_status(response)
        return {}  # unreachable, but satisfies type checkers

    def _raise_for_status(self, response: requests.Response) -> None:
        status = response.status_code
        try:
            body = response.json()
            errors = body.get("errorMessages", []) or list(body.get("errors", {}).values())
            message = "; ".join(errors) if errors else response.text
        except Exception:
            message = response.text

        if status in (401, 403):
            raise JiraAuthError(f"Authentication failed ({status}): {message}", status)
        if status == 404:
            raise JiraNotFoundError(f"Not found: {message}", status)
        if status == 400:
            raise JiraValidationError(f"Bad request: {message}", status)
        if status == 429:
            raise JiraRateLimitError(f"Rate limit exceeded: {message}", status)
        raise JiraClientError(f"Jira API error ({status}): {message}", status)
