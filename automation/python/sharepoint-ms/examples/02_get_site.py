"""
Example 02 – Resolve a SharePoint site.

Fetches site metadata (ID, display name, URL) from the Graph API.
The site ID returned here is required by all subsequent examples.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH

Usage:
    cd examples
    python 02_get_site.py
"""
from _env import load_local_env, require_env
from sharepoint_ms import SharePointClient, SharePointConfig

load_local_env()
env = require_env(
    "TENANT_ID",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "SHAREPOINT_HOSTNAME",
    "SHAREPOINT_SITE_PATH",
)

config = SharePointConfig(
    tenant_id=env["TENANT_ID"],
    client_id=env["CLIENT_ID"],
    client_secret=env["CLIENT_SECRET"],
)
client = SharePointClient(config)

site = client.get_site(
    hostname=env["SHAREPOINT_HOSTNAME"],
    site_path=env["SHAREPOINT_SITE_PATH"],
)

print("Site resolved successfully!")
print(f"  ID          : {site['id']}")
print(f"  Name        : {site.get('displayName')}")
print(f"  URL         : {site.get('webUrl')}")
print(f"  Description : {site.get('description', '(none)')}")
