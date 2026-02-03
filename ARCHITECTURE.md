# Architecture

## How MLflow Descope Auth Works

This plugin uses **MLflow's `mlflow.app` entry point** to add Descope authentication to the MLflow server. It provides server-side authentication with a browser-based login UI.

### Plugin Architecture

```txt
┌─────────────────────────────────────────┐
│           Browser                       │
│  (User visits MLflow UI)                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         MLflow Server                   │
│  (with Descope plugin loaded)           │
├─────────────────────────────────────────┤
│  before_request hook                    │  ← Validates session cookie
│  - Check DS/DSR cookies                 │
│  - Redirect to /auth/login if invalid   │
│  - Set user context in Flask g          │
├─────────────────────────────────────────┤
│  after_request hook                     │  ← Updates cookie if refreshed
│  - Check if token was refreshed         │
│  - Update DS cookie with new token      │
├─────────────────────────────────────────┤
│  Auth Routes                            │
│  - /auth/login   (Descope Web Component)│
│  - /auth/logout  (Clear cookies)        │
│  - /auth/user    (Current user info)    │
│  - /health       (Health check)         │
└─────────────────────────────────────────┘
```

### Entry Point

The plugin registers one MLflow entry point in `pyproject.toml`:

```toml
[project.entry-points."mlflow.app"]
descope = "mlflow_descope_auth.server:create_app"
```

### Authentication Flow

1. **User visits MLflow UI**

   ```txt
   Browser → GET / 
        → before_request hook triggered
        → No valid session cookie?
        → Redirect to /auth/login
   ```

2. **Login with Descope**

   ```txt
   Browser → /auth/login
        → Descope Web Component loads
        → User authenticates via Descope flow
        → On success: JavaScript sets cookies (DS, DSR)
        → Redirect to MLflow UI
   ```

3. **Authenticated Access**

   ```txt
   Browser → GET / (with DS cookie)
        → before_request hook validates session
        → Sets user info in Flask g
        → MLflow UI loads normally
   ```

4. **Token Refresh**

   ```txt
   Request comes in with expired session token
        → validate_and_refresh_session() refreshes token
        → after_request hook updates DS cookie
        → User continues seamlessly
   ```

### Key Components

#### 1. `server.py` - Flask App Factory

```python
def create_app(app: Flask = None) -> Flask:
    """MLflow app factory entry point."""
    if app is None:
        from mlflow.server import app as mlflow_app
        app = mlflow_app
    
    register_auth_routes(app)
    app.before_request(_before_request)
    app.after_request(_after_request)
    return app
```

#### 2. `auth_routes.py` - Authentication Endpoints

- `/auth/login` - Login page with Descope Web Component
- `/auth/logout` - Clears cookies, redirects to login
- `/auth/user` - Returns current user info as JSON
- `/health` - Health check endpoint

#### 3. `client.py` - Descope SDK Wrapper

- Session validation with Descope API
- Token refresh handling
- User claims extraction from validated tokens

#### 4. `config.py` - Configuration

- Environment variable management
- Cookie settings
- Default values and validation

### Why This Architecture?

1. **Server-Side Security**
   - Tokens stored in HttpOnly cookies (not accessible to JavaScript)
   - Server validates every request
   - Automatic token refresh

2. **Standard MLflow Integration**
   - Uses official `mlflow.app` entry point
   - Works with stock MLflow server
   - No custom server deployment needed

3. **Minimal Dependencies**
   - Only `descope` SDK required
   - Uses Flask (already part of MLflow)
   - No additional frameworks

4. **Simple Configuration**
   - Just environment variables
   - No config files needed
   - Works in any environment (local, Docker, K8s)

### Cookie Details

| Cookie | Purpose | HttpOnly | Secure |
|--------|---------|----------|--------|
| `DS`   | Session token | Yes | Configurable |
| `DSR`  | Refresh token | Yes | Configurable |

Set `DESCOPE_COOKIE_SECURE=true` in production (HTTPS).

### Security Considerations

- Cookies are HttpOnly (not accessible to JavaScript XSS attacks)
- Session tokens are validated on every request
- Refresh tokens enable seamless token renewal
- No tokens stored in browser localStorage/sessionStorage
