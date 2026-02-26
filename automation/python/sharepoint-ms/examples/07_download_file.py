"""
Example 07 – Download a file from a document library.

Downloads a file identified by its Graph item ID to a local path.

To find an item ID:
    Run example 04 or 05 and copy the ID from the output,
    then set ITEM_ID in your .env file.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH,
    DRIVE_NAME, ITEM_ID

Usage:
    cd examples
    python 07_download_file.py
"""
from pathlib import Path

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
    "ITEM_ID",
)

# Local directory where the file will be saved.
DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloads"

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

item_id = env["ITEM_ID"]

# Fetch item metadata to know the filename before downloading.
item_meta = client.get_item_by_id(site_id, drive_id, item_id)
filename = item_meta.get("name", f"item_{item_id}")
destination = DOWNLOAD_DIR / filename

print(f"Downloading : {filename}  ({item_meta.get('size', '?')} bytes)")
print(f"Saving to   : {destination}")

saved_path = client.download_file(
    site_id=site_id,
    drive_id=drive_id,
    item_id=item_id,
    destination=destination,
)

print(f"\nDownload successful!  File saved to: {saved_path}")
