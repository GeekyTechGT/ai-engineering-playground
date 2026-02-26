import json
import os

from sharepoint_ms import SharePointClient, SharePointConfig


config = SharePointConfig(
    tenant_id=os.environ["TENANT_ID"],
    client_id=os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
)

client = SharePointClient(config)

result = client.get_user_site_permissions(
    user_email=os.environ["TARGET_USER_EMAIL"],
    hostname=os.environ["SHAREPOINT_HOSTNAME"],
    site_path=os.environ["SHAREPOINT_SITE_PATH"],
)

print(json.dumps(result, indent=2, ensure_ascii=False))
