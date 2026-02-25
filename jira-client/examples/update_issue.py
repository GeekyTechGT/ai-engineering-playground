"""Example: update fields of an existing issue.

Usage:
    python examples/update_issue.py KAN-1
"""

import sys

from jira_client import JiraClient
from jira_client.models import IssueUpdate

if len(sys.argv) < 2:
    print("Usage: python examples/update_issue.py <ISSUE-KEY>  (e.g. KAN-1)")
    sys.exit(1)

issue_key = sys.argv[1]
client = JiraClient.from_env()

update = IssueUpdate(
    summary="Fix login button not responding on mobile [CRITICAL]",
    priority="Highest",
    labels=["mobile", "safari", "urgent"],
    description="Regression introduced in v2.4.0. Affects all iOS devices running Safari.",
)

client.issues.update(issue_key, update)

issue = client.issues.get(issue_key)
print(f"Updated [{issue.key}]: {issue.summary}")
print(f"Priority: {issue.priority.name if issue.priority else 'None'}")
