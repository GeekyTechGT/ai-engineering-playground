"""
Example 03 – List document libraries (drives).

Every SharePoint document library is a Graph API "drive".
This example lists all libraries in the site so you can find the
ID and name of the one you want to work with (e.g. "Documents").

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH

Usage:
    cd examples
    python 03_list_drives.py
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

site = client.get_site(env["SHAREPOINT_HOSTNAME"], env["SHAREPOINT_SITE_PATH"])
site_id = site["id"]

drives = client.list_drives(site_id)

print(f"Found {len(drives)} document librar{'y' if len(drives) == 1 else 'ies'}:\n")
for drive in drives:
    print(f"  Name  : {drive.get('name')}")
    print(f"  ID    : {drive['id']}")
    print(f"  Type  : {drive.get('driveType')}")
    print(f"  URL   : {drive.get('webUrl')}")
    print()
