"""
sharepoint-ms – Python library for Microsoft SharePoint Online automation.

Public API
----------
::

    from sharepoint_ms import SharePointClient, SharePointConfig
    from sharepoint_ms import SharePointError, AuthenticationError, NotFoundError

The only classes you normally need are ``SharePointClient`` and
``SharePointConfig``.  The exception classes are re-exported for convenience
so callers do not need to import from sub-modules.
"""
from .config import SharePointConfig
from .client import SharePointClient
from .exceptions import (
    SharePointError,
    AuthenticationError,
    NotFoundError,
    ForbiddenError,
    ApiError,
)

__version__ = "0.2.0"

__all__ = [
    "SharePointClient",
    "SharePointConfig",
    "SharePointError",
    "AuthenticationError",
    "NotFoundError",
    "ForbiddenError",
    "ApiError",
    "__version__",
]
