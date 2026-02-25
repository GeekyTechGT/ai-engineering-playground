import requests
from requests.auth import HTTPBasicAuth

from jira_client.api.comments import CommentsAPI
from jira_client.api.issues import IssuesAPI
from jira_client.api.projects import ProjectsAPI
from jira_client.config import AUTH_BEARER, JiraConfig


class JiraClient:
    """Main entry point for the Jira Cloud API client.

    Usage::

        from jira_client import JiraClient

        client = JiraClient.from_env()            # loads .env automatically
        projects = client.projects.get_all()
        issue = client.issues.get("PROJ-1")
    """

    def __init__(self, config: JiraConfig) -> None:
        self._config = config
        self._session = self._build_session()
        self.projects = ProjectsAPI(config, self._session)
        self.issues = IssuesAPI(config, self._session)
        self.comments = CommentsAPI(config, self._session)

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self._config.auth_type == AUTH_BEARER:
            session.headers["Authorization"] = f"Bearer {self._config.api_token}"
        else:
            session.auth = HTTPBasicAuth(self._config.email, self._config.api_token)
        session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        return session

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "JiraClient":
        """Create a JiraClient by loading credentials from a .env file."""
        config = JiraConfig.from_env(env_file)
        return cls(config)
