# Quickstart Guide

Get MLflow running with Descope authentication in 5 minutes!

## Prerequisites

- Python 3.8 or higher installed
- pip package manager
- A Descope account (free at [descope.com](https://www.descope.com/))

## Step 1: Create a Descope Project

1. Go to [app.descope.com](https://app.descope.com/) and sign up/login
2. Click "Create New Project"
3. Give it a name (e.g., "MLflow Auth")
4. Copy your **Project ID** (starts with `P2`)

## Step 2: Configure Authentication Flow

1. In Descope Console, go to **Authentication → Flows**
2. You'll see a default `sign-up-or-in` flow - click to edit
3. Add your desired authentication methods:
   - **OAuth**: Google, GitHub, Microsoft, etc.
   - **Magic Link**: Passwordless email authentication
   - **OTP**: SMS or email one-time password
   - **Password**: Traditional username/password

4. Click **Publish** to save your flow

## Step 3: Install MLflow Descope Auth

```bash
pip install mlflow-descope-auth
```

## Step 4: Configure Environment

Create a `.env` file in your project directory:

```bash
# Required: Your Descope Project ID
DESCOPE_PROJECT_ID=P2XXXXX

# Optional: Flow ID (default is "sign-up-or-in")
DESCOPE_FLOW_ID=sign-up-or-in

# Optional: Where to redirect after login (default is "/")
DESCOPE_REDIRECT_URL=/
```

## Step 5: Run MLflow

```bash
mlflow server --app-name descope-auth --host 0.0.0.0 --port 5000
```

## Step 6: Test Authentication

1. Open your browser and go to `http://localhost:5000`
2. You'll be redirected to the Descope login page
3. Authenticate using one of your configured methods
4. You'll be redirected back to MLflow and logged in!

## What's Next?

### Configure Admin Access

By default, all authenticated users have READ access. To grant admin privileges:

1. In your `.env` file, add:
   ```bash
   DESCOPE_ADMIN_ROLES=admin,mlflow-admin
   ```

2. In Descope Console, go to **Authorization → Roles**
3. Create a role called `admin` or `mlflow-admin`
4. Assign this role to specific users

### Add More Authentication Methods

1. Go to Descope Console → **Authentication → Flows**
2. Edit your flow and add more methods (OAuth, SAML, etc.)
3. **No code changes needed!** Just publish the flow
4. Restart MLflow to see the changes

### Configure Permissions

Create custom permission mapping in your `.env`:

```bash
# Default permission for all users (READ, EDIT, or MANAGE)
DESCOPE_DEFAULT_PERMISSION=READ

# Roles that get admin access (MANAGE permission)
DESCOPE_ADMIN_ROLES=admin,mlflow-admin,superuser
```

### Production Deployment

For production, use a proper database:

```bash
mlflow server \
  --app-name descope-auth \
  --backend-store-uri postgresql://user:pass@localhost/mlflow \
  --default-artifact-root s3://my-bucket/mlflow \
  --host 0.0.0.0 \
  --port 5000
```

### Docker Deployment

Create `docker-compose.yml`:

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

## Troubleshooting

### Login page shows but authentication fails

**Problem**: Web component loads but authentication doesn't work

**Solution**: 
1. Check that your `DESCOPE_PROJECT_ID` is correct
2. Ensure your flow exists in Descope Console
3. Check browser console for errors
4. Verify your domain is whitelisted in Descope Console → **Project Settings → Authentication Hosts**

### Redirected to login in a loop

**Problem**: After successful authentication, you're redirected back to login

**Solution**:
1. Clear browser cookies
2. Check that cookies are enabled
3. If using HTTPS, ensure your redirect URL uses HTTPS too
4. Check browser console for cookie errors

### "DESCOPE_PROJECT_ID is required" error

**Problem**: MLflow fails to start

**Solution**:
```bash
# Make sure .env file exists in the same directory
cat .env

# Or set environment variable directly
export DESCOPE_PROJECT_ID=P2XXXXX
mlflow server --app-name descope-auth
```

### Port 5000 already in use

**Problem**: `Address already in use` error

**Solution**:
```bash
# Use a different port
mlflow server --app-name descope-auth --port 5001

# Or kill the process using port 5000
lsof -ti:5000 | xargs kill -9
```

## Need Help?

- **Documentation**: See [README.md](../README.md) for full documentation
- **Issues**: [GitHub Issues](https://github.com/descope/mlflow-descope-auth/issues)
- **Descope Docs**: [docs.descope.com](https://docs.descope.com/)

## Next Steps

- Read the [Configuration Guide](../README.md#configuration-reference)
- Learn about [Permission Mapping](../README.md#permission-mapping)
- Explore [Advanced Features](../README.md#advanced-features)
- Check out [Docker Examples](../examples/)

Happy MLflow-ing with Descope! 🚀
