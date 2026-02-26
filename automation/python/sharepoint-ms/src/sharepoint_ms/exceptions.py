"""
Exception hierarchy for sharepoint-ms.

All library exceptions inherit from SharePointError so callers can catch
either the base class or a specific subclass.
"""
from __future__ import annotations


class SharePointError(RuntimeError):
    """Base exception for all sharepoint-ms errors."""


class AuthenticationError(SharePointError):
    """Raised when OAuth2 authentication fails (bad credentials, network error, etc.)."""


class NotFoundError(SharePointError):
    """Raised when a requested resource does not exist (HTTP 404)."""


class ForbiddenError(SharePointError):
    """Raised when the application lacks permission to access a resource (HTTP 403)."""


class ApiError(SharePointError):
    """Raised for unexpected Graph API or SharePoint REST API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
