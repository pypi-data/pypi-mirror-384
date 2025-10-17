"""Tests for URL normalization."""

from radiusdesk_api.client import RadiusDeskClient


def test_url_normalization_without_cake_path():
    """Test that /cake4/rd_cake is added when not present."""
    url = RadiusDeskClient._normalize_base_url("https://example.com")
    assert url == "https://example.com/cake4/rd_cake"


def test_url_normalization_with_trailing_slash():
    """Test that trailing slashes are handled correctly."""
    url = RadiusDeskClient._normalize_base_url("https://example.com/")
    assert url == "https://example.com/cake4/rd_cake"


def test_url_normalization_with_cake_path():
    """Test that /cake4/rd_cake is not duplicated when already present."""
    url = RadiusDeskClient._normalize_base_url("https://example.com/cake4/rd_cake")
    assert url == "https://example.com/cake4/rd_cake"


def test_url_normalization_with_cake_path_and_trailing_slash():
    """Test URL with /cake4/rd_cake and trailing slash."""
    url = RadiusDeskClient._normalize_base_url("https://example.com/cake4/rd_cake/")
    assert url == "https://example.com/cake4/rd_cake"


def test_url_normalization_different_formats():
    """Test various URL formats."""
    test_cases = [
        ("http://radiusdesk.local", "http://radiusdesk.local/cake4/rd_cake"),
        ("https://radiusdesk.local/", "https://radiusdesk.local/cake4/rd_cake"),
        ("https://radiusdesk.local/cake4/rd_cake", "https://radiusdesk.local/cake4/rd_cake"),
        ("https://radiusdesk.local/cake4/rd_cake/", "https://radiusdesk.local/cake4/rd_cake"),
        ("http://192.168.1.100", "http://192.168.1.100/cake4/rd_cake"),
        ("http://192.168.1.100:8080", "http://192.168.1.100:8080/cake4/rd_cake"),
    ]

    for input_url, expected_url in test_cases:
        result = RadiusDeskClient._normalize_base_url(input_url)
        assert result == expected_url, (
            f"Expected {expected_url}, got {result} for input {input_url}"
        )
