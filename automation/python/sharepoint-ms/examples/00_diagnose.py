"""
Example 00 – Diagnose app permissions.

Runs a series of Graph API calls and reports which ones succeed or fail,
so you can see exactly which Azure app permissions are missing before
running the other examples.

Required .env variables:
    TENANT_ID, CLIENT_ID, CLIENT_SECRET,
    SHAREPOINT_HOSTNAME, SHAREPOINT_SITE_PATH

Usage:
    cd examples
    python 00_diagnose.py
"""
import sys

import requests

from _env import load_local_env, require_env
from sharepoint_ms import SharePointConfig
from sharepoint_ms._auth import ClientCredentialsTokenProvider
from sharepoint_ms._http import GRAPH_BASE, GRAPH_SCOPE

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"

def ok(msg: str)   -> None: print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg: str) -> None: print(f"  {RED}✗{RESET} {msg}")
def info(msg: str) -> None: print(f"  {YELLOW}•{RESET} {msg}")


def check(label: str, url: str, token: str, timeout: int = 15) -> bool:
    """Perform a GET and report pass/fail. Returns True on success."""
    try:
        r = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=timeout,
        )
        if r.status_code < 400:
            ok(f"{label}  →  HTTP {r.status_code}")
            return True
        else:
            fail(f"{label}  →  HTTP {r.status_code}")
            try:
                err = r.json().get("error", {})
                info(f"  code: {err.get('code')}  –  {err.get('message', r.text[:120])}")
            except Exception:
                info(f"  {r.text[:200]}")
            return False
    except Exception as exc:
        fail(f"{label}  →  exception: {exc}")
        return False


load_local_env()
env = require_env(
    "TENANT_ID", "CLIENT_ID", "CLIENT_SECRET",
    "SHAREPOINT_HOSTNAME", "SHAREPOINT_SITE_PATH",
)

config = SharePointConfig(
    tenant_id=env["TENANT_ID"],
    client_id=env["CLIENT_ID"],
    client_secret=env["CLIENT_SECRET"],
)

print(f"\n{BOLD}=== sharepoint-ms diagnostics ==={RESET}\n")

# ── Step 1: Authentication ─────────────────────────────────────────────────
print(f"{BOLD}[1] Authentication (client_credentials){RESET}")
tokens = ClientCredentialsTokenProvider(config)
try:
    graph_token = tokens.get_token(GRAPH_SCOPE)
    ok(f"Graph token acquired  (len={len(graph_token)})")
except Exception as exc:
    fail(f"Cannot obtain Graph token: {exc}")
    info("Fix: check TENANT_ID, CLIENT_ID, CLIENT_SECRET in your .env")
    sys.exit(1)

hostname = env["SHAREPOINT_HOSTNAME"]
sp_scope = f"https://{hostname}/.default"
try:
    sp_token = tokens.get_token(sp_scope)
    ok(f"SharePoint token acquired  (scope={sp_scope})")
except Exception as exc:
    fail(f"Cannot obtain SharePoint token: {exc}")
    info(f"Fix: the app may not be permitted to request scope '{sp_scope}'")
    sp_token = None

# ── Step 2: Graph API permissions ─────────────────────────────────────────
print(f"\n{BOLD}[2] Microsoft Graph API permissions{RESET}")

site_path  = env["SHAREPOINT_SITE_PATH"].strip("/")
site_url   = f"{GRAPH_BASE}/sites/{hostname}:/{site_path}"
drives_url = None   # filled in after site resolves

site_ok = check("Sites.Read.All  →  GET /sites/{hostname}:/{path}", site_url, graph_token)
if site_ok:
    try:
        import json
        r = requests.get(site_url, headers={"Authorization": f"Bearer {graph_token}"}, timeout=15)
        site_id = r.json().get("id", "")
        drives_url = f"{GRAPH_BASE}/sites/{site_id}/drives"
        info(f"site_id = {site_id}")
    except Exception:
        pass

if drives_url:
    drives_ok = check(
        "Files.ReadWrite.All  →  GET /sites/{id}/drives",
        drives_url, graph_token,
    )
else:
    fail("Files.ReadWrite.All  →  skipped (site not resolved)")
    drives_ok = False

user_url = f"{GRAPH_BASE}/users/{env.get('TARGET_USER_EMAIL', 'me')}?$select=id"
if env.get("TARGET_USER_EMAIL"):
    check("User.Read.All  →  GET /users/{email}", user_url, graph_token)
else:
    info("User.Read.All  →  skipped (TARGET_USER_EMAIL not set in .env)")

# ── Step 3: SharePoint REST API ────────────────────────────────────────────
print(f"\n{BOLD}[3] SharePoint REST API permissions{RESET}")
if sp_token:
    sp_url = (
        f"https://{hostname}/{env['SHAREPOINT_SITE_PATH'].strip('/')}/"
        "_api/web/title"
    )
    check(
        "Sites.FullControl.All  →  GET /_api/web/title",
        sp_url, sp_token,
    )
else:
    fail("SharePoint REST  →  skipped (no SharePoint token)")

# ── Summary ────────────────────────────────────────────────────────────────
print(f"\n{BOLD}[4] Summary{RESET}")
if not site_ok:
    print(f"""
  {RED}ACTION REQUIRED:{RESET} Add these permissions in the Azure Portal:

  portal.azure.com → Microsoft Entra ID → App registrations
    → [your app] → API permissions → Add a permission

  Microsoft Graph  (Application permissions, admin consent required):
    ✦ Sites.Read.All
    ✦ Files.ReadWrite.All
    ✦ User.Read.All
    ✦ GroupMember.Read.All

  SharePoint  (Application permissions, admin consent required):
    ✦ Sites.FullControl.All

  Then click: "Grant admin consent for [your tenant]"
""")
else:
    print(f"  {GREEN}All checked permissions appear to be working.{RESET}")

print()
