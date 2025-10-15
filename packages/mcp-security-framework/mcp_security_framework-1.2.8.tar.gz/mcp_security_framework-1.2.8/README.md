# MCP Security Framework

[![PyPI version](https://badge.fury.io/py/mcp-security-framework.svg)](https://badge.fury.io/py/mcp-security-framework)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

Universal security framework for microservices with SSL/TLS, authentication, authorization, and rate limiting.

## Features

- 🔐 **Multi-method Authentication**: API keys, JWT tokens, X.509 certificates
- 🛡️ **SSL/TLS Management**: Server and client certificate handling
- 🔑 **Role-based Authorization**: Flexible permission system with role hierarchy
- ⚡ **Rate Limiting**: Configurable request rate limiting
- 🚀 **Framework Agnostic**: Works with FastAPI, Flask, Django, and standalone
- 🛠️ **CLI Tools**: Certificate management and security testing
- 📊 **Comprehensive Logging**: Security event logging and monitoring

## Quick Start

### Installation

```bash
# Basic installation
pip install mcp-security-framework

# With framework support
pip install mcp-security-framework[fastapi]
pip install mcp-security-framework[flask]
pip install mcp-security-framework[django]

# Development installation
pip install mcp-security-framework[dev]
```

### Basic Usage

```python
from mcp_security_framework import SecurityManager, SecurityConfig
from mcp_security_framework.schemas.config import AuthConfig, PermissionConfig

# Create configuration
config = SecurityConfig(
    auth=AuthConfig(
        enabled=True,
        methods=["api_key"],
        api_keys={"admin": "admin_key_123"}
    ),
    permissions=PermissionConfig(roles_file="roles.json")
)

# Create security manager
security_manager = SecurityManager(config)

# Validate request
result = security_manager.validate_request({
    "api_key": "admin_key_123",
    "required_permissions": ["read", "write"]
})

if result.is_valid:
    print("Access granted!")
else:
    print(f"Access denied: {result.error_message}")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from mcp_security_framework import create_fastapi_security_middleware, SecurityConfig

# Configuration
config = SecurityConfig(
    auth=AuthConfig(
        enabled=True,
        methods=["api_key", "jwt"],
        api_keys={"user": "user_key_456"}
    ),
    permissions=PermissionConfig(roles_file="roles.json")
)

# Create FastAPI app
app = FastAPI()

# Add security middleware
security_middleware = create_fastapi_security_middleware(config)
app.add_middleware(security_middleware)

@app.get("/secure")
async def secure_endpoint():
    return {"message": "Access granted"}

@app.get("/public")
async def public_endpoint():
    return {"message": "Public access"}
```

### Flask Integration

```python
from flask import Flask
from mcp_security_framework import create_flask_security_middleware, SecurityConfig

# Configuration
config = SecurityConfig(
    auth=AuthConfig(
        enabled=True,
        methods=["api_key"]
    ),
    permissions=PermissionConfig(roles_file="roles.json")
)

# Create Flask app
app = Flask(__name__)

# Add security middleware
security_middleware = create_flask_security_middleware(config)
app.wsgi_app = security_middleware(app.wsgi_app)

@app.route("/secure")
def secure_endpoint():
    return {"message": "Access granted"}
```

## CLI Tools

### Certificate Management

```bash
# Create root CA
mcp-cert create-ca --ca-name "My Root CA" --output-dir ./certs

# Create client certificate
mcp-cert create-client-cert --name "client1" --roles "user,admin" --permissions "read,write"

# Create server certificate
mcp-cert create-server-cert --name "api-server" --domains "api.example.com"
```

### Security Testing

```bash
# Validate configuration
mcp-security validate-config --config-file security_config.json

# Test authentication
mcp-security test-auth --config-file security_config.json --api-key "test_key"
```

## Configuration

### Basic Configuration File

```json
{
  "ssl": {
    "enabled": true,
    "cert_file": "server.crt",
    "key_file": "server.key",
    "ca_cert_file": "ca.crt",
    "verify_mode": "CERT_REQUIRED",
    "min_version": "TLSv1.2"
  },
  "auth": {
    "enabled": true,
    "methods": ["api_key", "jwt", "certificate"],
    "api_keys": {
      "admin": "admin_key_123",
      "user": "user_key_456"
    },
    "jwt_secret": "your_jwt_secret_key",
    "jwt_expiry_hours": 24,
    "public_paths": ["/docs", "/health"]
  },
  "certificates": {
    "ca_dir": "./certs",
    "roles_oid": "1.3.6.1.4.1.99999.1.1",
    "permissions_oid": "1.3.6.1.4.1.99999.1.2",
    "verify_certificates": true,
    "check_revocation": true
  },
  "permissions": {
    "roles_file": "roles.json",
    "deny_by_default": true,
    "case_sensitive": false,
    "allow_wildcard": true
  },
  "rate_limit": {
    "enabled": true,
    "rate_limit": 100,
    "time_window": 60,
    "by_ip": true,
    "by_user": true
  }
}
```

### Roles and Permissions

```json
{
  "roles": {
    "admin": {
      "name": "admin",
      "description": "Administrator role",
      "permissions": ["read", "write", "delete", "admin"],
      "priority": 100
    },
    "user": {
      "name": "user",
      "description": "Regular user role",
      "permissions": ["read", "write"],
      "priority": 50
    },
    "guest": {
      "name": "guest",
      "description": "Guest role",
      "permissions": ["read"],
      "priority": 10
    }
  },
  "role_hierarchy": {
    "roles": {
      "admin": ["user"],
      "user": ["guest"]
    }
  },
  "default_policy": {
    "deny_by_default": true,
    "require_role_match": true,
    "case_sensitive": false,
    "allow_wildcard": true
  }
}
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [API Reference](docs/api_reference.md)
- [Examples](docs/examples/)
  - [FastAPI Integration](docs/examples/fastapi_integration.md)
  - [Flask Integration](docs/examples/flask_integration.md)
  - [Standalone Usage](docs/examples/standalone_usage.md)
- [Security Guide](docs/security/)
  - [SSL/TLS Setup](docs/security/ssl_tls.md)
  - [Authentication Methods](docs/security/authentication.md)
  - [Authorization and Roles](docs/security/authorization.md)
  - [Certificate Management](docs/security/certificates.md)
- [Troubleshooting](docs/troubleshooting.md)

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/mcp-security/mcp-security-framework.git
cd mcp-security-framework

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_security_framework --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Lint code
flake8 src tests
mypy src

# Run all quality checks
tox
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
sphinx-build -b html docs docs/_build/html
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format and lint your code (`black`, `isort`, `flake8`, `mypy`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Security

If you discover a security vulnerability, please report it to us at security@mcp.example.com.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://mcp-security-framework.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/mcp-security/mcp-security-framework/issues)
- 💬 [Discussions](https://github.com/mcp-security/mcp-security-framework/discussions)
- 📧 [Email Support](mailto:support@mcp.example.com)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.
