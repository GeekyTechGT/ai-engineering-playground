from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from jira_client.utils import adf_to_text, text_to_adf


@dataclass
class IssueType:
    """Represents a Jira issue type (Bug, Story, Task, …)."""

    id: str
    name: str
    description: str = ""
    subtask: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueType":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            subtask=data.get("subtask", False),
        )


@dataclass
class Priority:
    """Represents an issue priority (Highest, High, Medium, Low, Lowest)."""

    id: str
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Priority":
        return cls(id=data["id"], name=data["name"])


@dataclass
class Status:
    """Represents the workflow status of an issue."""

    id: str
    name: str
    category: str  # "new" | "indeterminate" | "done"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Status":
        return cls(
            id=data["id"],
            name=data["name"],
            category=data.get("statusCategory", {}).get("key", ""),
        )


@dataclass
class Issue:
    """Represents a Jira issue."""

    id: str
    key: str
    summary: str
    issue_type: IssueType
    status: Status
    project_key: str
    description: str | None = None
    priority: Priority | None = None
    assignee: str | None = None
    reporter: str | None = None
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    created: datetime | None = None
    updated: datetime | None = None
    resolved: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        fields = data["fields"]

        def _parse_dt(val: str | None) -> datetime | None:
            return datetime.fromisoformat(val.replace("Z", "+00:00")) if val else None

        assignee = fields.get("assignee") or {}
        reporter = fields.get("reporter") or {}
        priority = Priority.from_dict(fields["priority"]) if fields.get("priority") else None
        components = [c["name"] for c in fields.get("components", [])]

        return cls(
            id=data["id"],
            key=data["key"],
            summary=fields["summary"],
            issue_type=IssueType.from_dict(fields["issuetype"]),
            status=Status.from_dict(fields["status"]),
            project_key=fields["project"]["key"],
            description=adf_to_text(fields.get("description")),
            priority=priority,
            assignee=assignee.get("displayName"),
            reporter=reporter.get("displayName"),
            labels=fields.get("labels", []),
            components=components,
            created=_parse_dt(fields.get("created")),
            updated=_parse_dt(fields.get("updated")),
            resolved=_parse_dt(fields.get("resolutiondate")),
        )


@dataclass
class IssueCreate:
    """Data transfer object for creating a new Jira issue."""

    project_key: str
    summary: str
    issue_type: str = "Task"
    description: str | None = None
    priority: str | None = None
    assignee_account_id: str | None = None
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    due_date: str | None = None  # "YYYY-MM-DD"

    def to_payload(self) -> dict[str, Any]:
        """Serialize to the Jira REST API v3 payload format."""
        issue_fields: dict[str, Any] = {
            "project": {"key": self.project_key},
            "summary": self.summary,
            "issuetype": {"name": self.issue_type},
        }
        if self.description is not None:
            issue_fields["description"] = text_to_adf(self.description)
        if self.priority is not None:
            issue_fields["priority"] = {"name": self.priority}
        if self.assignee_account_id is not None:
            issue_fields["assignee"] = {"accountId": self.assignee_account_id}
        if self.labels:
            issue_fields["labels"] = self.labels
        if self.components:
            issue_fields["components"] = [{"name": c} for c in self.components]
        if self.due_date is not None:
            issue_fields["duedate"] = self.due_date
        return {"fields": issue_fields}


@dataclass
class IssueUpdate:
    """Data transfer object for updating an existing Jira issue.

    Only non-None fields are included in the update payload.
    """

    summary: str | None = None
    description: str | None = None
    priority: str | None = None
    assignee_account_id: str | None = None
    labels: list[str] | None = None
    components: list[str] | None = None
    due_date: str | None = None

    def to_payload(self) -> dict[str, Any]:
        """Serialize to the Jira REST API v3 payload format."""
        issue_fields: dict[str, Any] = {}
        if self.summary is not None:
            issue_fields["summary"] = self.summary
        if self.description is not None:
            issue_fields["description"] = text_to_adf(self.description)
        if self.priority is not None:
            issue_fields["priority"] = {"name": self.priority}
        if self.assignee_account_id is not None:
            issue_fields["assignee"] = {"accountId": self.assignee_account_id}
        if self.labels is not None:
            issue_fields["labels"] = self.labels
        if self.components is not None:
            issue_fields["components"] = [{"name": c} for c in self.components]
        if self.due_date is not None:
            issue_fields["duedate"] = self.due_date
        return {"fields": issue_fields}


@dataclass
class IssueSearchResult:
    """Paginated result from a JQL search."""

    total: int
    start_at: int
    max_results: int
    issues: list[Issue]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueSearchResult":
        issues = [Issue.from_dict(i) for i in data.get("issues", [])]
        return cls(
            total=data.get("total", len(issues)),
            start_at=data.get("startAt", 0),
            max_results=data.get("maxResults", len(issues)),
            issues=issues,
        )
