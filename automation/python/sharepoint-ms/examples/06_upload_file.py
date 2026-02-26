"""
Example 06 – Upload a local file to a document library folder.

Uploads a file from the local filesystem into the specified folder
inside a SharePoint document library.  The folder is specified as a
path relative to the library root.

The example uploads the project README.md by default; set LOCAL_FILE in
.env or change the variable below to upload any file you like.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH,
    DRIVE_NAME

Optional .env variables:
    SUBFOLDER_PATH  – target folder inside the library (default: library root)

Usage:
    cd examples
    python 06_upload_file.py
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
)

# File to upload – defaults to the project README; change as needed.
LOCAL_FILE = Path(__file__).resolve().parent.parent / "README.md"

# Target folder inside the library (empty string = library root).
FOLDER_PATH = env.get("SUBFOLDER_PATH", "")

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

destination = f"{drive['name']}/{FOLDER_PATH}" if FOLDER_PATH else drive["name"]
print(f"Uploading  : {LOCAL_FILE}")
print(f"Destination: {destination}/")

uploaded = client.upload_file(
    site_id=site_id,
    drive_id=drive_id,
    folder_path=FOLDER_PATH,
    local_file=LOCAL_FILE,
)

print(f"\nUpload successful!")
print(f"  Name  : {uploaded.get('name')}")
print(f"  ID    : {uploaded.get('id')}")
print(f"  Size  : {uploaded.get('size')} bytes")
print(f"  URL   : {uploaded.get('webUrl')}")
