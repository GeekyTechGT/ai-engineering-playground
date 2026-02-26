from datetime import date
from typing import Any

import requests

from jira_client.api.base import BaseAPI
from jira_client.config import JiraConfig
from jira_client.models.issue import Issue, IssueCreate, IssueSearchResult, IssueUpdate

_ISSUE_FIELDS = (
    "summary,description,issuetype,status,priority,"
    "assignee,reporter,labels,components,project,created,updated,resolutiondate"
)


class IssuesAPI(BaseAPI):
    """API operations for Jira issues."""

    def __init__(self, config: JiraConfig, session: requests.Session) -> None:
        super().__init__(config, session)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, issue: IssueCreate) -> Issue:
        """Create a new issue and return the created issue."""
        response = self._session.post(self._url("issue"), json=issue.to_payload())
        data = self._handle_response(response)
        return self.get(data["key"])

    def get(self, issue_key: str) -> Issue:
        """Return a single issue by key (e.g. "PROJ-42")."""
        response = self._session.get(
            self._url(f"issue/{issue_key}"),
            params={"fields": _ISSUE_FIELDS},
        )
        data = self._handle_response(response)
        return Issue.from_dict(data)

    def update(self, issue_key: str, update: IssueUpdate) -> None:
        """Update fields of an existing issue."""
        response = self._session.put(
            self._url(f"issue/{issue_key}"),
            json=update.to_payload(),
        )
        self._handle_response(response)

    def delete(self, issue_key: str, delete_subtasks: bool = False) -> None:
        """Delete an issue. Set delete_subtasks=True to also remove child issues."""
        response = self._session.delete(
            self._url(f"issue/{issue_key}"),
            params={"deleteSubtasks": str(delete_subtasks).lower()},
        )
        self._handle_response(response)

    # ------------------------------------------------------------------
    # Search / filtering
    # ------------------------------------------------------------------

    def search(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: list[str] | None = None,
    ) -> IssueSearchResult:
        """Search issues using a JQL query string."""
        response = self._session.get(
            self._url("search/jql"),
            params={
                "jql": jql,
                "maxResults": max_results,
                "startAt": start_at,
                "fields": ",".join(fields or _ISSUE_FIELDS.split(",")),
            },
        )
        data = self._handle_response(response)
        return IssueSearchResult.from_dict(data)

    def get_open(
        self,
        project_key: str | None = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> IssueSearchResult:
        """Return open (not-done) issues, optionally filtered by project."""
        project = project_key or self._config.default_project
        conditions = ["statusCategory != Done"]
        if project:
            conditions.insert(0, f'project = "{project}"')
        jql = " AND ".join(conditions) + " ORDER BY created DESC"
        return self.search(jql, max_results=max_results, start_at=start_at)

    def get_closed(
        self,
        project_key: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> IssueSearchResult:
        """Return closed issues, optionally filtered by project and resolution date range."""
        project = project_key or self._config.default_project
        conditions = ["statusCategory = Done"]
        if project:
            conditions.insert(0, f'project = "{project}"')
        if date_from:
            conditions.append(f'resolutiondate >= "{date_from.isoformat()}"')
        if date_to:
            conditions.append(f'resolutiondate <= "{date_to.isoformat()}"')
        jql = " AND ".join(conditions) + " ORDER BY resolutiondate DESC"
        return self.search(jql, max_results=max_results, start_at=start_at)

    # ------------------------------------------------------------------
    # Transitions (status changes)
    # ------------------------------------------------------------------

    def get_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        """Return the available workflow transitions for an issue."""
        response = self._session.get(self._url(f"issue/{issue_key}/transitions"))
        data = self._handle_response(response)
        return data.get("transitions", [])

    def transition(self, issue_key: str, transition_id: str) -> None:
        """Apply a workflow transition to change the issue status."""
        response = self._session.post(
            self._url(f"issue/{issue_key}/transitions"),
            json={"transition": {"id": transition_id}},
        )
        self._handle_response(response)

    # ------------------------------------------------------------------
    # Assignee
    # ------------------------------------------------------------------

    def assign(self, issue_key: str, account_id: str | None) -> None:
        """Assign an issue to a user. Pass None to unassign."""
        response = self._session.put(
            self._url(f"issue/{issue_key}/assignee"),
            json={"accountId": account_id},
        )
        self._handle_response(response)

    # ------------------------------------------------------------------
    # Watchers
    # ------------------------------------------------------------------

    def get_watchers(self, issue_key: str) -> list[dict[str, Any]]:
        """Return the list of watchers for an issue."""
        response = self._session.get(self._url(f"issue/{issue_key}/watchers"))
        data = self._handle_response(response)
        return data.get("watchers", [])

    def add_watcher(self, issue_key: str, account_id: str) -> None:
        """Add a user as a watcher."""
        response = self._session.post(
            self._url(f"issue/{issue_key}/watchers"),
            json=account_id,
        )
        self._handle_response(response)

    # ------------------------------------------------------------------
    # Links
    # ------------------------------------------------------------------

    def link(
        self,
        link_type: str,
        inward_issue_key: str,
        outward_issue_key: str,
        comment: str | None = None,
    ) -> None:
        """Create an issue link between two issues.

        Common link_type values: "Blocks", "Cloners", "Duplicate", "Relates".
        """
        from jira_client.utils import text_to_adf

        payload: dict[str, Any] = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue_key},
            "outwardIssue": {"key": outward_issue_key},
        }
        if comment:
            payload["comment"] = {"body": text_to_adf(comment)}
        response = self._session.post(self._url("issueLink"), json=payload)
        self._handle_response(response)

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def bulk_create(self, issues: list[IssueCreate]) -> list[Issue]:
        """Create multiple issues in a single API call."""
        payload = {"issueUpdates": [i.to_payload() for i in issues]}
        response = self._session.post(self._url("issue/bulk"), json=payload)
        data = self._handle_response(response)
        return [self.get(item["key"]) for item in data.get("issues", [])]
