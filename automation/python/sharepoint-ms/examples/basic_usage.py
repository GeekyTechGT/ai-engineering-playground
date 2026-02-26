from pathlib import Path

from sharepoint_ms import SharePointClient, SharePointConfig
from _env import load_local_env, require_env

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
site_id = site["id"]

print(f"Site ID: {site_id}")

items = client.list_drive_root_items(site_id)
print("Contenuti root:")
for item in items:
    print(f"- {item.get('name')} ({'folder' if 'folder' in item else 'file'})")

# Upload file di esempio
uploaded = client.upload_file(site_id=site_id, folder_path="Shared Documents", local_file=Path("README.md"))
print(f"Upload completato: {uploaded.get('name')}")
