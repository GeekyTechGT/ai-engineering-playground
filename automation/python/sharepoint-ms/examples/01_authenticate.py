"""
Example 01 – Verify credentials.

Authenticates against Microsoft Graph API using the client credentials flow
and confirms the connection is working.  Run this first to validate your
.env configuration before running any other example.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET

Usage:
    cd examples
    python 01_authenticate.py
"""
from _env import load_local_env, require_env
from sharepoint_ms import SharePointClient, SharePointConfig, AuthenticationError

load_local_env()
env = require_env("TENANT_ID", "CLIENT_ID", "CLIENT_SECRET")

config = SharePointConfig(
    tenant_id=env["TENANT_ID"],
    client_id=env["CLIENT_ID"],
    client_secret=env["CLIENT_SECRET"],
)

client = SharePointClient(config)

try:
    client.authenticate()
    print("Authentication successful!")
    print(f"Tenant ID : {env['TENANT_ID']}")
    print(f"Client ID : {env['CLIENT_ID']}")
except AuthenticationError as exc:
    print(f"Authentication FAILED: {exc}")
    raise SystemExit(1)
