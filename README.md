# MLflow Descope Authentication Plugin

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A simple, standards-compliant authentication plugin for [MLflow](https://mlflow.org/) using [Descope](https://www.descope.com/).

## Features

✨ **Simple Plugin Architecture** - Uses MLflow's standard plugin system  
🔐 **Descope Authentication** - Secure token-based authentication  
🏷️ **Automatic Tagging** - User context automatically added to MLflow runs  
📊 **Request Headers** - User info propagated via HTTP headers  
⚡ **Zero Configuration** - Works with environment variables

## How It Works

This plugin integrates with MLflow via three standard plugin types:

1. **Request Auth Provider** - Adds Descope authentication to MLflow API requests
2. **Request Header Provider** - Injects user context into request headers
3. **Run Context Provider** - Automatically tags runs with user information

## Installation

```bash
pip install mlflow-descope-auth
```

Or from source:

```bash
git clone https://github.com/descope/mlflow-descope-auth.git
cd mlflow-descope-auth
pip install -e .
```

## Configuration

### 1. Set Up Descope

1. Sign up at [descope.com](https://www.descope.com/)
2. Create a new project
3. Copy your Project ID (starts with `P2`)
4. Create authentication flow in Descope Console

### 2. Get Authentication Tokens

Authenticate with Descope and obtain session tokens. You can use:

- [Descope Web SDK](https://docs.descope.com/build/guides/client_sdks/web/)
- [Descope Python SDK](https://docs.descope.com/build/guides/client_sdks/python/)
- Descope API directly

Example using Python SDK:

```python
from descope import DescopeClient

descope_client = DescopeClient(project_id="P2XXXXX")

# Authenticate user (example with magic link)
response = descope_client.magiclink.sign_in_or_up(
    method="email",
    login_id="user@example.com"
)

# Extract tokens
session_token = response["sessionToken"]["jwt"]
refresh_token = response["refreshToken"]["jwt"]

print(f"export DESCOPE_SESSION_TOKEN='{session_token}'")
print(f"export DESCOPE_REFRESH_TOKEN='{refresh_token}'")
```

### 3. Set Environment Variables

```bash
# Required
export DESCOPE_PROJECT_ID="P2XXXXX"
export DESCOPE_SESSION_TOKEN="<your-session-token>"
export DESCOPE_REFRESH_TOKEN="<your-refresh-token>"

# Optional (with defaults)
export DESCOPE_ADMIN_ROLES="admin,mlflow-admin"
export DESCOPE_DEFAULT_PERMISSION="READ"
export DESCOPE_USERNAME_CLAIM="sub"  # or "email"
```

### 4. Enable the Plugin

```bash
# Set MLflow tracking authentication
export MLFLOW_TRACKING_AUTH=descope

# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000
```

## Usage

Once configured, the plugin works automatically:

```python
import mlflow

# Plugin automatically adds authentication to requests
mlflow.set_tracking_uri("http://localhost:5000")

# Start a run - user context automatically added
with mlflow.start_run():
    mlflow.log_param("alpha", 0.5)
    mlflow.log_metric("rmse", 0.8)
```

### Automatic Run Tagging

The plugin automatically adds these tags to all runs:

- `descope.user_id` - User's Descope ID
- `descope.username` - Username
- `descope.email` - User's email
- `descope.name` - User's display name
- `descope.roles` - Comma-separated list of roles
- `descope.permissions` - Comma-separated list of permissions
- `descope.tenants` - Comma-separated list of tenants

### Request Headers

The plugin adds these headers to MLflow API requests:

- `X-Descope-User-ID`
- `X-Descope-Username`  
- `X-Descope-Email`
- `X-Descope-Roles`
- `X-Descope-Permissions`
- `X-Descope-Tenants`

## Development

### Setup with mise

```bash
# Install mise
curl https://mise.run | sh

# Clone and setup
git clone https://github.com/descope/mlflow-descope-auth.git
cd mlflow-descope-auth

# Install dependencies
mise run install

# Verify plugin is registered
mise run verify-plugin
```

### Available Tasks

```bash
# Development
mise run dev              # Start MLflow server with plugin enabled
mise run demo             # Run demo tracking session (requires tokens)

# Testing
mise run test             # Run tests with coverage
mise run test-quick       # Run tests without coverage
mise run verify-plugin    # Verify plugin entry points registered

# Code Quality
mise run lint             # Check code style
mise run format           # Format code
mise run check            # Run all checks (lint + format + type)
mise run fix              # Auto-fix all issues

# Maintenance
mise run clean            # Remove generated files
mise run pre-commit-install  # Install git hooks
mise run pre-commit       # Run hooks on all files
mise run ci               # Run full CI pipeline
```

## Plugin Entry Points

This plugin registers three MLflow entry points:

```toml
[project.entry-points."mlflow.request_auth_provider"]
descope = "mlflow_descope_auth.auth_provider:DescopeAuthProvider"

[project.entry-points."mlflow.request_header_provider"]
descope = "mlflow_descope_auth.header_provider:DescopeHeaderProvider"

[project.entry-points."mlflow.run_context_provider"]
descope = "mlflow_descope_auth.context_provider:DescopeContextProvider"
```

## Configuration Reference

| Variable                  | Required | Default              | Description                                     |
| ------------------------- | -------- | -------------------- | ----------------------------------------------- |
| `DESCOPE_PROJECT_ID`      | ✅ Yes   | -                    | Your Descope Project ID                         |
| `DESCOPE_SESSION_TOKEN`   | ✅ Yes   | -                    | Current session JWT token                       |
| `DESCOPE_REFRESH_TOKEN`   | ❌ No    | -                    | Refresh token for automatic renewal             |
| `DESCOPE_ADMIN_ROLES`     | ❌ No    | `admin,mlflow-admin` | Comma-separated list of admin roles             |
| `DESCOPE_DEFAULT_PERMISSION` | ❌ No | `READ`               | Default permission level (READ/EDIT/MANAGE)     |
| `DESCOPE_USERNAME_CLAIM`  | ❌ No    | `sub`                | JWT claim to use as username (`sub` or `email`) |
| `MLFLOW_TRACKING_AUTH`    | ✅ Yes   | -                    | Set to `descope` to enable plugin               |

## Architecture

### Simple Plugin Design

This plugin follows MLflow's standard plugin architecture:

```
MLflow Client
    ↓
[Auth Provider]     ← Adds authentication to requests
    ↓
[Header Provider]   ← Injects user context headers  
    ↓
[Context Provider]  ← Tags runs with user info
    ↓
MLflow Server
```

### Components

- **`auth_provider.py`** - Implements `RequestAuthProvider` for authentication
- **`header_provider.py`** - Implements `RequestHeaderProvider` for headers
- **`context_provider.py`** - Implements `RunContextProvider` for run tagging
- **`client.py`** - Descope SDK wrapper for token validation
- **`config.py`** - Configuration management
- **`store.py`** - User store adapter (optional, for advanced use cases)

## Troubleshooting

### Plugin Not Loaded

```bash
# Verify plugin is installed
pip list | grep mlflow-descope-auth

# Check entry points
python -c "import pkg_resources; print([ep for ep in pkg_resources.iter_entry_points('mlflow.request_auth_provider')])"
```

### Authentication Fails

```bash
# Check environment variables
env | grep DESCOPE

# Verify tokens are valid
python -c "
from mlflow_descope_auth import get_descope_client
import os
client = get_descope_client()
result = client.validate_session(
    os.environ['DESCOPE_SESSION_TOKEN'],
    os.environ.get('DESCOPE_REFRESH_TOKEN')
)
print('✓ Token valid')
"
```

### Enable Debug Logging

```bash
export MLFLOW_TRACKING_INSECURE_TLS=true  # For development only
export PYTHONWARNINGS=default

python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import mlflow
mlflow.set_tracking_uri('http://localhost:5000')
mlflow.search_runs()
"
```

## Comparison: Simple Plugin vs Full App

| Feature                    | Simple Plugin (This) | Full App Approach      |
| -------------------------- | -------------------- | ---------------------- |
| **Architecture**           | Extends MLflow       | Wraps MLflow           |
| **Complexity**             | Low                  | High                   |
| **Dependencies**           | Minimal              | FastAPI, Uvicorn, etc. |
| **MLflow Compatibility**   | Standard             | Custom                 |
| **Maintenance**            | Easy                 | Complex                |
| **Integration**            | Plugin system        | App replacement        |
| **Setup**                  | Environment vars     | Config files + UI      |

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/descope/mlflow-descope-auth/wiki)
- **Issues**: [GitHub Issues](https://github.com/descope/mlflow-descope-auth/issues)
- **Descope Docs**: [docs.descope.com](https://docs.descope.com/)
- **MLflow Docs**: [mlflow.org/docs](https://mlflow.org/docs/latest/index.html)

## Related Projects

- [MLflow](https://mlflow.org/) - Open source platform for the ML lifecycle
- [Descope](https://www.descope.com/) - Authentication and user management
- [MLflow Plugin Guide](https://mlflow.org/docs/latest/plugins.html) - Official plugin documentation

---

Made with ❤️ by the MLflow Descope Auth Contributors
