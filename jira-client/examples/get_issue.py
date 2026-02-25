"""Example: fetch and display a single issue.

Usage:
    python examples/get_issue.py KAN-1
"""

import sys

from jira_client import JiraClient

if len(sys.argv) < 2:
    print("Usage: python examples/get_issue.py <ISSUE-KEY>  (e.g. KAN-1)")
    sys.exit(1)

client = JiraClient.from_env()

issue = client.issues.get(sys.argv[1])

print(f"Key:        {issue.key}")
print(f"Summary:    {issue.summary}")
print(f"Type:       {issue.issue_type.name}")
print(f"Status:     {issue.status.name}")
print(f"Priority:   {issue.priority.name if issue.priority else 'None'}")
print(f"Assignee:   {issue.assignee or 'Unassigned'}")
print(f"Reporter:   {issue.reporter or 'Unknown'}")
print(f"Labels:     {', '.join(issue.labels) or 'None'}")
print(f"Created:    {issue.created}")
print(f"Updated:    {issue.updated}")

if issue.description:
    print(f"\nDescription:\n{issue.description}")
