from typing import Any

import requests

from jira_client.api.base import BaseAPI
from jira_client.config import JiraConfig
from jira_client.models.project import Project


class ProjectsAPI(BaseAPI):
    """API operations for Jira projects."""

    def __init__(self, config: JiraConfig, session: requests.Session) -> None:
        super().__init__(config, session)

    def get_all(self) -> list[Project]:
        """Return all accessible Jira projects."""
        response = self._session.get(
            self._url("project"),
            params={"expand": "description,lead,category"},
        )
        data = self._handle_response(response)
        return [Project.from_dict(p) for p in data]

    def get(self, project_key: str) -> Project:
        """Return a single project by its key."""
        response = self._session.get(
            self._url(f"project/{project_key}"),
            params={"expand": "description,lead,category"},
        )
        data = self._handle_response(response)
        return Project.from_dict(data)

    def get_issue_types(self, project_key: str) -> list[dict[str, Any]]:
        """Return the issue types available in a project."""
        response = self._session.get(self._url(f"issuetype/project"), params={"projectId": self._get_project_id(project_key)})
        data = self._handle_response(response)
        if isinstance(data, list):
            return data
        # fallback: expand from project endpoint
        response = self._session.get(
            self._url(f"project/{project_key}"),
            params={"expand": "issueTypes"},
        )
        data = self._handle_response(response)
        return data.get("issueTypes", [])

    def _get_project_id(self, project_key: str) -> str:
        """Resolve a project key to its numeric ID."""
        response = self._session.get(self._url(f"project/{project_key}"))
        data = self._handle_response(response)
        return data["id"]

    def get_components(self, project_key: str) -> list[dict[str, Any]]:
        """Return all components defined in a project."""
        response = self._session.get(self._url(f"project/{project_key}/components"))
        return self._handle_response(response)  # type: ignore[return-value]

    def get_versions(self, project_key: str) -> list[dict[str, Any]]:
        """Return all versions defined in a project."""
        response = self._session.get(self._url(f"project/{project_key}/versions"))
        return self._handle_response(response)  # type: ignore[return-value]
