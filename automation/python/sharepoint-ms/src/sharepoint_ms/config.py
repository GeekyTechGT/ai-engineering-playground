"""
Configuration dataclass for SharePointClient.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SharePointConfig:
    """
    Credentials and runtime settings required by SharePointClient.

    Attributes:
        tenant_id:       Azure AD tenant ID (GUID).
        client_id:       Azure AD app registration client ID (GUID).
        client_secret:   Client secret for the app registration.
        timeout_seconds: HTTP request timeout in seconds (default: 30).
    """

    tenant_id: str
    client_id: str
    client_secret: str
    timeout_seconds: int = 30
