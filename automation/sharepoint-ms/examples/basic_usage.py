import os
from pathlib import Path

from sharepoint_ms import SharePointClient, SharePointConfig


config = SharePointConfig(
    tenant_id=os.environ["TENANT_ID"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
)

client = SharePointClient(config)

site = client.get_site(
    hostname=os.environ["SHAREPOINT_HOSTNAME"],
    site_path=os.environ["SHAREPOINT_SITE_PATH"],
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
