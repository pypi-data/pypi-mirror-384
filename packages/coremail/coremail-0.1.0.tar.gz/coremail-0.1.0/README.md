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
from coremail import CoremailClient, CoremailAPI

# Initialize the client with environment variables
client = CoremailClient()

# Or with explicit parameters
client = CoremailClient(
    base_url="http://your-host-of-coremail:9900/apiws/v3",
    app_id="your_app_id@your-domain.com",
    secret="your_secret_key"
)

# Initialize the API wrapper
api = CoremailAPI(client)

# Example: Check if user exists
user_exists = api.user_exists("test_user@your-domain.com")
print(f"User exists: {user_exists}")

# Example: Get user attributes
user_attrs = api.get_user_info("test_user@your-domain.com")
print(f"User attributes: {user_attrs}")

# Example: Change user password
change_result = api.change_user_attributes(
    "test_user@your-domain.com",
    {"password": "new_secure_password"}
)
print(f"Password changed: {change_result}")
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

The low-level client provides direct access to all Coremail API endpoints:

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
- `search_messages(user_at_domain, search_params)` - Search messages for a user
- `get_logs(log_type, start_time=None, end_time=None, limit=None)` - Get system logs
- `manage_group(operation, group_name, user_at_domain=None)` - Manage groups
- `get_system_config(config_type=None)` - Get system configuration
- `admin(operation, params=None)` - Perform administrative operations
- `refresh_token()` - Force refresh the authentication token

### CoremailAPI

The high-level API wrapper provides simplified methods:

- `get_user_info(user_at_domain)` - Get complete user information
- `change_user_attributes(user_at_domain, attrs)` - Change user attributes
- `create_user(user_at_domain, attrs)` - Create a new user
- `delete_user(user_at_domain)` - Delete a user
- `list_users(domain=None, attrs=None)` - List users in the system or domain
- `list_domains(attrs=None)` - List domains in the system
- `get_domain_info(domain_name, attrs=None)` - Get domain information
- `change_domain_attributes(domain_name, attrs)` - Change domain attributes
- `user_exists(user_at_domain)` - Check if a user exists (wrapper for userExist)
- `search_messages(user_at_domain, search_params)` - Search messages for a user
- `get_logs(log_type, start_time=None, end_time=None, limit=None)` - Get system logs
- `manage_group(operation, group_name, user_at_domain=None)` - Manage groups
- `get_system_config(config_type=None)` - Get system configuration
- `admin_operation(operation, params=None)` - Perform administrative operations
- `authenticate_user(user_at_domain, password)` - Authenticate a user and return boolean
- `check_user_exists(user_at_domain)` - Check if user exists (via getAttrs)

## Examples

### Basic User Management

```python
from coremail import CoremailClient, CoremailAPI

client = CoremailClient()
api = CoremailAPI(client)

# Create a new user
new_user_result = api.create_user(
    "newuser@your-domain.com",
    {
        "password": "initial_password",
        "quota_mb": 1024,
        "user_enabled": True,
        "user_name": "New User"
    }
)

# Update user attributes
update_result = api.change_user_attributes(
    "newuser@your-domain.com",
    {
        "password": "new_secure_password",
        "quota_mb": 2048
    }
)

# Get user info
user_info = api.get_user_info("newuser@your-domain.com")

# Delete user
delete_result = api.delete_user("newuser@your-domain.com")
```

### Domain Management

```python
# List all domains
domains = api.list_domains()

# Get domain information
domain_info = api.get_domain_info("your-domain.com")

# Update domain settings
api.change_domain_attributes(
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
# Check if user exists
exists = api.user_exists("test@your-domain.com")

# Authenticate user
is_authenticated = api.authenticate_user("user@domain.com", "password")

# Manual authentication
auth_response = client.authenticate("user@domain.com", "password")
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