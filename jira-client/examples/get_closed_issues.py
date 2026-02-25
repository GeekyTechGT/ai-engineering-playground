"""Example: retrieve closed issues within a date range."""

from datetime import date

from jira_client import JiraClient

client = JiraClient.from_env()

result = client.issues.get_closed(
    project_key=None,   # uses JIRA_PROJECT from .env — change to e.g. "KAN" to override
    date_from=date(2024, 1, 1),
    date_to=date(2024, 12, 31),
    max_results=50,
)

print(f"Closed issues in 2024: {result.total} (showing {len(result.issues)})\n")
for issue in result.issues:
    resolved = issue.resolved.date() if issue.resolved else "N/A"
    print(f"  [{issue.key}] {issue.summary} | Resolved: {resolved}")
