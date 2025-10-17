"""Integration tests for voucher operations."""

import os
import pytest
from radiusdesk_api import RadiusDeskClient


# Skip all tests if credentials are not provided
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv('RADIUSDESK_URL'),
        os.getenv('RADIUSDESK_USERNAME'),
        os.getenv('RADIUSDESK_PASSWORD'),
        os.getenv('RADIUSDESK_CLOUD_ID'),
        os.getenv('RADIUSDESK_REALM_ID'),
        os.getenv('RADIUSDESK_PROFILE_ID')
    ]),
    reason="RadiusDesk credentials not provided in environment variables"
)


@pytest.fixture
def client():
    """Fixture providing an authenticated RadiusDesk client."""
    return RadiusDeskClient(
        base_url=os.getenv('RADIUSDESK_URL'),
        username=os.getenv('RADIUSDESK_USERNAME'),
        password=os.getenv('RADIUSDESK_PASSWORD'),
        cloud_id=os.getenv('RADIUSDESK_CLOUD_ID')
    )


@pytest.fixture
def test_voucher_config():
    """Fixture providing test voucher configuration."""
    return {
        'realm_id': int(os.getenv('RADIUSDESK_REALM_ID')),
        'profile_id': int(os.getenv('RADIUSDESK_PROFILE_ID'))
    }


@pytest.fixture
def cleanup_vouchers(client):
    """
    Fixture that tracks created voucher IDs and deletes them after the test.

    Usage:
        result = client.vouchers.create(...)
        cleanup_vouchers.append(voucher_id)
    """
    created_voucher_ids = []

    yield created_voucher_ids

    # Cleanup: Delete all created vouchers
    for voucher_id in created_voucher_ids:
        try:
            client.vouchers.delete(voucher_id=voucher_id)
            print(f"Cleaned up test voucher ID: {voucher_id}")
        except Exception as e:
            print(f"Failed to cleanup voucher ID {voucher_id}: {e}")


def test_list_vouchers(client):
    """Test listing vouchers."""
    result = client.vouchers.list(limit=10)
    assert isinstance(result, dict)
    assert 'items' in result or 'data' in result


def test_create_single_voucher(client, test_voucher_config, cleanup_vouchers):
    """Test creating a single voucher."""
    voucher = client.vouchers.create(
        realm_id=test_voucher_config['realm_id'],
        profile_id=test_voucher_config['profile_id'],
        quantity=1
    )
    assert isinstance(voucher, dict)
    assert 'name' in voucher
    assert 'id' in voucher
    assert len(voucher['name']) > 0

    # Track for cleanup
    voucher_id = voucher.get('id')
    if voucher_id:
        cleanup_vouchers.append(voucher_id)


def test_create_multiple_vouchers(client, test_voucher_config, cleanup_vouchers):
    """Test creating multiple vouchers."""
    result = client.vouchers.create(
        realm_id=test_voucher_config['realm_id'],
        profile_id=test_voucher_config['profile_id'],
        quantity=3
    )
    assert isinstance(result, list)
    assert len(result) == 3

    # Track all created vouchers for cleanup
    for voucher in result:
        voucher_id = voucher.get('id')
        if voucher_id:
            cleanup_vouchers.append(voucher_id)


def test_get_voucher_details(client, test_voucher_config, cleanup_vouchers):
    """Test getting voucher details and usage statistics."""
    # First create a voucher
    voucher = client.vouchers.create(
        realm_id=test_voucher_config['realm_id'],
        profile_id=test_voucher_config['profile_id'],
        quantity=1
    )

    # Track for cleanup
    voucher_id = voucher.get('id')
    if voucher_id:
        cleanup_vouchers.append(voucher_id)

    # Get its details (includes usage statistics)
    voucher_code = voucher.get('name')
    details = client.vouchers.get_details(voucher_code)
    assert isinstance(details, dict)


def test_list_vouchers_with_pagination(client):
    """Test listing vouchers with pagination parameters."""
    result = client.vouchers.list(limit=5, page=1, start=0)
    assert isinstance(result, dict)


def test_delete_voucher(client, test_voucher_config):
    """Test deleting a voucher."""
    # First create a voucher to delete
    voucher = client.vouchers.create(
        realm_id=test_voucher_config['realm_id'],
        profile_id=test_voucher_config['profile_id'],
        quantity=1
    )

    assert 'id' in voucher
    voucher_id = voucher.get('id')

    # Delete the voucher
    result = client.vouchers.delete(voucher_id=voucher_id)
    assert isinstance(result, dict)
    assert result.get('success') is True
