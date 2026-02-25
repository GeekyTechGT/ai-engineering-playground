import os
from dataclasses import dataclass

from dotenv import load_dotenv

AUTH_BASIC = "basic"
AUTH_BEARER = "bearer"


@dataclass
class JiraConfig:
    """Jira Cloud connection configuration.

    auth_type:
        "basic"  — classic API token, uses HTTP Basic Auth (email + token).
                   Generate at https://id.atlassian.com/manage-profile/security/api-tokens
        "bearer" — OAuth 2.0 / scoped token, sent as 'Authorization: Bearer <token>'.
                   email is not required in this mode.
    """

    domain: str
    api_token: str
    email: str = ""
    auth_type: str = AUTH_BASIC
    default_project: str | None = None

    @property
    def base_url(self) -> str:
        return f"https://{self.domain}/rest/api/3"

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "JiraConfig":
        """Load configuration from environment variables or a .env file."""
        load_dotenv(env_file)

        domain = os.getenv("JIRA_DOMAIN")
        api_token = os.getenv("JIRA_API_TOKEN")
        auth_type = os.getenv("JIRA_AUTH_TYPE", AUTH_BASIC).lower()

        missing = [
            name
            for name, val in [("JIRA_DOMAIN", domain), ("JIRA_API_TOKEN", api_token)]
            if not val
        ]

        email = os.getenv("JIRA_EMAIL", "")
        if auth_type == AUTH_BASIC and not email:
            missing.append("JIRA_EMAIL")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            domain=domain,  # type: ignore[arg-type]
            api_token=api_token,  # type: ignore[arg-type]
            email=email,
            auth_type=auth_type,
            default_project=os.getenv("JIRA_PROJECT"),
        )
