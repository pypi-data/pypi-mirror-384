"""Main client for RadiusDesk API."""

import logging

from .auth import AuthManager
from .vouchers import VoucherManager
from .users import UserManager

logger = logging.getLogger(__name__)


class RadiusDeskClient:
    """
    Main client for interacting with the RadiusDesk API.

    This client provides a unified interface for managing vouchers, users,
    and authentication with a RadiusDesk instance.

    Example:
        >>> client = RadiusDeskClient(
        ...     base_url="https://radiusdesk.example.com",
        ...     username="admin",
        ...     password="secret",
        ...     cloud_id="1"
        ... )
        >>> voucher = client.vouchers.create(realm_id=1, profile_id=2)
        >>> users = client.users.list()
    """

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        """
        Normalize the base URL to include /cake4/rd_cake path if not present.

        RadiusDesk API endpoints are structured as:
        http://server/cake4/rd_cake/endpoint.json

        Args:
            base_url: Base URL provided by user

        Returns:
            Normalized base URL with /cake4/rd_cake path
        """
        url = base_url.rstrip('/')

        # Check if URL already contains cake4/rd_cake
        if '/cake4/rd_cake' not in url:
            url = f"{url}/cake4/rd_cake"

        return url

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        cloud_id: str,
        auto_login: bool = True
    ):
        """
        Initialize the RadiusDesk API client.

        Args:
            base_url: Base URL of the RadiusDesk instance
                (e.g., "https://radiusdesk.example.com" or
                "https://radiusdesk.example.com/cake4/rd_cake")
            username: Username for authentication
            password: Password for authentication
            cloud_id: Cloud ID for the RadiusDesk instance
            auto_login: Whether to automatically login on initialization

        Raises:
            AuthenticationError: If auto_login is True and authentication fails
        """
        # Normalize base URL to include /cake4/rd_cake if not present
        self.base_url = self._normalize_base_url(base_url)
        self.cloud_id = cloud_id

        # Initialize authentication manager with normalized URL
        self._auth = AuthManager(self.base_url, username, password)

        # Initialize resource managers with normalized URL
        self._vouchers = VoucherManager(self.base_url, self._auth, cloud_id)
        self._users = UserManager(self.base_url, self._auth, cloud_id)

        # Optionally login immediately to validate credentials
        if auto_login:
            self._auth.login()
            logger.info("RadiusDesk client initialized and authenticated")
        else:
            logger.info("RadiusDesk client initialized (deferred authentication)")

    @property
    def vouchers(self) -> VoucherManager:
        """
        Get the voucher manager.

        Returns:
            VoucherManager instance for managing vouchers
        """
        return self._vouchers

    @property
    def users(self) -> UserManager:
        """
        Get the user manager.

        Returns:
            UserManager instance for managing permanent users
        """
        return self._users

    @property
    def auth(self) -> AuthManager:
        """
        Get the authentication manager.

        Returns:
            AuthManager instance for managing authentication
        """
        return self._auth

    def check_connection(self) -> bool:
        """
        Check if the connection to RadiusDesk is working.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            return self._auth.check_token()
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False

    def refresh_token(self) -> str:
        """
        Manually refresh the authentication token.

        Returns:
            New authentication token

        Raises:
            AuthenticationError: If token refresh fails
        """
        return self._auth.refresh_token()
