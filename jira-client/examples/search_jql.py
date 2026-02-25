"""Example: run a custom JQL query."""

from jira_client import JiraClient

client = JiraClient.from_env()

# Find all high-priority bugs assigned to you, updated in the last 7 days
project_key = client._config.default_project
if not project_key:
    raise ValueError("Set JIRA_PROJECT in your .env file")

jql = f'project = "{project_key}" AND updated >= -7d ORDER BY updated DESC'

result = client.issues.search(jql, max_results=20)
print(f"Matching issues: {result.total}\n")
for issue in result.issues:
    print(f"  [{issue.key}] {issue.summary} | {issue.status.name}")
