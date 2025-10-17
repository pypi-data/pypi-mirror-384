"""Utility functions for the RadiusDesk API client."""

import time
from typing import Any, Dict


def generate_timestamp() -> str:
    """
    Generate a timestamp string for API requests.

    Returns:
        Timestamp string in milliseconds
    """
    return str(int(time.time() * 1000))


def parse_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate API response data.

    Args:
        response_data: Raw response data from the API

    Returns:
        Parsed response data

    Raises:
        ValueError: If response format is invalid
    """
    if not isinstance(response_data, dict):
        raise ValueError("Invalid response format: expected dictionary")

    return response_data


def build_headers(content_type: str = "application/x-www-form-urlencoded") -> Dict[str, str]:
    """
    Build request headers for API calls.

    Args:
        content_type: Content-Type header value

    Returns:
        Dictionary of headers
    """
    return {
        "Content-Type": f"{content_type}; charset=UTF-8"
    }
