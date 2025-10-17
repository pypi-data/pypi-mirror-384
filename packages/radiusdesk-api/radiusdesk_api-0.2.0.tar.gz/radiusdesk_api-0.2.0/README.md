# RadiusDesk API Client

[![CI/CD](https://github.com/keeganwhite/radiusdesk-api/workflows/CI/CD/badge.svg)](https://github.com/keeganwhite/radiusdesk-api/actions)
[![PyPI version](https://badge.fury.io/py/radiusdesk-api.svg)](https://badge.fury.io/py/radiusdesk-api)
[![Python Support](https://img.shields.io/pypi/pyversions/radiusdesk-api.svg)](https://pypi.org/project/radiusdesk-api/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Python client for interacting with the cake4 [RADIUSdesk](https://www.radiusdesk.com/) API. This package provides a simple interface for managing vouchers, permanent users, and user balances in your RadiusDesk instance.

## Features

- **Token-based authentication** with automatic token management
- **Voucher management**: Create, list, and query voucher usage details
- **User management**: Create permanent users and add data/time top-ups
- **Automatic token refresh** to handle expired tokens seamlessly

## Installation

Install the package from PyPI using pip:

```bash
pip install radiusdesk-api
```

## Requirements

- Python 3.10 or higher
- A RadiusDesk instance with API access
- Valid credentials (username, password, cloud ID)

**Note**: The package automatically handles the RADIUSdesk API URL structure (`/cake4/rd_cake/`). You can provide the base URL with or without this path - it will be added automatically if not present.

## Quick Start

```python
from radiusdesk_api import RadiusDeskClient

# Initialize the client
# Note: The /cake4/rd_cake path is added automatically if not present
client = RadiusDeskClient(
    base_url="https://radiusdesk.example.com",  # or include /cake4/rd_cake
    username="admin",
    password="your-password",
    cloud_id="1"
)

# Create a voucher
voucher = client.vouchers.create(
    realm_id=1,
    profile_id=2,
    quantity=1
)
print(f"Created voucher: {voucher['name']} (ID: {voucher['id']})")

# List all vouchers
vouchers = client.vouchers.list(limit=100)
print(f"Total vouchers: {vouchers['totalCount']}")

# Create a permanent user
user = client.users.create(
    username="john.doe",
    password="secure-password",
    profile_id=2,
    name="John",
    surname="Doe",
    email="john.doe@example.com"
)
print(f"Created user: {user}")
```

## Usage Examples

### Authentication

The client handles authentication automatically, but you can also manage tokens manually:

```python
from radiusdesk_api import RadiusDeskClient

# Auto-login on initialization (default)
client = RadiusDeskClient(
    base_url="https://radiusdesk.example.com",
    username="admin",
    password="password",
    cloud_id="1"
)

# Defer authentication until first API call
client = RadiusDeskClient(
    base_url="https://radiusdesk.example.com",
    username="admin",
    password="password",
    cloud_id="1",
    auto_login=False
)

# Check connection
if client.check_connection():
    print("Connected to RadiusDesk!")

# Manually refresh token
new_token = client.refresh_token()
```

### Voucher Operations

#### Create Vouchers

```python
# Create a single voucher
voucher = client.vouchers.create(
    realm_id=1,
    profile_id=2,
    quantity=1,
    never_expire=True
)
print(f"Voucher code: {voucher['name']} (ID: {voucher['id']})")

# Create multiple vouchers
vouchers = client.vouchers.create(
    realm_id=1,
    profile_id=2,
    quantity=10,
    never_expire=False
)
print(f"Created {len(vouchers)} vouchers")
```

#### List Vouchers

```python
# List all vouchers
result = client.vouchers.list(limit=100)
for voucher in result['items']:
    print(f"Voucher: {voucher['name']}")

# List with pagination
result = client.vouchers.list(limit=50, page=2, start=50)
```

#### Get Voucher Details

```python
# Get detailed usage information about a voucher
# (includes connection history, data usage, session info)
voucher_code = voucher['name']
details = client.vouchers.get_details(voucher_code)
print(details)
```

#### Delete Voucher

```python
# Delete a voucher by ID
result = client.vouchers.delete(voucher_id=123)
if result.get('success'):
    print("Voucher deleted successfully!")
```

### User Operations

#### Create Permanent Users

```python
# Create a user with all details
user = client.users.create(
    username="john.doe",
    password="secure-password",
    realm_id=1,
    profile_id=2,
    name="John",
    surname="Doe",
    email="john.doe@example.com",
    phone="+1234567890",
    address="123 Main St"
)

# Create a user with minimal information (required params only)
user = client.users.create(
    username="jane.doe",
    password="secure-password",
    realm_id=1,
    profile_id=2
)
```

#### List Users

```python
# List all permanent users
users = client.users.list(limit=100)
for user in users['items']:
    print(f"User: {user['username']}")

# List with pagination
users = client.users.list(limit=50, page=2)
```

#### Add Top-Ups (Data/Time Balance)

```python
# Add data balance to a user
result = client.users.add_data(
    user_id=123,
    amount=2,
    unit="gb",
    comment="Monthly data allocation"
)

# Add time balance to a user
result = client.users.add_time(
    user_id=123,
    amount=60,
    unit="minutes",
    comment="Bonus time"
)

# Supported units:
# Data: "mb", "gb"
# Time: "minutes", "hours", "days"
```

#### Delete User

```python
# Delete a permanent user
result = client.users.delete(user_id=123)
print(f"User deleted: {result}")
```

## Error Handling

The package provides custom exceptions for different error scenarios:

```python
from radiusdesk_api import (
    RadiusDeskClient,
    AuthenticationError,
    APIError,
    TokenExpiredError
)

try:
    client = RadiusDeskClient(
        base_url="https://radiusdesk.example.com",
        username="admin",
        password="wrong-password",
        cloud_id="1"
    )
except AuthenticationError as e:
    print(f"Authentication failed: {e}")

try:
    voucher = client.vouchers.create(
        realm_id=999,  # Invalid realm
        profile_id=999  # Invalid profile
    )
except APIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
```

## Logging

The package uses Python's built-in logging module. Enable logging to see detailed information:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = RadiusDeskClient(
    base_url="https://radiusdesk.example.com",
    username="admin",
    password="password",
    cloud_id="1"
)
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/keeganwhite/radiusdesk-api.git
cd radiusdesk-api

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .

# Create .env file from template
cp .env.example .env
# Edit .env with your credentials
```

### Running Tests

The package uses integration tests that require a live RadiusDesk instance.

**Option 1: Using .env file (Recommended)**

```bash
# Create .env file from template
cp .env.example .env
# Edit .env with your credentials

# Run tests
./run_tests.sh
```

**Option 2: Manual environment variables**

```bash
export RADIUSDESK_URL="https://radiusdesk.example.com"
export RADIUSDESK_USERNAME="admin"
export RADIUSDESK_PASSWORD="password"
export RADIUSDESK_CLOUD_ID="1"
export RADIUSDESK_REALM_ID="1"
export RADIUSDESK_PROFILE_ID="2"

pytest tests/ -v
```

### Code Quality

```bash
# Run linting
flake8 radiusdesk_api tests

# Format code
black radiusdesk_api tests
```

### Building the Package

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Check the build
twine check dist/*
```

### Publishing to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

## GitHub Actions

The package includes a GitHub Actions workflow that:

- Runs linting with flake8
- Runs integration tests on Python 3.10, 3.11, and 3.12
- Builds the package
- Publishes to PyPI when a commit message contains `[release]`

### Required GitHub Secrets

Set these secrets in your GitHub repository settings:

- `RADIUSDESK_URL`: URL of your RadiusDesk instance
- `RADIUSDESK_USERNAME`: Username for authentication
- `RADIUSDESK_PASSWORD`: Password for authentication
- `RADIUSDESK_CLOUD_ID`: Cloud ID
- `RADIUSDESK_REALM_ID`: Realm ID for testing
- `RADIUSDESK_PROFILE_ID`: Profile ID for testing
- `PYPI_API_TOKEN`: Your PyPI API token for publishing

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: https://pypi.org/project/radiusdesk-api/
- **Source Code**: https://github.com/keeganwhite/radiusdesk-api
- **Issue Tracker**: https://github.com/keeganwhite/radiusdesk-api/issues
- **RadiusDesk**: https://www.radiusdesk.com/
- **RadiusDesk GitHub**: https://github.com/RADIUSdesk/rdcore
