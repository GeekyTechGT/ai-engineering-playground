"""
Example 04 – List root items in the Documents library.

Finds the document library whose name matches DRIVE_NAME (default: "Documents")
and lists all files and folders at its root level.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH, DRIVE_NAME

Usage:
    cd examples
    python 04_list_documents_root.py
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
    "DRIVE_NAME",
)

config = SharePointConfig(
    tenant_id=env["TENANT_ID"],
    client_id=env["CLIENT_ID"],
    client_secret=env["CLIENT_SECRET"],
)
client = SharePointClient(config)

site = client.get_site(env["SHAREPOINT_HOSTNAME"], env["SHAREPOINT_SITE_PATH"])
site_id = site["id"]

drive = client.get_drive_by_name(site_id, env["DRIVE_NAME"])
drive_id = drive["id"]
print(f"Library: {drive['name']}  ({drive['webUrl']})\n")

items = client.list_root_items(site_id, drive_id)

if not items:
    print("(empty library)")
else:
    print(f"{'TYPE':<8}  {'NAME':<40}  {'ID'}")
    print("-" * 80)
    for item in items:
        kind = "folder" if "folder" in item else "file"
        name = item.get("name", "")
        item_id = item.get("id", "")
        size = item.get("size", "")
        extra = f"  [{size} bytes]" if kind == "file" and size else ""
        print(f"{kind:<8}  {name:<40}  {item_id}{extra}")
