from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jira_client.utils import adf_to_text, text_to_adf


@dataclass
class Comment:
    """Represents a comment on a Jira issue."""

    id: str
    author: str
    body: str | None
    created: datetime
    updated: datetime

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Comment":
        def _parse_dt(val: str) -> datetime:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            author=(data.get("author") or {}).get("displayName", ""),
            body=adf_to_text(data.get("body")),
            created=_parse_dt(data["created"]),
            updated=_parse_dt(data["updated"]),
        )


@dataclass
class CommentCreate:
    """Data transfer object for adding a comment."""

    body: str

    def to_payload(self) -> dict[str, Any]:
        return {"body": text_to_adf(self.body)}


@dataclass
class CommentUpdate:
    """Data transfer object for updating a comment."""

    body: str

    def to_payload(self) -> dict[str, Any]:
        return {"body": text_to_adf(self.body)}
