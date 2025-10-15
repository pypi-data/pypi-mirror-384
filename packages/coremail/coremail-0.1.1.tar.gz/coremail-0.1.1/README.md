# Coremail Python SDK

[![PyPI version](https://badge.fury.io/py/coremail.svg)](https://badge.fury.io/py/coremail)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/coremail.svg)](https://pypi.org/project/coremail/)
[![Build Status](https://github.com/liudonghua123/coremail/workflows/Tests/badge.svg)](https://github.com/liudonghua123/coremail/actions)

A comprehensive Python SDK for interacting with Coremail XT API.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Development](#development)
- [License](#license)

## Features

- 🔐 **Secure Authentication**: Token-based authentication with automatic caching (1 hour TTL)
- 📦 **Comprehensive API Coverage**: Full support for user, domain, and system management
- 🧪 **Well Tested**: Extensively tested with 100% test coverage
- 📝 **Type Hints**: Full type annotations for better development experience
- 📊 **Rate Limiting**: Built-in token caching to optimize API usage
- 🔄 **Error Handling**: Unified error handling with proper exceptions

## Installation

```bash
pip install coremail
```

## Quick Start

```python
from coremail import CoremailClient

# Initialize the client with environment variables
client = CoremailClient()

# Or with explicit parameters
client = CoremailClient(
    base_url="http://your-host-of-coremail:9900/apiws/v3",
    app_id="your_app_id@your-domain.com",
    secret="your_secret_key"
)

# Example: Request a token
token = client.requestToken()
print(f"Token: {token}")

# Example: Get user attributes
user_attrs = client.getAttrs("test_user@your-domain.com")
print(f"User attributes: {user_attrs}")

# Example: Change user password
change_result = client.changeAttrs(
    "test_user@your-domain.com",
    {"password": "new_secure_password"}
)
print(f"Password changed: {change_result}")

# Example: Authenticate a user
auth_result = client.authenticate("test_user@your-domain.com", "password")
print(f"Authentication result: {auth_result}")
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
COREMAIL_BASE_URL=http://your-host-of-coremail:9900/apiws/v3
COREMAIL_APP_ID=your_app_id@your-domain.com
COREMAIL_SECRET=your_secret_key
```

### Manual Configuration

```python
from coremail import CoremailClient

client = CoremailClient(
    base_url="http://your-host-of-coremail:9900/apiws/v3",
    app_id="your_app_id@your-domain.com", 
    secret="your_secret_key"
)
```

## API Reference

### CoremailClient

The client provides direct access to all Coremail API endpoints:

- `requestToken()` - Request a new authentication token (with 1-hour cache)
- `authenticate(user_at_domain, password)` - Authenticate a user
- `getAttrs(user_at_domain, attrs=None)` - Get user attributes
- `changeAttrs(user_at_domain, attrs)` - Change user attributes
- `create(user_at_domain, attrs)` - Create a new user
- `delete(user_at_domain)` - Delete a user
- `list_users(domain=None, attrs=None)` - List users in the system or domain
- `listDomains(attrs=None)` - List domains in the system
- `getDomainAttrs(domain_name, attrs=None)` - Get domain attributes
- `changeDomainAttrs(domain_name, attrs)` - Change domain attributes
- `userExist(user_at_domain)` - Check if a user exists
- `search(user_at_domain, search_params)` - Search messages for a user
- `get_logs(log_type, start_time=None, end_time=None, limit=None)` - Get system logs
- `manage_group(operation, group_name, user_at_domain=None)` - Manage groups
- `get_system_config(config_type=None)` - Get system configuration
- `admin(operation, params=None)` - Perform administrative operations
- `refresh_token()` - Force refresh the authentication token

## Examples

### Basic User Management

```python
from coremail import CoremailClient

client = CoremailClient()

# Create a new user
new_user_result = client.create(
    "newuser@your-domain.com",
    {
        "password": "initial_password",
        "quota_mb": 1024,
        "user_enabled": True,
        "user_name": "New User"
    }
)

# Update user attributes
update_result = client.changeAttrs(
    "newuser@your-domain.com",
    {
        "password": "new_secure_password",
        "quota_mb": 2048
    }
)

# Get user info
user_info = client.getAttrs("newuser@your-domain.com")

# Delete user
delete_result = client.delete("newuser@your-domain.com")
```

### Domain Management

```python
# List all domains
domains = client.listDomains()

# Get domain information
domain_info = client.getDomainAttrs("your-domain.com")

# Update domain settings
client.changeDomainAttrs(
    "your-domain.com",
    {
        "quota_mb": 1024000,
        "max_users": 1000,
        "enabled": True
    }
)
```

### Authentication and Validation

```python
# Check if user exists by attempting to get attributes
result = client.getAttrs("test@your-domain.com")
exists = result.get('code') == 0

# Authenticate user directly
auth_response = client.authenticate("user@domain.com", "password")
is_authenticated = auth_response.get('code') == 0
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/liudonghua123/coremail.git
cd coremail

# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=coremail

# Run specific test file
pytest tests/test_client.py
```

### Code Quality

```bash
# Run type checking
mypy coremail

# Format code
black coremail tests

# Check linting
flake8 coremail tests
```

### Building

```bash
# Build the package
python -m build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues, please file them in the [Issues](https://github.com/liudonghua123/coremail/issues) section of the repository.

For questions and support, you can:
- Open an issue on GitHub
- Check the documentation
- Look at the examples in the `examples/` directory