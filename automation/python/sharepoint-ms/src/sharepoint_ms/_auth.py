"""
OAuth2 token provider for Microsoft identity platform.

Design
------
- ``TokenProvider`` is a Protocol (structural subtyping) so any object that
  implements ``get_token(scope)`` / ``invalidate(scope)`` qualifies.
- ``ClientCredentialsTokenProvider`` is the default implementation for
  server-to-server (app-only) flows.  It caches tokens in memory; tokens are
  re-fetched only after they are explicitly invalidated.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import requests

from .config import SharePointConfig
from .exceptions import AuthenticationError


@runtime_checkable
class TokenProvider(Protocol):
    """
    Protocol for OAuth2 bearer-token providers.

    Any class that implements ``get_token`` and ``invalidate`` satisfies this
    protocol; it does **not** need to inherit from ``TokenProvider``.
    """

    def get_token(self, scope: str) -> str:
        """Return a valid bearer token for *scope*."""
        ...

    def invalidate(self, scope: str) -> None:
        """Remove the cached token for *scope* so it will be re-fetched."""
        ...


class ClientCredentialsTokenProvider:
    """
    Fetches and caches tokens using the OAuth2 *client_credentials* flow.

    Tokens are stored in a plain ``dict`` keyed by OAuth2 scope string.
    Call ``invalidate(scope)`` to force a refresh on the next ``get_token`` call
    (useful when the token is close to expiry or after a 401 response).
    """

    def __init__(self, config: SharePointConfig) -> None:
        self._config = config
        self._cache: dict[str, str] = {}

    def get_token(self, scope: str) -> str:
        """Return a cached token or fetch a new one if the cache is empty."""
        if scope not in self._cache:
            self._cache[scope] = self._fetch_token(scope)
        return self._cache[scope]

    def invalidate(self, scope: str) -> None:
        """Evict *scope* from the cache so the next call will re-authenticate."""
        self._cache.pop(scope, None)

    def _fetch_token(self, scope: str) -> str:
        url = (
            f"https://login.microsoftonline.com"
            f"/{self._config.tenant_id}/oauth2/v2.0/token"
        )
        payload = {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "grant_type": "client_credentials",
            "scope": scope,
        }
        response = requests.post(
            url, data=payload, timeout=self._config.timeout_seconds
        )
        if response.status_code >= 400:
            raise AuthenticationError(
                f"Authentication failed (HTTP {response.status_code}): {response.text}"
            )
        token = response.json().get("access_token")
        if not token:
            raise AuthenticationError("No access_token found in OAuth2 response.")
        return token
