"""Voucher management for RadiusDesk API."""

import logging
from typing import Dict, Any, Union
import requests

from .exceptions import APIError
from .utils import build_headers, generate_timestamp

logger = logging.getLogger(__name__)


class VoucherManager:
    """Manages voucher operations for RadiusDesk API."""

    def __init__(self, base_url: str, auth_manager, cloud_id: str):
        """
        Initialize VoucherManager.

        Args:
            base_url: Base URL of the RadiusDesk instance
            auth_manager: AuthManager instance for authentication
            cloud_id: Cloud ID for the RadiusDesk instance
        """
        self.base_url = base_url.rstrip('/')
        self.auth_manager = auth_manager
        self.cloud_id = cloud_id

    def list(self, limit: int = 100, page: int = 1, start: int = 0) -> Dict[str, Any]:
        """
        Fetch vouchers from the RadiusDesk API.

        Args:
            limit: Maximum number of vouchers to fetch
            page: Page number
            start: Starting offset

        Returns:
            Dictionary containing vouchers data

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/vouchers/index.json"
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

        logger.info(f"Fetching vouchers from {url}")

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
            raise APIError(f"Failed to fetch vouchers: {str(e)}", status_code=status_code)

    def get_details(self, voucher_code: str, limit: int = 150) -> Dict[str, Any]:
        """
        Fetch the usage details and statistics for a specific voucher.

        This method retrieves accounting records (radaccts) for a voucher,
        which includes connection history, data usage, and session information.

        Args:
            voucher_code: The voucher code to fetch details for
            limit: Maximum number of records to fetch

        Returns:
            Dictionary containing voucher usage details and statistics

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/radaccts/index.json"
        token = self.auth_manager.token

        params = {
            "_dc": generate_timestamp(),
            "username": voucher_code,
            "page": 1,
            "start": 0,
            "limit": limit,
            "token": token,
            "sel_language": "4_4",
            "cloud_id": self.cloud_id,
        }
        cookies = {"Token": token}

        logger.info(f"Fetching voucher details for {voucher_code}")

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
            raise APIError(f"Failed to fetch voucher details: {str(e)}", status_code=status_code)

    def create(
        self,
        realm_id: int,
        profile_id: int,
        quantity: int = 1,
        never_expire: bool = True,
        extra_name: str = "",
        extra_value: str = ""
    ) -> Union[Dict[str, Any], list]:
        """
        Create voucher(s) in the RadiusDesk API.

        Args:
            realm_id: ID of the realm
            profile_id: ID of the profile
            quantity: Number of vouchers to create
            never_expire: Whether vouchers should never expire
            extra_name: Extra name field
            extra_value: Extra value field

        Returns:
            If quantity=1, returns the voucher data (dict) with keys: id, name, etc.
            If quantity>1, returns list of voucher data dicts

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/vouchers/add.json"
        token = self.auth_manager.token

        payload = {
            "single_field": "true",
            "realm_id": realm_id,
            "profile_id": profile_id,
            "quantity": quantity,
            "never_expire": "on" if never_expire else "off",
            "extra_name": extra_name,
            "extra_value": extra_value,
            "token": token,
            "sel_language": "4_4",
            "cloud_id": self.cloud_id,
        }

        cookies = {"Token": token}

        logger.info(f"Creating {quantity} voucher(s)")

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
            logger.info(f"Response data: {response_data}")

            # Check if the operation was successful
            if not response_data.get('success', True):
                error_msg = response_data.get('message', 'Unknown error')
                errors = response_data.get('errors', {})
                if errors:
                    error_details = ', '.join([f"{k}: {v}" for k, v in errors.items()])
                    error_msg = f"{error_msg} - {error_details}"
                raise APIError(f"Failed to create voucher: {error_msg}", status_code=422)

            if quantity == 1:
                voucher_data = response_data["data"][0]
                logger.info(f"Created voucher: {voucher_data.get('name')}")
                return voucher_data
            else:
                voucher_list = response_data["data"]
                logger.info(f"Created {quantity} vouchers")
                return voucher_list

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to create voucher: {str(e)}", status_code=status_code)
        except (KeyError, IndexError) as e:
            raise APIError(f"Invalid response format: {str(e)}")

    def delete(self, voucher_id: int) -> Dict[str, Any]:
        """
        Delete a voucher.

        Args:
            voucher_id: ID of the voucher to delete

        Returns:
            Dictionary containing the deletion response

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}/vouchers/delete.json"
        token = self.auth_manager.token

        # Query parameters
        params = {
            "token": token,
            "cloud_id": self.cloud_id,
        }

        # JSON payload as array
        payload = [{"id": voucher_id}]

        cookies = {"Token": token}

        # Build headers with JSON content type
        headers = build_headers()
        headers["Content-Type"] = "application/json"

        logger.info(f"Deleting voucher ID: {voucher_id}")

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
                raise APIError(f"Failed to delete voucher: {error_msg}", status_code=422)

            logger.info(f"Deleted voucher ID: {voucher_id}")
            return response_data

        except requests.exceptions.RequestException as e:
            status_code = None
            if hasattr(e, 'response'):
                status_code = getattr(e.response, 'status_code', None)
            raise APIError(f"Failed to delete voucher: {str(e)}", status_code=status_code)
