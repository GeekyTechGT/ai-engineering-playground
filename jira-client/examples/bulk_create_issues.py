"""Example: bulk-create multiple issues in one API call (useful for LLM pipelines).

Reads the project key from JIRA_PROJECT in .env.

Usage:
    python examples/bulk_create_issues.py
"""

from jira_client import JiraClient
from jira_client.models import IssueCreate

client = JiraClient.from_env()
project_key = client._config.default_project

if not project_key:
    raise ValueError("Set JIRA_PROJECT in your .env file")

issues_to_create = [
    IssueCreate(
        project_key=project_key,
        summary="Implement user authentication",
        issue_type="Story",
        priority="High",
        labels=["auth", "backend"],
    ),
    IssueCreate(
        project_key=project_key,
        summary="Design login UI mockup",
        issue_type="Task",
        priority="Medium",
        labels=["design", "frontend"],
    ),
    IssueCreate(
        project_key=project_key,
        summary="Write unit tests for auth module",
        issue_type="Task",
        priority="Medium",
        labels=["testing", "backend"],
    ),
]

created = client.issues.bulk_create(issues_to_create)
print(f"Created {len(created)} issue(s):")
for issue in created:
    print(f"  [{issue.key}] {issue.summary}")
