"""
Low-level HTTP clients for Microsoft Graph API and SharePoint REST API.

Both clients share the same ``TokenProvider`` but request tokens with
different OAuth2 scopes:

- ``GraphHttpClient``        → scope ``https://graph.microsoft.com/.default``
- ``SharePointRestClient``   → scope ``https://{hostname}/.default``
"""
from __future__ import annotations

from typing import Any

import requests

from ._auth import TokenProvider
from .exceptions import ApiError, ForbiddenError, NotFoundError

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


class GraphHttpClient:
    """
    Thin HTTP wrapper around Microsoft Graph API v1.0.

    Responsibilities:
    - Attach bearer tokens to every request.
    - Follow pagination transparently in ``get_paged``.
    - Map HTTP error codes to typed exceptions.
    """

    def __init__(self, token_provider: TokenProvider, timeout: int = 30) -> None:
        self._tokens = token_provider
        self._timeout = timeout

    # ------------------------------------------------------------------ #
    # Public methods
    # ------------------------------------------------------------------ #

    def get(
        self,
        endpoint: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Perform a single GET and return the JSON body as a dict."""
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def get_paged(self, endpoint: str) -> list[dict[str, Any]]:
        """
        Retrieve all pages of a Graph API collection.

        Follows ``@odata.nextLink`` automatically and merges all ``value``
        arrays into a single list.
        """
        url: str | None = f"{GRAPH_BASE}{endpoint}"
        items: list[dict[str, Any]] = []
        while url:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self._timeout,
            )
            self._raise_for_status(response, "GET", url)
            body = response.json()
            items.extend(body.get("value", []))
            url = body.get("@odata.nextLink")
        return items

    def put(
        self,
        endpoint: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        """Perform a PUT with a binary body and return the JSON response."""
        response = self._request(
            "PUT",
            endpoint,
            data=data,
            extra_headers={"Content-Type": content_type},
        )
        return response.json()

    def get_raw(self, endpoint: str) -> bytes:
        """
        Perform a GET and return the raw response body bytes.

        Follows redirects automatically (Graph API download URLs often redirect
        to pre-authenticated Azure Blob Storage SAS URLs).
        """
        url = f"{GRAPH_BASE}{endpoint}"
        response = requests.get(
            url,
            headers=self._headers(),
            timeout=self._timeout,
            allow_redirects=True,
        )
        self._raise_for_status(response, "GET", url)
        return response.content

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tokens.get_token(GRAPH_SCOPE)}",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, str] | None = None,
        data: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> requests.Response:
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        url = f"{GRAPH_BASE}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=data,
            timeout=self._timeout,
            allow_redirects=True,
        )
        self._raise_for_status(response, method, url)
        return response

    @staticmethod
    def _raise_for_status(
        response: requests.Response, method: str, url: str
    ) -> None:
        code = response.status_code
        if code < 400:
            return
        text = response.text
        if code == 403:
            raise ForbiddenError(
                f"Access denied on {method} {url} (HTTP 403).\n"
                f"Check that the app registration has the required API permissions "
                f"with admin consent.\nResponse: {text}"
            )
        if code == 404:
            raise NotFoundError(
                f"Resource not found: {method} {url} (HTTP 404).\n"
                f"Verify hostname, site path, drive name, and item IDs."
            )
        raise ApiError(
            f"Graph API error (HTTP {code}) on {method} {url}: {text}",
            status_code=code,
        )


class SharePointRestClient:
    """
    HTTP client for the SharePoint REST API (``/_api/...`` endpoints).

    Used only for operations not available in Graph API, such as reading
    SharePoint role assignments and group memberships.
    """

    def __init__(
        self,
        token_provider: TokenProvider,
        hostname: str,
        timeout: int = 30,
    ) -> None:
        self._tokens = token_provider
        self._hostname = hostname
        self._timeout = timeout
        self._scope = f"https://{hostname}/.default"

    def get(self, site_path: str, api_path: str) -> Any:
        """Perform a GET and return the parsed JSON payload."""
        url = f"https://{self._hostname}{site_path}{api_path}"
        response = requests.get(
            url, headers=self._headers(), timeout=self._timeout
        )
        self._raise_for_status(response, "GET", url)
        return response.json()

    def get_list(self, site_path: str, api_path: str) -> list[dict[str, Any]]:
        """
        Perform a GET and extract the list portion of the response.

        Handles both OData v3 (``{"d": {"results": [...]}}`` ) and
        OData v4 (``{"value": [...]}`` ) formats.
        """
        payload = self.get(site_path, api_path)
        if isinstance(payload.get("value"), list):
            return payload["value"]
        return payload.get("d", {}).get("results", [])

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tokens.get_token(self._scope)}",
            "Accept": "application/json;odata=nometadata",
        }

    @staticmethod
    def _raise_for_status(
        response: requests.Response, method: str, url: str
    ) -> None:
        code = response.status_code
        if code < 400:
            return
        text = response.text
        if code == 403:
            raise ForbiddenError(
                f"Access denied on {method} {url} (HTTP 403).\n"
                f"The app may need SharePoint 'Sites.FullControl.All' permission.\n"
                f"Response: {text}"
            )
        if code == 404:
            raise NotFoundError(
                f"Resource not found: {method} {url} (HTTP 404).\n"
                f"Verify hostname and site path."
            )
        raise ApiError(
            f"SharePoint REST error (HTTP {code}) on {method} {url}: {text}",
            status_code=code,
        )
