# Quickstart Guide

Get MLflow running with Descope authentication in 5 minutes!

## Prerequisites

- Python 3.9 or higher installed
- pip package manager
- A Descope account (free at [descope.com](https://www.descope.com/))

## Step 1: Create a Descope Project

1. Go to [app.descope.com](https://app.descope.com/) and sign up/login
2. Click "Create New Project"
3. Give it a name (e.g., "MLflow Auth")
4. Copy your **Project ID** (starts with `P2`)

## Step 2: Get Authentication Tokens

Authenticate with Descope to obtain session tokens. You can use the Descope Python SDK:

```python
from descope import DescopeClient

descope_client = DescopeClient(project_id="P2XXXXX")

# Authenticate user (example with magic link)
response = descope_client.magiclink.sign_in_or_up(
    method="email",
    login_id="user@example.com"
)

# Extract session token
session_token = response["sessionToken"]["jwt"]
print(f"export DESCOPE_SESSION_TOKEN='{session_token}'")
```

Or use any other Descope authentication method (OAuth, SAML, etc.) via:
- [Descope Web SDK](https://docs.descope.com/build/guides/client_sdks/web/)
- [Descope Python SDK](https://docs.descope.com/build/guides/client_sdks/python/)
- Descope API directly

> **Note**: Token refresh is handled automatically by the server, not via environment variables.

## Step 3: Install MLflow Descope Auth

```bash
pip install mlflow-descope-auth
```

## Step 4: Configure Environment

Set the required environment variables:

```bash
# Required
export DESCOPE_PROJECT_ID="P2XXXXX"
export DESCOPE_SESSION_TOKEN="<your-session-token>"

# Enable the plugin
export MLFLOW_TRACKING_AUTH=descope

# Optional (with defaults)
export DESCOPE_ADMIN_ROLES="admin,mlflow-admin"
export DESCOPE_DEFAULT_PERMISSION="READ"
export DESCOPE_USERNAME_CLAIM="sub"  # or "email"
```

## Step 5: Use MLflow

Once configured, the plugin works automatically with any MLflow client:

```python
import mlflow

# Set tracking URI to your MLflow server
mlflow.set_tracking_uri("http://localhost:5000")

# Start a run - authentication and user context are automatic!
with mlflow.start_run():
    mlflow.log_param("alpha", 0.5)
    mlflow.log_metric("rmse", 0.8)
```

The plugin automatically:
- Adds authentication headers to all requests
- Injects user context headers (X-Descope-User-ID, X-Descope-Email, etc.)
- Tags runs with user information (descope.user_id, descope.email, etc.)

## What's Next?

### Verify Plugin is Loaded

```bash
# Check that the plugin is registered
python -c "
from importlib.metadata import entry_points
eps = entry_points(group='mlflow.request_auth_provider')
print([ep.name for ep in eps])
"
# Should include 'descope'
```

### Configure Admin Access

By default, all authenticated users have READ access. To grant admin privileges:

1. Set admin roles in your environment:

   ```bash
   export DESCOPE_ADMIN_ROLES="admin,mlflow-admin"
   ```

2. In Descope Console, go to **Authorization → Roles**
3. Create a role called `admin` or `mlflow-admin`
4. Assign this role to specific users

### Configure Permissions

```bash
# Default permission for all users (READ, EDIT, or MANAGE)
export DESCOPE_DEFAULT_PERMISSION="READ"

# Roles that get admin access (MANAGE permission)
export DESCOPE_ADMIN_ROLES="admin,mlflow-admin,superuser"
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

## Troubleshooting

### Plugin not loaded

**Problem**: Authentication doesn't work

**Solution**:

```bash
# Verify plugin is installed
pip list | grep mlflow-descope-auth

# Check entry points
python -c "
from importlib.metadata import entry_points
eps = entry_points(group='mlflow.request_auth_provider')
print([ep.name for ep in eps])
"

# Ensure MLFLOW_TRACKING_AUTH is set
echo $MLFLOW_TRACKING_AUTH  # Should be "descope"
```

### Authentication fails

**Problem**: Requests fail with authentication errors

**Solution**:

```bash
# Check environment variables
env | grep DESCOPE

# Verify tokens are valid
python -c "
from mlflow_descope_auth import get_descope_client
import os
client = get_descope_client()
result = client.validate_session(os.environ['DESCOPE_SESSION_TOKEN'])
print('✓ Token valid')
"
```

### "DESCOPE_PROJECT_ID is required" error

**Problem**: Plugin fails to initialize

**Solution**:

```bash
# Set the required environment variable
export DESCOPE_PROJECT_ID=P2XXXXX
export DESCOPE_SESSION_TOKEN="<your-token>"
```

## Need Help?

- **Documentation**: See [README.md](../README.md) for full documentation
- **Architecture**: See [ARCHITECTURE.md](../ARCHITECTURE.md) for technical details
- **Issues**: [GitHub Issues](https://github.com/descope/mlflow-descope-auth/issues)
- **Descope Docs**: [docs.descope.com](https://docs.descope.com/)

## Next Steps

- Read the [Configuration Reference](../README.md#configuration-reference)
- Learn about the [Plugin Architecture](../ARCHITECTURE.md)
- Check out the [Docker Examples](../examples/)

Happy MLflow-ing with Descope! 🚀
