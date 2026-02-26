"""
SharePoint document-library (drive) and file operations via Microsoft Graph API.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ._http import GraphHttpClient
from .exceptions import NotFoundError


class DriveService:
    """
    Provides file and folder operations for SharePoint document libraries.

    In SharePoint terminology a *document library* maps 1-to-1 to a Graph API
    *drive*.  Every operation requires a ``site_id`` (from ``SiteService``)
    and a ``drive_id`` (from ``list_drives`` or ``get_drive_by_name``).

    Single responsibility: manage drives, folders and files.
    """

    def __init__(self, http: GraphHttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------ #
    # Drives (document libraries)
    # ------------------------------------------------------------------ #

    def list_drives(self, site_id: str) -> list[dict[str, Any]]:
        """
        List all document libraries in a site.

        Args:
            site_id: Composite site ID returned by ``SiteService.get_site``.

        Returns:
            List of drive resources.  Key fields per item:

            - ``id``        – drive ID used in subsequent calls
            - ``name``      – display name (e.g. ``Documents``)
            - ``driveType`` – usually ``documentLibrary``
            - ``webUrl``    – browser URL of the library
        """
        return self._http.get_paged(f"/sites/{site_id}/drives")

    def get_drive_by_name(self, site_id: str, drive_name: str) -> dict[str, Any]:
        """
        Find a document library by its display name (case-insensitive).

        Args:
            site_id:    Composite site ID.
            drive_name: Display name of the library, e.g. ``Documents``.

        Returns:
            Drive resource dict.

        Raises:
            NotFoundError: If no library with that name is found.
        """
        drives = self.list_drives(site_id)
        for drive in drives:
            if drive.get("name", "").lower() == drive_name.lower():
                return drive
        available = [d.get("name") for d in drives]
        raise NotFoundError(
            f"Document library '{drive_name}' not found in site.\n"
            f"Available libraries: {available}"
        )

    # ------------------------------------------------------------------ #
    # Listing items
    # ------------------------------------------------------------------ #

    def list_root_items(self, site_id: str, drive_id: str) -> list[dict[str, Any]]:
        """
        List all items at the root of a document library.

        Args:
            site_id:  Composite site ID.
            drive_id: Drive ID from ``list_drives`` or ``get_drive_by_name``.

        Returns:
            List of ``driveItem`` resources.
        """
        return self._http.get_paged(
            f"/sites/{site_id}/drives/{drive_id}/root/children"
        )

    def list_folder_items(
        self, site_id: str, drive_id: str, folder_path: str
    ) -> list[dict[str, Any]]:
        """
        List items inside a folder identified by its path from the drive root.

        Args:
            site_id:     Composite site ID.
            drive_id:    Drive ID.
            folder_path: Path relative to drive root, e.g. ``Reports`` or
                         ``Reports/2024/Q1``.

        Returns:
            List of ``driveItem`` resources inside the folder.

        Raises:
            NotFoundError: If the folder path does not exist.
        """
        clean = folder_path.strip("/")
        endpoint = f"/sites/{site_id}/drives/{drive_id}/root:/{clean}:/children"
        return self._http.get_paged(endpoint)

    def list_items_by_id(
        self, site_id: str, drive_id: str, item_id: str
    ) -> list[dict[str, Any]]:
        """
        List items inside a folder identified by its Graph item ID.

        Args:
            item_id: ``id`` field of a folder ``driveItem``.

        Returns:
            List of child ``driveItem`` resources.
        """
        return self._http.get_paged(
            f"/sites/{site_id}/drives/{drive_id}/items/{item_id}/children"
        )

    def get_item_by_id(
        self, site_id: str, drive_id: str, item_id: str
    ) -> dict[str, Any]:
        """
        Get metadata for a single item identified by its Graph item ID.

        Args:
            item_id: ``id`` field of a ``driveItem``.

        Returns:
            ``driveItem`` resource dict.
        """
        return self._http.get(
            f"/sites/{site_id}/drives/{drive_id}/items/{item_id}"
        )

    def get_item_by_path(
        self, site_id: str, drive_id: str, item_path: str
    ) -> dict[str, Any]:
        """
        Get metadata for a single item identified by its path from the drive root.

        Args:
            item_path: Path relative to drive root, e.g. ``Reports/report.xlsx``.

        Returns:
            ``driveItem`` resource dict.

        Raises:
            NotFoundError: If the item does not exist at that path.
        """
        clean = item_path.strip("/")
        return self._http.get(f"/sites/{site_id}/drives/{drive_id}/root:/{clean}")

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

        The Graph API redirects file-content requests to pre-authenticated
        Azure Blob Storage URLs; this is handled automatically.

        Args:
            site_id:     Composite site ID.
            drive_id:    Drive ID.
            item_id:     ``id`` field of the file ``driveItem``.
            destination: Local path where the file will be saved.
                         Parent directories are created if they do not exist.

        Returns:
            Resolved ``Path`` of the downloaded file.
        """
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = self._http.get_raw(
            f"/sites/{site_id}/drives/{drive_id}/items/{item_id}/content"
        )
        dest.write_bytes(content)
        return dest

    def upload_file(
        self,
        site_id: str,
        drive_id: str,
        folder_path: str,
        local_file: str | Path,
    ) -> dict[str, Any]:
        """
        Upload a local file to a folder in a document library.

        Uses the Graph API simple upload endpoint (max ~4 MB).  For larger
        files use the resumable upload session API (not yet implemented).

        Args:
            site_id:     Composite site ID.
            drive_id:    Drive ID.
            folder_path: Target folder path relative to drive root.
                         Use an empty string ``""`` to upload to the library root.
            local_file:  Local path of the file to upload.

        Returns:
            ``driveItem`` resource dict of the uploaded file, including
            ``id``, ``name``, ``size``, and ``webUrl``.

        Raises:
            FileNotFoundError: If *local_file* does not exist.
        """
        file_path = Path(local_file)
        if not file_path.exists():
            raise FileNotFoundError(f"Local file not found: {file_path}")

        clean_folder = folder_path.strip("/")
        if clean_folder:
            endpoint = (
                f"/sites/{site_id}/drives/{drive_id}"
                f"/root:/{clean_folder}/{file_path.name}:/content"
            )
        else:
            endpoint = (
                f"/sites/{site_id}/drives/{drive_id}"
                f"/root:/{file_path.name}:/content"
            )

        return self._http.put(endpoint, file_path.read_bytes())
