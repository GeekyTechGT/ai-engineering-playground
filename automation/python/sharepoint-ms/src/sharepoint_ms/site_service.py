"""
SharePoint site operations via Microsoft Graph API.
"""
from __future__ import annotations

from typing import Any

from ._http import GraphHttpClient


class SiteService:
    """
    Provides site-level operations using the Microsoft Graph API.

    Single responsibility: resolve and inspect SharePoint sites.
    Instantiate via ``SharePointClient``; do not use directly unless you are
    composing a custom client.
    """

    def __init__(self, http: GraphHttpClient) -> None:
        self._http = http

    def get_site(self, hostname: str, site_path: str) -> dict[str, Any]:
        """
        Resolve a SharePoint site by hostname and server-relative path.

        The Graph API endpoint used is::

            GET /sites/{hostname}:/{site_path}

        Args:
            hostname:   SharePoint hostname, e.g. ``contoso.sharepoint.com``.
            site_path:  Server-relative path, e.g. ``/sites/TeamSite`` or
                        ``/sites/virtualization/testing``.

        Returns:
            Site resource dict.  Key fields:

            - ``id``          – composite ID used by all other Graph calls
            - ``displayName`` – human-readable name
            - ``webUrl``      – full URL of the site
        """
        # Strip any trailing slash; the Graph API requires the path without it.
        clean_path = site_path.strip("/")
        endpoint = f"/sites/{hostname}:/{clean_path}"
        return self._http.get(endpoint)
