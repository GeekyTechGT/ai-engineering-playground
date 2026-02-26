"""Diagnostic script: verify credentials and Jira connectivity.

Run this first to confirm that your .env is correct before using other examples.

    python examples/check_auth.py

Supports both auth modes:
    JIRA_AUTH_TYPE=basic   (classic API token — email + token via HTTP Basic Auth)
    JIRA_AUTH_TYPE=bearer  (OAuth 2.0 / scoped token — sent as Bearer header)
"""

import sys

from jira_client import JiraClient
from jira_client.config import AUTH_BASIC, AUTH_BEARER, JiraConfig


def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _info(msg: str) -> None:
    print(f"         {msg}")


# ── 1. Load and display config ────────────────────────────────────────────────
print("\n=== Step 1: Load configuration from .env ===")
try:
    config = JiraConfig.from_env()
    _ok("Configuration loaded successfully")
    _info(f"Domain:          {config.domain}")
    _info(f"Auth type:       {config.auth_type}")
    if config.auth_type == AUTH_BASIC:
        _info(f"Email:           {config.email}")
    _info(f"API token:       {'*' * 8}{config.api_token[-4:]}")
    _info(f"Default project: {config.default_project or '(not set)'}")
except ValueError as exc:
    _fail(str(exc))
    _info("Hint: copy .env.example to .env and fill in the required variables.")
    sys.exit(1)

client = JiraClient(config)

# ── 2. Check authenticated user ───────────────────────────────────────────────
print("\n=== Step 2: Verify token (GET /myself) ===")
try:
    response = client._session.get(f"{config.base_url}/myself")
    if response.status_code == 200:
        me = response.json()
        _ok(f"Authenticated as: {me.get('displayName')} <{me.get('emailAddress')}>")
        _info(f"Account ID: {me.get('accountId')}")
        _info(f"Active:     {me.get('active')}")
    elif response.status_code == 401:
        _fail("Authentication failed (401) — token is invalid or expired.")
        if config.auth_type == AUTH_BASIC:
            _info("Tip: make sure JIRA_AUTH_TYPE=basic, JIRA_EMAIL is correct,")
            _info("     and JIRA_API_TOKEN is a *classic* API token (not OAuth).")
            _info("     Generate one at: https://id.atlassian.com/manage-profile/security/api-tokens")
        else:
            _info("Tip: make sure JIRA_AUTH_TYPE=bearer and JIRA_API_TOKEN is a valid OAuth 2.0 token.")
        _info(f"     Raw response: {response.text[:300]}")
        sys.exit(1)
    elif response.status_code == 403:
        _fail("Forbidden (403) — token is valid but lacks permission to read user profile.")
        _info(f"     Raw response: {response.text[:300]}")
        sys.exit(1)
    else:
        _fail(f"Unexpected status {response.status_code}: {response.text[:300]}")
        sys.exit(1)
except Exception as exc:
    _fail(f"Network error — check JIRA_DOMAIN ({config.domain}): {exc}")
    sys.exit(1)

# ── 3. List accessible projects ───────────────────────────────────────────────
print("\n=== Step 3: List accessible projects (GET /project/search) ===")
try:
    response = client._session.get(
        f"{config.base_url}/project/search",
        params={"maxResults": 50, "orderBy": "key"},
    )
    if response.status_code == 200:
        data = response.json()
        projects = data.get("values", [])
        total = data.get("total", len(projects))
        if projects:
            _ok(f"Found {total} accessible project(s):")
            for p in projects:
                _info(f"  [{p['key']}]  {p['name']}  ({p.get('projectTypeKey', '')})")
        else:
            _fail("No projects returned — the token is valid but has no Browse Projects permission.")
    else:
        _fail(f"Status {response.status_code}: {response.text[:300]}")
except Exception as exc:
    _fail(f"Error: {exc}")

# ── 4. Check default project (if set) ─────────────────────────────────────────
if config.default_project:
    print(f"\n=== Step 4: Check default project '{config.default_project}' ===")
    try:
        response = client._session.get(f"{config.base_url}/project/{config.default_project}")
        if response.status_code == 200:
            p = response.json()
            _ok(f"Project accessible: [{p['key']}] {p['name']}")
            _info(f"Type: {p.get('projectTypeKey')}")
            if lead := p.get("lead"):
                _info(f"Lead: {lead.get('displayName')}")
        elif response.status_code == 404:
            _fail(f"Project '{config.default_project}' not found or not accessible.")
            _info("Hint: JIRA_PROJECT must be the project KEY (e.g. 'KAN'), not the project name.")
            _info("      Keys are shown in brackets in Step 3 above.")
        elif response.status_code == 403:
            _fail(f"Access denied to project '{config.default_project}'.")
        else:
            _fail(f"Status {response.status_code}: {response.text[:300]}")
    except Exception as exc:
        _fail(f"Error: {exc}")
else:
    print("\n=== Step 4: Skipped (JIRA_PROJECT not set in .env) ===")

print("\n=== Done ===\n")
