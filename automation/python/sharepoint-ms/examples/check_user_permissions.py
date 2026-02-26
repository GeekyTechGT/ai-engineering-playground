import json

from sharepoint_ms import SharePointClient, SharePointConfig
from _env import load_local_env, require_env

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

print(json.dumps(result, indent=2, ensure_ascii=False))
