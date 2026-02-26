from dataclasses import dataclass
from typing import Any


@dataclass
class ProjectCategory:
    """Represents a Jira project category."""

    id: str
    name: str
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectCategory":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
        )


@dataclass
class Project:
    """Represents a Jira project."""

    id: str
    key: str
    name: str
    project_type: str
    description: str = ""
    lead: str | None = None
    category: ProjectCategory | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        category = None
        if cat_data := data.get("projectCategory"):
            category = ProjectCategory.from_dict(cat_data)

        lead = None
        if lead_data := data.get("lead"):
            lead = lead_data.get("displayName")

        return cls(
            id=data["id"],
            key=data["key"],
            name=data["name"],
            project_type=data.get("projectTypeKey", ""),
            description=data.get("description", ""),
            lead=lead,
            category=category,
        )
