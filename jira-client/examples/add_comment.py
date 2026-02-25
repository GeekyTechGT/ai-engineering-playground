"""Example: add, list, update and delete comments on an issue.

Usage:
    python examples/add_comment.py KAN-1
"""

import sys

from jira_client import JiraClient
from jira_client.models import CommentCreate, CommentUpdate

if len(sys.argv) < 2:
    print("Usage: python examples/add_comment.py <ISSUE-KEY>  (e.g. KAN-1)")
    sys.exit(1)

client = JiraClient.from_env()
issue_key = sys.argv[1]

# Add a comment
added = client.comments.add(
    issue_key,
    CommentCreate("Reproduced on iPhone 14 Pro with iOS 17.2. Assigning to mobile team."),
)
print(f"Comment added (id={added.id}) by {added.author}")

# List all comments
comments = client.comments.get_all(issue_key)
print(f"\nAll comments ({len(comments)}):")
for c in comments:
    print(f"  [{c.id}] {c.author}: {c.body}")

# Update the comment just added
updated = client.comments.update(
    issue_key,
    added.id,
    CommentUpdate("Reproduced on iPhone 14 Pro iOS 17.2. Fixed in branch fix/login-tap."),
)
print(f"\nComment updated at {updated.updated}")

# Delete it
client.comments.delete(issue_key, added.id)
print("Comment deleted.")
