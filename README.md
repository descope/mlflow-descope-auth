# MLflow Descope Authentication Plugin

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A simple, standards-compliant authentication plugin for [MLflow](https://mlflow.org/) using [Descope](https://www.descope.com/).

## Features

🔐 **Descope Authentication** - Secure token-based authentication with auto-refresh  
🌐 **Browser Login UI** - Built-in login page with Descope Web Component  
🍪 **Cookie-Based Sessions** - Secure, HttpOnly cookies with automatic refresh

## How It Works

This plugin integrates with MLflow via the `mlflow.app` entry point, providing server-side authentication with a browser-based login UI.

```
Browser → /auth/login → Descope Web Component → Cookie Set → MLflow UI
                                    ↑
                              before_request hook validates cookies
```

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

## Quick Start

1. **Set environment variables**:
   ```bash
   export DESCOPE_PROJECT_ID="P2XXXXX"
   ```

2. **Start MLflow with Descope authentication**:
   ```bash
   mlflow server --app-name descope --host 0.0.0.0 --port 5000
   ```

3. **Access MLflow UI**: Open `http://localhost:5000` in your browser. You'll be redirected to the login page.

4. **Logout**: Visit `/auth/logout` to clear your session.

## Configuration Reference

| Variable                     | Required | Default              | Description                                     |
| ---------------------------- | -------- | -------------------- | ----------------------------------------------- |
| `DESCOPE_PROJECT_ID`         | ✅ Yes   | -                    | Your Descope Project ID                         |
| `DESCOPE_FLOW_ID`            | ❌ No    | `sign-up-or-in`      | Descope flow ID for login                       |
| `DESCOPE_ADMIN_ROLES`        | ❌ No    | `admin,mlflow-admin` | Comma-separated list of admin roles             |
| `DESCOPE_DEFAULT_PERMISSION` | ❌ No    | `READ`               | Default permission level (READ/EDIT/MANAGE)     |
| `DESCOPE_USERNAME_CLAIM`     | ❌ No    | `sub`                | JWT claim to use as username (`sub` or `email`) |
| `DESCOPE_COOKIE_SECURE`      | ❌ No    | `false`              | Enable secure cookies (set `true` for HTTPS)    |

## Plugin Entry Point

This plugin registers one MLflow entry point:

```toml
[project.entry-points."mlflow.app"]
descope = "mlflow_descope_auth.server:create_app"
```

## Architecture

### Components

- **`server.py`** - Flask app factory for `mlflow.app` entry point
- **`auth_routes.py`** - Login, logout, and user info endpoints
- **`client.py`** - Descope SDK wrapper for token validation
- **`config.py`** - Configuration management
- **`store.py`** - User store adapter (optional, for advanced use cases)

### Authentication Flow

1. User visits MLflow UI
2. `before_request` hook checks for valid session cookie (`DS`)
3. If no valid session → redirect to `/auth/login`
4. User authenticates via Descope Web Component
5. On success, session cookies (`DS`, `DSR`) are set
6. User redirected back to MLflow UI
7. `after_request` hook refreshes cookies if token was refreshed

## Development

### Setup

```bash
# Clone and setup
git clone https://github.com/descope/mlflow-descope-auth.git
cd mlflow-descope-auth

# Install with uv
uv sync

# Run tests
uv run pytest tests/ -v

# Lint and format
uv run ruff check mlflow_descope_auth tests --fix
uv run ruff format mlflow_descope_auth tests
```

### Verify Plugin Registration

```bash
python -c "from importlib.metadata import entry_points; print([ep.name for ep in entry_points(group='mlflow.app')])"
```

## Troubleshooting

### Plugin Not Loaded

```bash
# Verify plugin is installed
pip list | grep mlflow-descope-auth

# Check entry points
python -c "from importlib.metadata import entry_points; print([ep.name for ep in entry_points(group='mlflow.app')])"
```

### Cookie Issues

- Ensure `DESCOPE_COOKIE_SECURE=true` when using HTTPS
- Check browser dev tools for cookie presence (`DS`, `DSR`)
- Verify cookies are not being blocked by browser settings

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/descope/mlflow-descope-auth/issues)
- **Descope Docs**: [docs.descope.com](https://docs.descope.com/)
- **MLflow Docs**: [mlflow.org/docs](https://mlflow.org/docs/latest/index.html)

---

Made with ❤️ by the MLflow Descope Auth Contributors
