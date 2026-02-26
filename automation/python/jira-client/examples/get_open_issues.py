"""Example: retrieve all open issues for a project.

Uses JIRA_PROJECT from .env when no project key is passed.

Usage:
    python examples/get_open_issues.py          # uses JIRA_PROJECT from .env
    python examples/get_open_issues.py KAN      # explicit project key
"""

import sys

from jira_client import JiraClient

client = JiraClient.from_env()
project_key = sys.argv[1] if len(sys.argv) > 1 else None

result = client.issues.get_open(project_key=project_key, max_results=25)
print(f"Open issues: {result.total} (showing {len(result.issues)})\n")

for issue in result.issues:
    assignee = issue.assignee or "Unassigned"
    priority = issue.priority.name if issue.priority else "-"
    print(f"  [{issue.key}] {issue.summary}")
    print(f"           Status: {issue.status.name} | Priority: {priority} | Assignee: {assignee}")
