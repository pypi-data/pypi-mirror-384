"""Authentication management for RadiusDesk API."""

import logging
from typing import Optional
import requests

from .exceptions import AuthenticationError
from .utils import build_headers, generate_timestamp

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication and token lifecycle for RadiusDesk API."""

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize AuthManager.

        Args:
            base_url: Base URL of the RadiusDesk instance
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self._token: Optional[str] = None

    @property
    def token(self) -> str:
        """
        Get the current authentication token, logging in if necessary.

        Returns:
            Authentication token

        Raises:
            AuthenticationError: If login fails
        """
        if self._token is None:
            self._token = self.login()
        return self._token

    def login(self) -> str:
        """
        Authenticate and retrieve the token.

        Returns:
            Authentication token

        Raises:
            AuthenticationError: If authentication fails
        """
        login_url = f"{self.base_url}/dashboard/authenticate.json"
        logger.info(f"Logging in to {login_url}")

        payload = {
            "auto_compact": "false",
            "username": self.username,
            "password": self.password,
        }

        try:
            response = requests.post(
                login_url,
                headers=build_headers(),
                data=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            if data.get("success"):
                self._token = data["data"]["token"]
                logger.info("Authentication successful")
                return self._token
            else:
                error_msg = data.get("message", "Unknown error")
                raise AuthenticationError(f"Login failed: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Login request failed: {str(e)}")
        except (KeyError, ValueError) as e:
            raise AuthenticationError(f"Invalid response format: {str(e)}")

    def check_token(self) -> bool:
        """
        Check the validity of the current token.

        Returns:
            True if token is valid, False otherwise
        """
        if self._token is None:
            return False

        check_token_url = f"{self.base_url}/dashboard/check_token.json"

        params = {
            "_dc": generate_timestamp(),
            "token": self._token,
            "auto_compact": "false",
        }
        cookies = {"Token": self._token}

        try:
            response = requests.get(
                check_token_url,
                headers=build_headers(),
                params=params,
                cookies=cookies,
                timeout=30
            )
            response.raise_for_status()

            # Check the success field in the JSON response
            data = response.json()
            return data.get("success", False)

        except requests.exceptions.RequestException:
            return False
        except (KeyError, ValueError):
            return False

    def refresh_token(self) -> str:
        """
        Refresh the authentication token.

        Returns:
            New authentication token

        Raises:
            AuthenticationError: If token refresh fails
        """
        logger.info("Refreshing authentication token")
        self._token = None
        return self.login()

    def invalidate_token(self) -> None:
        """Invalidate the current token."""
        self._token = None
        logger.info("Token invalidated")
