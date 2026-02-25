"""Example: list all accessible Jira projects."""

from jira_client import JiraClient

client = JiraClient.from_env()

projects = client.projects.get_all()
print(f"Found {len(projects)} project(s):\n")
for project in projects:
    lead = f" | Lead: {project.lead}" if project.lead else ""
    print(f"  [{project.key}] {project.name} ({project.project_type}){lead}")
