"""
Example 08 – Check user permissions on a SharePoint site.

Inspects the effective SharePoint role assignments for a specific user,
covering direct assignments, SharePoint group memberships, and AAD
security-group memberships.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH,
    TARGET_USER_EMAIL

Required Azure app permissions (application, with admin consent):
    Microsoft Graph:
        Sites.Read.All, User.Read.All, GroupMember.Read.All
    SharePoint:
        Sites.FullControl.All  (or AllSites.FullControl)

Usage:
    cd examples
    python 08_check_permissions.py
"""
import json

from _env import load_local_env, require_env
from sharepoint_ms import SharePointClient, SharePointConfig

load_local_env()
env = require_env(
    "TENANT_ID",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "SHAREPOINT_HOSTNAME",
    "SHAREPOINT_SITE_PATH",
    "TARGET_USER_EMAIL",
)

config = SharePointConfig(
    tenant_id=env["TENANT_ID"],
    client_id=env["CLIENT_ID"],
    client_secret=env["CLIENT_SECRET"],
)
client = SharePointClient(config)

result = client.get_user_site_permissions(
    user_email=env["TARGET_USER_EMAIL"],
    hostname=env["SHAREPOINT_HOSTNAME"],
    site_path=env["SHAREPOINT_SITE_PATH"],
)

# Pretty-print the full report
print(json.dumps(result, indent=2, ensure_ascii=False))

# Summary line
has_access = result.get("has_access", False)
roles = result.get("effective_roles", [])
user_name = result.get("user", {}).get("display_name", env["TARGET_USER_EMAIL"])
if has_access:
    print(f"\n{user_name} has access with roles: {', '.join(roles)}")
else:
    print(f"\n{user_name} has NO access to this site.")
