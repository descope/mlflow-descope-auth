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

## Step 2: Install MLflow Descope Auth

```bash
pip install mlflow-descope-auth
```

## Step 3: Start MLflow with Descope Authentication

```bash
export DESCOPE_PROJECT_ID="P2XXXXX"
mlflow server --app-name descope --host 0.0.0.0 --port 5000
```

## Step 4: Access MLflow

1. Open your browser: `http://localhost:5000`
2. You'll be redirected to the Descope login page
3. Sign in with your Descope account
4. After authentication, you'll be redirected to the MLflow UI

That's it! You now have a secure MLflow server with Descope authentication.

## Alternative: Client-Side Mode (For CLI/Scripts)

If you need programmatic access without browser login, use environment variable tokens:

### Get Authentication Tokens

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

### Configure Environment

```bash
export DESCOPE_PROJECT_ID="P2XXXXX"
export DESCOPE_SESSION_TOKEN="<your-session-token>"
export MLFLOW_TRACKING_AUTH=descope
```

### Use MLflow

```python
import mlflow

mlflow.set_tracking_uri("http://localhost:5000")

with mlflow.start_run():
    mlflow.log_param("alpha", 0.5)
    mlflow.log_metric("rmse", 0.8)
```

## What's Next?

### Verify Plugin is Loaded

```bash
python -c "
from importlib.metadata import entry_points
eps = entry_points(group='mlflow.app')
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

### Automatic Run Tagging

The plugin automatically adds these tags to all runs:

- `descope.user_id` - User's Descope ID
- `descope.username` - Username
- `descope.email` - User's email
- `descope.roles` - Comma-separated list of roles

### Logout

Visit `/auth/logout` to clear your session and redirect to login.

## Troubleshooting

### Server won't start

```bash
# Verify plugin is installed
pip list | grep mlflow-descope-auth

# Check DESCOPE_PROJECT_ID is set
echo $DESCOPE_PROJECT_ID
```

### Login page doesn't appear

Make sure you're using `--app-name descope`:
```bash
mlflow server --app-name descope --port 5000
```

### Authentication fails

```bash
# Check environment variables
env | grep DESCOPE
```

## Need Help?

- **Documentation**: See [README.md](../README.md) for full documentation
- **Issues**: [GitHub Issues](https://github.com/descope/mlflow-descope-auth/issues)
- **Descope Docs**: [docs.descope.com](https://docs.descope.com/)

Happy MLflow-ing with Descope!
