"""User management for RadiusDesk API."""

import logging
from typing import Dict, Any
import requests

from .exceptions import APIError
from .utils import build_headers, generate_timestamp

logger = logging.getLogger(__name__)


class UserManager:
    """Manages permanent user operations for RadiusDesk API."""

    def __init__(self, base_url: str, auth_manager, cloud_id: str):
        """
        Initialize UserManager.

        Args:
            base_url: Base URL of the RadiusDesk instance
            auth_manager: AuthManager instance for authentication
            cloud_id: Cloud ID for the RadiusDesk instance
        """
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
        self.cloud_id = cloud_id

    def create(
        self,
        username: str,
        password: str,
        profile_id: int,
        realm_id: int,
        name: str = "",
        surname: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
        data_cap_type: str = "hard",
        active: bool = True,
        always_active: bool = True,
        static_ip: str = "",
        extra_name: str = "",
        extra_value: str = "",
        site: str = "",
        ppsk: str = "",
        realm_vlan_id: int = 0,
        language: str = "4_4",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a permanent user in the RadiusDesk API.

        Args:
            username: Username for the permanent user
            password: Password for the permanent user
            profile_id: ID of the profile to assign to the user
            realm_id: ID of the realm
            name: User's first name (default: "")
            surname: User's surname (default: "")
            email: User's email address (default: "")
            phone: User's phone number (default: "")
            address: User's address (default: "")
            data_cap_type: Data cap type - "hard" or "soft" (default: "hard")
            active: Whether the user is active (default: True)
            always_active: Whether the user is always active (default: True)
            static_ip: Static IP address (default: "")
            extra_name: Extra name field (default: "")
            extra_value: Extra value field (default: "")
            site: Site identifier (default: "")
            ppsk: Pre-shared key (default: "")
            realm_vlan_id: Realm VLAN ID (default: 0)
            language: Language code (default: "4_4")
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dictionary containing the created user data

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/permanent-users/add.json"
        token = self.auth_manager.token

        payload = {
            "username": username,
            "password": password,
            "realm_id": realm_id,
            "profile_id": profile_id,
            "data_cap_type": data_cap_type,
            "name": name,
            "surname": surname,
            "language": language,
            "phone": phone,
            "email": email,
            "address": address,
            "static_ip": static_ip,
            "extra_name": extra_name,
            "extra_value": extra_value,
            "site": site,
            "ppsk": ppsk,
            "realm_vlan_id": realm_vlan_id,
            "token": token,
            "cloud_id": self.cloud_id,
        }

        # Add boolean fields (they need to be sent as "active" string if True)
        if active:
            payload["active"] = "active"
        if always_active:
            payload["always_active"] = "always_active"

        # Add any additional parameters
        payload.update(kwargs)

        cookies = {"Token": token}

        logger.info(f"Creating permanent user: {username}")

        try:
            response = requests.post(
                url,
                headers=build_headers(),
                data=payload,
                cookies=cookies,
                timeout=30
            )
            response.raise_for_status()
            response_data = response.json()

            # Check if the operation was successful
            if not response_data.get('success', True):
                error_msg = response_data.get('message', 'Unknown error')
                errors = response_data.get('errors', {})
                if errors:
                    error_details = ', '.join([f"{k}: {v}" for k, v in errors.items()])
                    error_msg = f"{error_msg} - {error_details}"
                # Use 422 (Unprocessable Entity) for validation/business logic errors
                # Original HTTP status was {response.status_code} but operation failed
                raise APIError(f"Failed to create permanent user: {error_msg}", status_code=422)

            logger.info(f"Created permanent user: {username}")
            # Return just the user data, not the full response wrapper
            return response_data.get('data', response_data)

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to create permanent user: {str(e)}", status_code=status_code)

    def list(self, limit: int = 100, page: int = 1, start: int = 0) -> Dict[str, Any]:
        """
        Fetch permanent users from the RadiusDesk API.

        Args:
            limit: Maximum number of users to fetch
            page: Page number
            start: Starting offset

        Returns:
            Dictionary containing users data

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/permanent-users/index.json"
        token = self.auth_manager.token

        params = {
            "_dc": generate_timestamp(),
            "page": page,
            "start": start,
            "limit": limit,
            "token": token,
            "sel_language": "4_4",
            "cloud_id": self.cloud_id,
        }
        cookies = {"Token": token}

        logger.info(f"Fetching permanent users from {url}")

        try:
            response = requests.get(
                url,
                headers=build_headers(),
                params=params,
                cookies=cookies,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to fetch permanent users: {str(e)}", status_code=status_code)

    def add_data(
        self,
        user_id: int,
        amount: int,
        unit: str = "gb",
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Add data balance to a permanent user via top-up.

        Args:
            user_id: ID of the permanent user
            amount: Amount of data to add
            unit: Unit for data amount ("mb", "gb", etc.)
            comment: Optional comment for the top-up

        Returns:
            Dictionary containing the top-up response

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/top-ups/add.json"
        token = self.auth_manager.token

        payload = {
            "permanent_user_id": user_id,
            "type": "data",
            "value": amount,
            "data_unit": unit,
            "comment": comment,
            "token": token,
            "cloud_id": self.cloud_id,
        }

        cookies = {"Token": token}

        logger.info(f"Adding {amount}{unit} data to user ID: {user_id}")

        try:
            response = requests.post(
                url,
                headers=build_headers(),
                data=payload,
                cookies=cookies,
                timeout=30
            )
            response.raise_for_status()

            response_data = response.json()
            logger.info(f"Added data top-up for user ID: {user_id}")
            return response_data

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to add data top-up: {str(e)}", status_code=status_code)

    def add_time(
        self,
        user_id: int,
        amount: int,
        unit: str = "minutes",
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Add time balance to a permanent user via top-up.

        Args:
            user_id: ID of the permanent user
            amount: Amount of time to add
            unit: Unit for time amount ("minutes", "hours", "days")
            comment: Optional comment for the top-up

        Returns:
            Dictionary containing the top-up response

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/top-ups/add.json"
        token = self.auth_manager.token

        payload = {
            "permanent_user_id": user_id,
            "type": "time",
            "value": amount,
            "time_unit": unit,
            "comment": comment,
            "token": token,
            "cloud_id": self.cloud_id,
        }

        cookies = {"Token": token}

        logger.info(f"Adding {amount} {unit} time to user ID: {user_id}")

        try:
            response = requests.post(
                url,
                headers=build_headers(),
                data=payload,
                cookies=cookies,
                timeout=30
            )
            response.raise_for_status()

            response_data = response.json()
            logger.info(f"Added time top-up for user ID: {user_id}")
            return response_data

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to add time top-up: {str(e)}", status_code=status_code)

    def delete(self, user_id: int) -> Dict[str, Any]:
        """
        Delete a permanent user.

        Args:
            user_id: ID of the user to delete

        Returns:
            Dictionary containing the deletion response

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/permanent-users/delete.json"
        token = self.auth_manager.token

        # Query parameters
        params = {
            "token": token,
            "cloud_id": self.cloud_id,
        }

        # JSON payload as array
        payload = [{"id": user_id}]

        cookies = {"Token": token}

        # Build headers with JSON content type
        headers = build_headers()
        headers["Content-Type"] = "application/json"

        logger.info(f"Deleting permanent user ID: {user_id}")

        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=payload,
                cookies=cookies,
                timeout=30
            )
            response.raise_for_status()

            response_data = response.json()

            # Check if the operation was successful
            if not response_data.get('success', True):
                error_msg = response_data.get('message', 'Unknown error')
                errors = response_data.get('errors', {})
                if errors:
                    error_details = ', '.join([f"{k}: {v}" for k, v in errors.items()])
                    error_msg = f"{error_msg} - {error_details}"
                # Use 422 (Unprocessable Entity) for validation/business logic errors
                # Original HTTP status was {response.status_code} but operation failed
                raise APIError(f"Failed to delete permanent user: {error_msg}", status_code=422)

            logger.info(f"Deleted permanent user ID: {user_id}")
            return response_data

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to delete permanent user: {str(e)}", status_code=status_code)
