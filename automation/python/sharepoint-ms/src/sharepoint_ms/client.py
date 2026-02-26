"""
SharePointClient – high-level façade for SharePoint Online automation.

This module is the single entry-point for library consumers.  It composes
the lower-level service classes behind a stable, flat API:

- Site resolution          → ``SiteService``
- Drive / file operations  → ``DriveService``
- Permission inspection    → ``PermissionService``

Callers create a ``SharePointClient`` with a ``SharePointConfig`` and call
methods directly on it; they never need to interact with the service classes.

Example::

    from sharepoint_ms import SharePointClient, SharePointConfig

    config = SharePointConfig(
        tenant_id="...",
        client_id="...",
        client_secret="...",
    )
    client = SharePointClient(config)

    site   = client.get_site("contoso.sharepoint.com", "/sites/TeamSite")
    drives = client.list_drives(site["id"])
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import SharePointConfig
from ._auth import ClientCredentialsTokenProvider
from ._http import GraphHttpClient, SharePointRestClient, GRAPH_SCOPE
from .site_service import SiteService
from .drive_service import DriveService
from .permission_service import PermissionService


class SharePointClient:
    """
    High-level façade for SharePoint Online automation via Microsoft Graph API.

    All methods authenticate lazily on first use; you do not need to call
    ``authenticate()`` explicitly unless you want to verify credentials upfront.

    Args:
        config: ``SharePointConfig`` with tenant, client ID, and secret.
    """

    def __init__(self, config: SharePointConfig) -> None:
        self._config = config
        self._tokens = ClientCredentialsTokenProvider(config)
        self._graph = GraphHttpClient(self._tokens, timeout=config.timeout_seconds)
        self._rest_clients: dict[str, SharePointRestClient] = {}

        self._sites = SiteService(self._graph)
        self._drives = DriveService(self._graph)
        self._permissions = PermissionService(
            self._graph,
            rest_client_factory=self._get_rest_client,
        )

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #

    def authenticate(self) -> None:
        """
        Proactively authenticate against Microsoft Graph API.

        Under normal use the client authenticates lazily on the first API call.
        Call this method explicitly to verify credentials at startup and get a
        clear ``AuthenticationError`` if anything is wrong.

        Raises:
            AuthenticationError: If the credentials are invalid or the tenant
                cannot be reached.
        """
        self._tokens.get_token(GRAPH_SCOPE)

    # ------------------------------------------------------------------ #
    # Sites
    # ------------------------------------------------------------------ #

    def get_site(self, hostname: str, site_path: str) -> dict[str, Any]:
        """
        Resolve a SharePoint site by hostname and server-relative path.

        Args:
            hostname:  SharePoint hostname, e.g. ``contoso.sharepoint.com``.
            site_path: Server-relative path, e.g. ``/sites/TeamSite`` or
                       ``/sites/virtualization/testing``.

        Returns:
            Site resource dict.  Important keys:

            - ``id``          – composite ID used in all subsequent calls
            - ``displayName`` – human-readable name
            - ``webUrl``      – full browser URL

        Example::

            site = client.get_site("contoso.sharepoint.com", "/sites/TeamSite")
            site_id = site["id"]
        """
        return self._sites.get_site(hostname, site_path)

    # ------------------------------------------------------------------ #
    # Drives (document libraries)
    # ------------------------------------------------------------------ #

    def list_drives(self, site_id: str) -> list[dict[str, Any]]:
        """
        List all document libraries (drives) in a site.

        Args:
            site_id: Composite site ID from ``get_site``.

        Returns:
            List of drive resources.  Key fields: ``id``, ``name``,
            ``driveType``, ``webUrl``.

        Example::

            drives = client.list_drives(site_id)
            for d in drives:
                print(d["name"], d["id"])
        """
        return self._drives.list_drives(site_id)

    def get_drive_by_name(self, site_id: str, drive_name: str) -> dict[str, Any]:
        """
        Find a document library by its display name (case-insensitive).

        Args:
            site_id:    Composite site ID.
            drive_name: Display name, e.g. ``Documents``.

        Returns:
            Drive resource dict.

        Raises:
            NotFoundError: If no library with that name exists.

        Example::

            drive = client.get_drive_by_name(site_id, "Documents")
            drive_id = drive["id"]
        """
        return self._drives.get_drive_by_name(site_id, drive_name)

    # ------------------------------------------------------------------ #
    # Listing items
    # ------------------------------------------------------------------ #

    def list_root_items(
        self, site_id: str, drive_id: str
    ) -> list[dict[str, Any]]:
        """
        List all items at the root of a document library.

        Args:
            site_id:  Composite site ID.
            drive_id: Drive ID from ``list_drives`` or ``get_drive_by_name``.

        Returns:
            List of ``driveItem`` resources.

        Example::

            items = client.list_root_items(site_id, drive_id)
        """
        return self._drives.list_root_items(site_id, drive_id)

    def list_folder_items(
        self, site_id: str, drive_id: str, folder_path: str
    ) -> list[dict[str, Any]]:
        """
        List all items inside a folder identified by its path from drive root.

        Args:
            site_id:     Composite site ID.
            drive_id:    Drive ID.
            folder_path: Path relative to drive root, e.g. ``Reports`` or
                         ``Reports/2024/Q1``.

        Returns:
            List of ``driveItem`` resources.

        Raises:
            NotFoundError: If the folder does not exist.

        Example::

            items = client.list_folder_items(site_id, drive_id, "Reports/2024")
        """
        return self._drives.list_folder_items(site_id, drive_id, folder_path)

    def list_items_by_id(
        self, site_id: str, drive_id: str, item_id: str
    ) -> list[dict[str, Any]]:
        """
        List items inside a folder identified by its Graph item ID.

        Useful when you already have the folder's ``id`` (e.g. from a previous
        listing) and want to avoid rebuilding the path.

        Args:
            site_id:  Composite site ID.
            drive_id: Drive ID.
            item_id:  ``id`` field of the folder ``driveItem``.

        Returns:
            List of child ``driveItem`` resources.
        """
        return self._drives.list_items_by_id(site_id, drive_id, item_id)

    def get_item_by_id(
        self, site_id: str, drive_id: str, item_id: str
    ) -> dict[str, Any]:
        """
        Get metadata for a single item by its Graph item ID.

        Args:
            item_id: ``id`` field of a ``driveItem``.

        Returns:
            ``driveItem`` resource dict.
        """
        return self._drives.get_item_by_id(site_id, drive_id, item_id)

    def get_item_by_path(
        self, site_id: str, drive_id: str, item_path: str
    ) -> dict[str, Any]:
        """
        Get metadata for a single item identified by its path from drive root.

        Args:
            item_path: Path relative to drive root, e.g. ``Reports/report.xlsx``.

        Returns:
            ``driveItem`` resource dict.

        Raises:
            NotFoundError: If the item does not exist at that path.
        """
        return self._drives.get_item_by_path(site_id, drive_id, item_path)

    # ------------------------------------------------------------------ #
    # File transfers
    # ------------------------------------------------------------------ #

    def download_file(
        self,
        site_id: str,
        drive_id: str,
        item_id: str,
        destination: str | Path,
    ) -> Path:
        """
        Download a file to a local path.

        Args:
            site_id:     Composite site ID.
            drive_id:    Drive ID.
            item_id:     ``id`` field of the file ``driveItem``.
            destination: Local file path.  Parent dirs are created automatically.

        Returns:
            Resolved ``Path`` of the downloaded file.

        Example::

            path = client.download_file(site_id, drive_id, item_id, "downloads/file.xlsx")
        """
        return self._drives.download_file(site_id, drive_id, item_id, destination)

    def upload_file(
        self,
        site_id: str,
        drive_id: str,
        folder_path: str,
        local_file: str | Path,
    ) -> dict[str, Any]:
        """
        Upload a local file to a folder in a document library.

        Args:
            site_id:     Composite site ID.
            drive_id:    Drive ID.
            folder_path: Target folder path from drive root.  Pass ``""`` to
                         upload directly to the library root.
            local_file:  Local file path.

        Returns:
            ``driveItem`` resource of the uploaded file (includes ``id``,
            ``name``, ``size``, ``webUrl``).

        Raises:
            FileNotFoundError: If *local_file* does not exist locally.

        Example::

            item = client.upload_file(site_id, drive_id, "Uploads", "report.pdf")
        """
        return self._drives.upload_file(site_id, drive_id, folder_path, local_file)

    # ------------------------------------------------------------------ #
    # Permissions
    # ------------------------------------------------------------------ #

    def get_user_site_permissions(
        self,
        user_email: str,
        hostname: str,
        site_path: str,
    ) -> dict[str, Any]:
        """
        Return the effective SharePoint permissions of a user on a site.

        Inspects direct user assignments, SharePoint group memberships,
        and AAD security-group memberships.

        Args:
            user_email: UPN or email of the user to inspect.
            hostname:   SharePoint hostname.
            site_path:  Server-relative site path.

        Returns:
            Dict with keys: ``user``, ``site``, ``effective_roles``,
            ``direct_assignments``, ``group_assignments``, ``has_access``.

        Example::

            result = client.get_user_site_permissions(
                "alice@contoso.com",
                "contoso.sharepoint.com",
                "/sites/TeamSite",
            )
            print(result["effective_roles"])
        """
        return self._permissions.get_user_site_permissions(
            user_email, hostname, site_path
        )

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _get_rest_client(self, hostname: str) -> SharePointRestClient:
        """Return (or create) a cached SharePointRestClient for *hostname*."""
        if hostname not in self._rest_clients:
            self._rest_clients[hostname] = SharePointRestClient(
                self._tokens, hostname, self._config.timeout_seconds
            )
        return self._rest_clients[hostname]
