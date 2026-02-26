"""
Example 05 – List contents of a subfolder.

Navigates to a specific folder inside a document library using its
path relative to the library root and lists all files and folders inside it.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH,
    DRIVE_NAME, SUBFOLDER_PATH

SUBFOLDER_PATH examples:
    Reports
    Reports/2024
    Reports/2024/Q1

Usage:
    cd examples
    python 05_list_subfolder.py
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
    "SUBFOLDER_PATH",
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

folder_path = env["SUBFOLDER_PATH"]
items = client.list_folder_items(site_id, drive_id, folder_path)

print(f"Contents of '{drive['name']}/{folder_path}':\n")
if not items:
    print("(empty folder)")
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
