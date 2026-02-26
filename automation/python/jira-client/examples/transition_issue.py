"""Example: list available transitions and change issue status.

Usage:
    python examples/transition_issue.py KAN-1
"""

import sys

from jira_client import JiraClient

if len(sys.argv) < 2:
    print("Usage: python examples/transition_issue.py <ISSUE-KEY>  (e.g. KAN-1)")
    sys.exit(1)

client = JiraClient.from_env()
issue_key = sys.argv[1]

transitions = client.issues.get_transitions(issue_key)
print(f"Available transitions for {issue_key}:")
for t in transitions:
    print(f"  [{t['id']}] {t['name']}")

# Move to "In Progress" (name match is case-insensitive)
target = next((t for t in transitions if t["name"].lower() == "in progress"), None)
if target:
    client.issues.transition(issue_key, target["id"])
    issue = client.issues.get(issue_key)
    print(f"\n{issue_key} is now: {issue.status.name}")
else:
    print("\n'In Progress' transition not available for this issue.")
