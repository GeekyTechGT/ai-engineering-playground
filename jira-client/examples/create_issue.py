"""Example: create a new Jira issue.

Reads the project key from JIRA_PROJECT in .env.
Automatically picks the first available issue type from the project.

Usage:
    python examples/create_issue.py
"""

from jira_client import JiraClient
from jira_client.models import IssueCreate

client = JiraClient.from_env()
project_key = client._config.default_project

if not project_key:
    raise ValueError("Set JIRA_PROJECT in your .env file")

# Fetch available issue types for this project
issue_types = client.projects.get_issue_types(project_key)
print(f"Available issue types in '{project_key}':")
for t in issue_types:
    print(f"  - {t['name']}")

# Use the first non-subtask type available
issue_type = next(
    (t["name"] for t in issue_types if not t.get("subtask", False)),
    issue_types[0]["name"] if issue_types else "Task",
)
print(f"\nUsing issue type: '{issue_type}'")

new_issue = IssueCreate(
    project_key=project_key,
    summary="Fix login button not responding on mobile",
    issue_type=issue_type,
    description=(
        "When using Safari on iOS 16 the login button does not respond to tap events.\n\n"
        "Steps to reproduce:\n"
        "1. Open the app on iPhone with Safari\n"
        "2. Tap the Login button\n"
        "3. Nothing happens"
    ),
    labels=["mobile", "safari"],
)

issue = client.issues.create(new_issue)
print(f"\nCreated: [{issue.key}] {issue.summary}")
print(f"Status:  {issue.status.name}")
print(f"Type:    {issue.issue_type.name}")
