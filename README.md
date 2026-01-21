# MLflow Descope Authentication Plugin

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A production-ready authentication plugin for [MLflow](https://mlflow.org/) using [Descope](https://www.descope.com/)'s Flow-based authentication pattern. This plugin enables SSO, MFA, and centralized user management for MLflow without hardcoding authentication methods.

## Features

✨ **Flow-Based Authentication** - Configure auth methods in Descope Console, not in code  
🔐 **Multiple Auth Methods** - OAuth, SAML, Magic Link, OTP, Passwords, TOTP (all configurable)  
🎯 **Zero-Touch Updates** - Change authentication methods without redeploying  
👥 **User Management** - Centralized user, role, and permission management  
🏢 **Multi-Tenant Support** - Built-in tenant isolation (optional)  
🔄 **Auto Token Refresh** - Seamless session management  
⚡ **Production Ready** - Type-safe, tested, and documented

## Architecture

```
User → Descope Flow (configured in console) → MLflow Plugin → MLflow UI
                                                 ↓
                                        Session Validation
                                        Permission Mapping
                                        User Management
```

## Quick Start

### Prerequisites

- Python 3.8+
- MLflow 2.0+
- Descope account (free tier available at [descope.com](https://www.descope.com/))

### Installation

```bash
pip install mlflow-descope-auth
```

Or install from source:

```bash
git clone https://github.com/descope/mlflow-descope-auth.git
cd mlflow-descope-auth
pip install -e .
```

### Configuration

1. **Create a Descope Project**
   - Sign up at [descope.com](https://www.descope.com/)
   - Create a new project
   - Copy your Project ID (starts with `P2`)

2. **Configure Authentication Flow**
   - In Descope Console, go to Authentication → Flows
   - Create or use the default `sign-up-or-in` flow
   - Configure your desired authentication methods (OAuth, SAML, etc.)

3. **Set Environment Variables**

Create a `.env` file:

```bash
# Required
DESCOPE_PROJECT_ID=P2XXXXX

# Optional (with defaults)
DESCOPE_FLOW_ID=sign-up-or-in
DESCOPE_REDIRECT_URL=/
DESCOPE_ADMIN_ROLES=admin,mlflow-admin
DESCOPE_DEFAULT_PERMISSION=READ
```

### Running MLflow with Descope Auth

```bash
# Using MLflow plugin system
mlflow server --app-name descope-auth --host 0.0.0.0 --port 5000

# Or with backend/artifact configuration
mlflow server \
  --app-name descope-auth \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root ./mlartifacts \
  --host 0.0.0.0 \
  --port 5000
```

Visit `http://localhost:5000` - you'll be redirected to the Descope-powered login page!

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DESCOPE_PROJECT_ID` | ✅ Yes | - | Your Descope Project ID (from console) |
| `DESCOPE_MANAGEMENT_KEY` | ❌ No | - | Management key for advanced features |
| `DESCOPE_FLOW_ID` | ❌ No | `sign-up-or-in` | Flow ID configured in Descope Console |
| `DESCOPE_REDIRECT_URL` | ❌ No | `/` | URL to redirect after successful login |
| `DESCOPE_WEB_COMPONENT_VERSION` | ❌ No | `3.54.0` | Descope web component version |
| `DESCOPE_BASE_URL` | ❌ No | `https://api.descope.com` | Descope API base URL |
| `DESCOPE_ADMIN_ROLES` | ❌ No | `admin,mlflow-admin` | Comma-separated list of admin roles |
| `DESCOPE_DEFAULT_PERMISSION` | ❌ No | `READ` | Default permission level (READ/EDIT/MANAGE) |
| `DESCOPE_USERNAME_CLAIM` | ❌ No | `sub` | JWT claim to use as username (`sub` or `email`) |

### MLflow Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MLFLOW_BACKEND_STORE_URI` | `sqlite:///mlflow.db` | MLflow backend store |
| `MLFLOW_ARTIFACT_ROOT` | `./mlartifacts` | Artifact storage location |

## How It Works

### 1. Login Flow

```
User visits MLflow → Redirect to /auth/login
                   ↓
      HTML page with <descope-wc flow-id="sign-up-or-in">
                   ↓
      User completes authentication (configured in console)
                   ↓
      Web component emits success event with JWT tokens
                   ↓
      Tokens stored in secure cookies (DS, DSR)
                   ↓
      Redirect to MLflow UI
```

### 2. Session Validation

On each request:
1. **Middleware** extracts tokens from cookies
2. **Descope SDK** validates session (auto-refreshes if expired)
3. **User claims** extracted from JWT (username, roles, permissions)
4. **Request state** populated with user info
5. **MLflow** processes request with user context

### 3. Permission Mapping

Descope roles/permissions → MLflow permission levels:

| Descope | MLflow | Access |
|---------|--------|--------|
| `admin`, `mlflow-admin` | `MANAGE` | Full access |
| `mlflow:manage` permission | `MANAGE` | Full access |
| `mlflow:edit` permission | `EDIT` | Read + Write |
| `mlflow:read` permission | `READ` | Read-only |
| Default (no specific permission) | `READ` | Read-only |

Configure admin roles via `DESCOPE_ADMIN_ROLES` environment variable.

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/descope/mlflow-descope-auth.git
cd mlflow-descope-auth

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with uv
uv sync --extra dev
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_config.py

# Run with verbose output
uv run pytest -v

# Generate coverage report
uv run pytest --cov=mlflow_descope_auth --cov-report=html
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
uv run black mlflow_descope_auth tests

# Lint code
uv run ruff check mlflow_descope_auth tests

# Type checking
uv run mypy mlflow_descope_auth
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v

# Generate coverage report
pytest --cov=mlflow_descope_auth --cov-report=html
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black mlflow_descope_auth tests

# Lint code
ruff check mlflow_descope_auth tests

# Type checking
mypy mlflow_descope_auth
```

## Examples

### Docker Compose

```yaml
version: '3.8'

services:
  mlflow:
    image: python:3.11-slim
    command: >
      sh -c "
        pip install mlflow mlflow-descope-auth &&
        mlflow server --app-name descope-auth --host 0.0.0.0
      "
    environment:
      - DESCOPE_PROJECT_ID=${DESCOPE_PROJECT_ID}
      - DESCOPE_FLOW_ID=sign-up-or-in
      - MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow.db
    ports:
      - "5000:5000"
    volumes:
      - mlflow-data:/mlflow

volumes:
  mlflow-data:
```

Run with:

```bash
DESCOPE_PROJECT_ID=P2XXXXX docker-compose up
```

### Kubernetes

See `examples/kubernetes.yaml` for a complete Kubernetes deployment example.

### Custom Permission Mapping

Create a custom config:

```python
from mlflow_descope_auth import Config, set_config

config = Config(
    DESCOPE_PROJECT_ID="P2XXXXX",
    ADMIN_ROLES=["admin", "superuser", "mlflow-admin"],
    DEFAULT_PERMISSION="EDIT",  # More permissive default
)

set_config(config)
```

## Advanced Features

### Multi-Tenant Support

Enable tenant-based access control:

```python
from mlflow_descope_auth import get_descope_client

client = get_descope_client()

# Validate tenant-specific permissions
has_access = client.validate_tenant_permissions(
    jwt_response,
    tenant="team-alpha",
    permissions=["mlflow:read"]
)
```

### Custom Middleware

Add custom authentication logic:

```python
from fastapi import Request
from mlflow_descope_auth.middleware import AuthenticationMiddleware

class CustomAuthMiddleware(AuthenticationMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Add custom pre-auth logic
        response = await super().dispatch(request, call_next)
        # Add custom post-auth logic
        return response
```

## Troubleshooting

### Common Issues

**Problem**: `ValueError: DESCOPE_PROJECT_ID environment variable is required`  
**Solution**: Set `DESCOPE_PROJECT_ID` in your `.env` file or environment

**Problem**: Login page shows but authentication fails  
**Solution**: Check that your Flow ID exists in Descope Console and is configured correctly

**Problem**: `AuthException: Invalid session`  
**Solution**: Clear browser cookies and try again. Check that your Descope Project ID is correct.

**Problem**: User redirected to login in a loop  
**Solution**: Ensure cookies are enabled and your domain is configured in Descope Console under "Application URLs"

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Roadmap

- [x] Flow-based authentication
- [x] Session management with auto-refresh
- [x] Basic permission mapping
- [ ] Advanced permission mapping with FGA
- [ ] User sync from Descope
- [ ] Admin UI for user management
- [ ] Audit logging
- [ ] Rate limiting
- [ ] Webhook support for user updates

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/descope/mlflow-descope-auth/wiki)
- **Issues**: [GitHub Issues](https://github.com/descope/mlflow-descope-auth/issues)
- **Discussions**: [GitHub Discussions](https://github.com/descope/mlflow-descope-auth/discussions)
- **Descope Docs**: [docs.descope.com](https://docs.descope.com/)
- **MLflow Docs**: [mlflow.org/docs](https://mlflow.org/docs/latest/index.html)

## Acknowledgments

- [MLflow](https://mlflow.org/) - Open source platform for the ML lifecycle
- [Descope](https://www.descope.com/) - Authentication and user management platform
- [mlflow-oidc-auth](https://github.com/mlflow-oidc/mlflow-oidc-auth) - Reference implementation
- [django-descope](https://github.com/descope/django-descope) - Django integration inspiration

---

Made with ❤️ by the MLflow Descope Auth Contributors
