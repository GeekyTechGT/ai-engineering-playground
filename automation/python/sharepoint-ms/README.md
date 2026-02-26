# sharepoint-ms

A Python library for automating **Microsoft SharePoint Online** via the
**Microsoft Graph API** (app-only authentication).

Designed for backend automation scenarios: CI/CD pipelines, scheduled jobs,
ETL processes, and system integrations.

---

## Features

| Capability | Description |
|---|---|
| App-only auth | OAuth2 `client_credentials` flow – no user login required |
| Site resolution | Resolve any SharePoint site by hostname + server-relative path |
| Document libraries | List, discover, and navigate document libraries (drives) |
| Folder browsing | List root items or navigate sub-folders by path or ID |
| File upload | Upload local files to any folder in any library |
| File download | Download files by item ID to a local path |
| Permission inspection | Check a user's effective SharePoint roles (direct, SP groups, AAD groups) |

---

## Prerequisites

### 1. Azure App Registration

You need an **App Registration** in **Microsoft Entra ID** (formerly Azure AD)
with the *client credentials* flow enabled.

1. Go to [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**.
2. Give it a name (e.g. `sharepoint-automation`), leave redirect URI blank.
3. After creation, note the **Application (client) ID** and **Directory (tenant) ID**.
4. Go to **Certificates & secrets** → **New client secret** → note the generated secret value.

### 2. API Permissions

Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Application permissions**.

Add and **grant admin consent** for:

| Permission | Scope | Why needed |
|---|---|---|
| `Sites.Read.All` | Graph | Read site metadata and drives |
| `Files.ReadWrite.All` | Graph | Upload and download files |
| `User.Read.All` | Graph | Look up users by email |
| `GroupMember.Read.All` | Graph | Resolve AAD group memberships |

For the **permission-check example** only, also add:

| Permission | Scope | Why needed |
|---|---|---|
| `Sites.FullControl.All` | SharePoint | Read SharePoint role assignments via REST API |

> **Note:** `Sites.FullControl.All` is a SharePoint-scoped permission found under
> **SharePoint** (not Microsoft Graph) in the permission picker.

---

## Installation

### Option A – Editable install (recommended for development)

```bash
# From the project root
pip install -e automation/python/sharepoint-ms
```

### Option B – Install from source wheel

```bash
cd automation/python/sharepoint-ms
pip install build
python -m build
pip install dist/sharepoint_ms-*.whl
```

### Dependencies

The library only requires `requests >= 2.31.0` (no other dependencies).

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```dotenv
# Azure AD credentials
TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CLIENT_SECRET=your-client-secret-here

# SharePoint target site
SHAREPOINT_HOSTNAME=contoso.sharepoint.com
SHAREPOINT_SITE_PATH=/sites/MySite

# Document library name (usually "Documents")
DRIVE_NAME=Documents

# Subfolder path (used by examples 05 and 06)
SUBFOLDER_PATH=Reports/2024

# Item ID for download example (copy from example 04 / 05 output)
ITEM_ID=01XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# User email for permission-check example
TARGET_USER_EMAIL=alice@contoso.com
```

> The `.env` file is loaded automatically by all example scripts.
> Never commit it to source control – it is already in `.gitignore`.

---

## Quick Start

```python
from sharepoint_ms import SharePointClient, SharePointConfig

config = SharePointConfig(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
)
client = SharePointClient(config)

# 1. Resolve the site
site = client.get_site("contoso.sharepoint.com", "/sites/TeamSite")
site_id = site["id"]

# 2. Find the "Documents" library
drive = client.get_drive_by_name(site_id, "Documents")
drive_id = drive["id"]

# 3. List files and folders at the library root
items = client.list_root_items(site_id, drive_id)
for item in items:
    kind = "folder" if "folder" in item else "file"
    print(f"{kind:6}  {item['name']}")

# 4. List a subfolder
sub_items = client.list_folder_items(site_id, drive_id, "Reports/2024")

# 5. Upload a file
uploaded = client.upload_file(site_id, drive_id, "Uploads", "/tmp/report.pdf")
print(f"Uploaded: {uploaded['webUrl']}")

# 6. Download a file (use the item ID from a listing)
client.download_file(site_id, drive_id, uploaded["id"], "/tmp/downloaded.pdf")
```

---

## Examples

All examples live in the `examples/` folder and are designed to be
**atomic** – each one demonstrates a single operation.

Run them from inside the `examples/` directory:

```bash
cd automation/python/sharepoint-ms/examples
python 01_authenticate.py
```

| Script | What it does |
|---|---|
| `01_authenticate.py` | Verify credentials and confirm the API connection works |
| `02_get_site.py` | Resolve a site and print its ID, name, and URL |
| `03_list_drives.py` | List all document libraries in a site |
| `04_list_documents_root.py` | List files and folders at the root of a document library |
| `05_list_subfolder.py` | List the contents of a specific subfolder (by path) |
| `06_upload_file.py` | Upload a local file into a document library folder |
| `07_download_file.py` | Download a file by its item ID to a local directory |
| `08_check_permissions.py` | Check a user's effective SharePoint permissions on a site |

### Required .env variables per example

| Example | Extra .env keys needed |
|---|---|
| 01 | — |
| 02 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH` |
| 03 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH` |
| 04 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH`, `DRIVE_NAME` |
| 05 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH`, `DRIVE_NAME`, `SUBFOLDER_PATH` |
| 06 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH`, `DRIVE_NAME` (+ optional `SUBFOLDER_PATH`) |
| 07 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH`, `DRIVE_NAME`, `ITEM_ID` |
| 08 | `SHAREPOINT_HOSTNAME`, `SHAREPOINT_SITE_PATH`, `TARGET_USER_EMAIL` |

---

## API Reference

### `SharePointConfig`

```python
@dataclass
class SharePointConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    timeout_seconds: int = 30   # HTTP timeout
```

### `SharePointClient`

#### Authentication

| Method | Description |
|---|---|
| `authenticate()` | Proactively verify credentials (otherwise lazy on first call) |

#### Sites

| Method | Returns | Description |
|---|---|---|
| `get_site(hostname, site_path)` | `dict` | Resolve site metadata |

#### Document Libraries (Drives)

| Method | Returns | Description |
|---|---|---|
| `list_drives(site_id)` | `list[dict]` | List all document libraries |
| `get_drive_by_name(site_id, drive_name)` | `dict` | Find a library by name (case-insensitive) |

#### Folders & Items

| Method | Returns | Description |
|---|---|---|
| `list_root_items(site_id, drive_id)` | `list[dict]` | Items at library root |
| `list_folder_items(site_id, drive_id, folder_path)` | `list[dict]` | Items in folder by path |
| `list_items_by_id(site_id, drive_id, item_id)` | `list[dict]` | Items in folder by ID |
| `get_item_by_id(site_id, drive_id, item_id)` | `dict` | Single item metadata by ID |
| `get_item_by_path(site_id, drive_id, item_path)` | `dict` | Single item metadata by path |

#### File Transfers

| Method | Returns | Description |
|---|---|---|
| `upload_file(site_id, drive_id, folder_path, local_file)` | `dict` | Upload a file |
| `download_file(site_id, drive_id, item_id, destination)` | `Path` | Download a file |

#### Permissions

| Method | Returns | Description |
|---|---|---|
| `get_user_site_permissions(user_email, hostname, site_path)` | `dict` | User's effective roles on a site |

### Exceptions

| Exception | When raised |
|---|---|
| `SharePointError` | Base class for all library exceptions |
| `AuthenticationError` | OAuth2 authentication failed |
| `NotFoundError` | Resource not found (HTTP 404) |
| `ForbiddenError` | Access denied – missing API permissions (HTTP 403) |
| `ApiError` | Any other Graph or SharePoint REST error |

---

## Troubleshooting

### `AuthenticationError: Authentication failed (HTTP 400)`

- Double-check `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` in your `.env`.
- Ensure the app registration exists and the secret has not expired.

### `ForbiddenError: Access denied (HTTP 403)`

- Go to the app registration → **API permissions** and verify all required
  permissions are present **and have admin consent** (green checkmark).
- For `get_user_site_permissions`, ensure `Sites.FullControl.All` (SharePoint)
  is granted.

### `NotFoundError: Resource not found (HTTP 404)`

- Verify `SHAREPOINT_HOSTNAME` and `SHAREPOINT_SITE_PATH` match the actual URL.
- Example URL `https://contoso.sharepoint.com/sites/virtualization/testing/`
  → `SHAREPOINT_HOSTNAME=contoso.sharepoint.com`
  → `SHAREPOINT_SITE_PATH=/sites/virtualization/testing`
- Verify `DRIVE_NAME` matches the exact display name of a document library
  (run example 03 to list available libraries).

### `RuntimeError: Missing environment variables`

- Make sure `.env` exists in the project root (copy from `.env.example`).
- All required keys must have non-empty values.

### Files not showing in the correct library

- In SharePoint, **"Documents"** is the most common default document library
  name, but your site may use a different name or a localized variant.
- Run **example 03** first to list all available document libraries and their
  exact names.

---

## Architecture

The library follows SOLID principles:

```
src/sharepoint_ms/
├── __init__.py            Public API exports
├── config.py              SharePointConfig dataclass (S)
├── exceptions.py          Exception hierarchy (S)
├── _auth.py               TokenProvider protocol + ClientCredentials impl (D, O)
├── _http.py               GraphHttpClient + SharePointRestClient (S)
├── site_service.py        SiteService – site resolution (S)
├── drive_service.py       DriveService – files and folders (S)
├── permission_service.py  PermissionService – role assignments (S)
└── client.py              SharePointClient façade (composes services) (D)
```

- **Single Responsibility** – each module has one well-defined job.
- **Open/Closed** – `TokenProvider` is a `Protocol`; swap implementations without changing callers.
- **Dependency Inversion** – `SharePointClient` depends on `TokenProvider` (abstraction), not `ClientCredentialsTokenProvider` (concrete class).

---

## Limitations

- **Upload size**: The simple upload endpoint supports files up to ~4 MB.
  For larger files, use the resumable upload session API (not yet implemented).
- **Delegated permissions**: Only app-only (`client_credentials`) authentication
  is supported. Delegated (user-context) flows are not implemented.
- **Token expiry**: Tokens are cached in memory for the lifetime of the
  `SharePointClient` instance. For long-running processes, create a new
  instance or call `client._tokens.invalidate(scope)` to force a refresh.

---

## License

MIT License – see [LICENSE](LICENSE).
