"""
RadiusDesk API Client
~~~~~~~~~~~~~~~~~~~~~

A Python client for interacting with the RadiusDesk API.

Basic usage:

    >>> from radiusdesk_api import RadiusDeskClient
    >>> client = RadiusDeskClient(
    ...     base_url="https://radiusdesk.example.com",
    ...     username="admin",
    ...     password="secret",
    ...     cloud_id="1"
    ... )
    >>> voucher = client.vouchers.create(realm_id=1, profile_id=2)
    >>> print(voucher)

Full documentation is available at https://github.com/keeganwhite/radiusdesk-api
"""

__version__ = "0.1.0"
__author__ = "Keegan White"
__license__ = "GPL-3.0-or-later"

from .client import RadiusDeskClient
from .exceptions import (
    RadiusDeskError,
    AuthenticationError,
    TokenExpiredError,
    APIError,
    ValidationError,
    ResourceNotFoundError,
)

__all__ = [
    "RadiusDeskClient",
    "RadiusDeskError",
    "AuthenticationError",
    "TokenExpiredError",
    "APIError",
    "ValidationError",
    "ResourceNotFoundError",
    "__version__",
]
