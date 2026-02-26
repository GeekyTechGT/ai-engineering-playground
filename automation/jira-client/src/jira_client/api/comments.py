import requests

from jira_client.api.base import BaseAPI
from jira_client.config import JiraConfig
from jira_client.models.comment import Comment, CommentCreate, CommentUpdate


class CommentsAPI(BaseAPI):
    """API operations for Jira issue comments."""

    def __init__(self, config: JiraConfig, session: requests.Session) -> None:
        super().__init__(config, session)

    def get_all(self, issue_key: str) -> list[Comment]:
        """Return all comments for an issue, ordered oldest first."""
        response = self._session.get(
            self._url(f"issue/{issue_key}/comment"),
            params={"orderBy": "created"},
        )
        data = self._handle_response(response)
        return [Comment.from_dict(c) for c in data.get("comments", [])]

    def get(self, issue_key: str, comment_id: str) -> Comment:
        """Return a single comment by ID."""
        response = self._session.get(self._url(f"issue/{issue_key}/comment/{comment_id}"))
        data = self._handle_response(response)
        return Comment.from_dict(data)

    def add(self, issue_key: str, comment: CommentCreate) -> Comment:
        """Add a new comment to an issue."""
        response = self._session.post(
            self._url(f"issue/{issue_key}/comment"),
            json=comment.to_payload(),
        )
        data = self._handle_response(response)
        return Comment.from_dict(data)

    def update(self, issue_key: str, comment_id: str, update: CommentUpdate) -> Comment:
        """Update the body of an existing comment."""
        response = self._session.put(
            self._url(f"issue/{issue_key}/comment/{comment_id}"),
            json=update.to_payload(),
        )
        data = self._handle_response(response)
        return Comment.from_dict(data)

    def delete(self, issue_key: str, comment_id: str) -> None:
        """Delete a comment permanently."""
        response = self._session.delete(
            self._url(f"issue/{issue_key}/comment/{comment_id}")
        )
        self._handle_response(response)
