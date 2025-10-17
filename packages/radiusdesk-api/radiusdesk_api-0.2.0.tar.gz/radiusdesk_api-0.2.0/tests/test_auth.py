"""Integration tests for authentication."""

import os
import pytest
from radiusdesk_api import RadiusDeskClient, AuthenticationError


# Skip all tests if credentials are not provided
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv('RADIUSDESK_URL'),
        os.getenv('RADIUSDESK_USERNAME'),
        os.getenv('RADIUSDESK_PASSWORD'),
        os.getenv('RADIUSDESK_CLOUD_ID')
    ]),
    reason="RadiusDesk credentials not provided in environment variables"
)


@pytest.fixture
def radiusdesk_config():
    """Fixture providing RadiusDesk configuration from environment variables."""
    return {
        'base_url': os.getenv('RADIUSDESK_URL'),
        'username': os.getenv('RADIUSDESK_USERNAME'),
        'password': os.getenv('RADIUSDESK_PASSWORD'),
        'cloud_id': os.getenv('RADIUSDESK_CLOUD_ID'),
    }


def test_successful_authentication(radiusdesk_config):
    """Test successful authentication with valid credentials."""
    client = RadiusDeskClient(**radiusdesk_config)
    assert client.auth.token is not None
    assert isinstance(client.auth.token, str)
    assert len(client.auth.token) > 0


def test_token_validation(radiusdesk_config):
    """Test token validation."""
    client = RadiusDeskClient(**radiusdesk_config)
    result = client.auth.check_token()
    assert result is True, f"check_token returned {result}, but token is valid (login succeeded)"


def test_connection_check(radiusdesk_config):
    """Test connection check."""
    client = RadiusDeskClient(**radiusdesk_config)
    result = client.check_connection()
    assert result is True, f"check_connection returned {result}"


def test_token_refresh(radiusdesk_config):
    """Test token refresh."""
    client = RadiusDeskClient(**radiusdesk_config)

    new_token = client.refresh_token()
    assert new_token is not None
    assert isinstance(new_token, str)


def test_invalid_credentials():
    """Test authentication failure with invalid credentials."""
    with pytest.raises(AuthenticationError):
        RadiusDeskClient(
            base_url=os.getenv('RADIUSDESK_URL', 'https://example.com'),
            username='invalid_user',
            password='invalid_password',
            cloud_id='1',
            auto_login=True
        )


def test_deferred_authentication(radiusdesk_config):
    """Test client initialization with deferred authentication."""
    config = radiusdesk_config.copy()
    config['auto_login'] = False

    client = RadiusDeskClient(**config)
    # Token should not be generated yet
    assert client.auth._token is None

    # Accessing token should trigger login
    token = client.auth.token
    assert token is not None
    assert isinstance(token, str)
