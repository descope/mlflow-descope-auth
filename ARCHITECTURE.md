# Architecture

## How MLflow Descope Auth Works

This plugin is an **MLflow app plugin** that wraps the MLflow Flask application with Descope authentication.

### Component Stack

```txt
┌─────────────────────────────────────────┐
│         FastAPI Application             │  <- Entry point
│  (mlflow_descope_auth.app:app)          │
├─────────────────────────────────────────┤
│  Authentication Middleware              │  <- Validates Descope sessions
│  - Checks cookies (DS, DSR)             │
│  - Validates with Descope SDK           │
│  - Auto-refreshes expired tokens        │
│  - Sets user info in request.state      │
├─────────────────────────────────────────┤
│  Auth Routes (/auth/*)                  │  <- Login, logout, health
│  - /auth/login (Descope web component)  │
│  - /auth/logout                         │
│  - /auth/user                           │
│  - /auth/health                         │
├─────────────────────────────────────────┤
│  AuthAwareWSGIMiddleware                │  <- Bridges FastAPI ↔ Flask
│  - Extracts auth from ASGI scope        │
│  - Injects into WSGI environ            │
│  - Sets REMOTE_USER for MLflow          │
├─────────────────────────────────────────┤
│  MLflow Flask Application               │  <- The actual MLflow server
│  (from mlflow.server import app)        │
└─────────────────────────────────────────┘
```

### Authentication Flow

1. **Unauthenticated Request**

   ```python
   User → FastAPI → AuthenticationMiddleware
        → No session found
        → RedirectResponse("/auth/login")
   ```

2. **Login Flow**

   ```txt
   User → /auth/login
        → HTML with <descope-wc> component
        → User authenticates (OAuth/SAML/etc)
        → Web component gets JWT tokens
        → JavaScript sets cookies (DS, DSR)
        → Redirect to "/"
   ```

3. **Authenticated Request**

   ```txt
   User → FastAPI → AuthenticationMiddleware
        → Extract tokens from cookies
        → Validate with Descope SDK
        → Set user info in request.state
        → Continue to next middleware
        → AuthAwareWSGIMiddleware
        → Inject auth into WSGI environ
        → MLflow Flask app
        → MLflow processes request with user context
   ```

### Key Components

#### 1. `app.py` - Application Factory

- Creates FastAPI app
- Adds authentication middleware
- Registers auth routes
- **Mounts MLflow Flask app at "/"**

#### 2. `middleware.py` - Session Validation

- Extracts session tokens from cookies
- Validates with Descope SDK
- Auto-refreshes expired tokens
- Attaches user info to request

#### 3. `wsgi_middleware.py` - ASGI ↔ WSGI Bridge

- Extracts auth from FastAPI request
- Injects into Flask's WSGI environ
- Sets `REMOTE_USER` for MLflow compatibility

#### 4. `auth_routes.py` - Authentication Endpoints

- `/auth/login` - Descope web component
- `/auth/logout` - Clear session cookies
- `/auth/user` - Get current user info
- `/auth/health` - Health check

#### 5. `client.py` - Descope SDK Wrapper

- Session validation
- Token refresh
- User info extraction
- Role/permission checking

### Why This Architecture?

1. **Separation of Concerns**
   - FastAPI handles auth
   - MLflow handles ML operations
   - Clean middleware layer bridges them

2. **No MLflow Modifications**
   - Uses MLflow as-is via `from mlflow.server import app`
   - Auth is completely external
   - Easy to upgrade MLflow versions

3. **Standard WSGI Integration**
   - Uses `REMOTE_USER` environ variable
   - Compatible with MLflow's auth expectations
   - Works with existing MLflow features

4. **Plugin System Integration**
   - Entry point: `mlflow.app`
   - Usage: `mlflow server --app-name descope-auth`
   - MLflow automatically discovers and loads it

### Dependencies

**Critical:** This plugin requires MLflow to be installed!

```toml
dependencies = [
    "mlflow>=2.0.0",      # ← Required! We import from mlflow.server
    "descope>=0.9.0",     # Descope SDK
    "fastapi>=0.100.0",   # FastAPI framework
    "asgiref>=3.7.0",     # ASGI ↔ WSGI adapter
    # ... other deps
]
```

Without MLflow, the plugin cannot function as it wraps MLflow's Flask app.

### Comparison: Descope vs OIDC Plugin

| Aspect        | mlflow-oidc-auth                | mlflow-descope-auth                 |
| ------------- | ------------------------------- | ----------------------------------- |
| Auth Provider | Generic OIDC                    | Descope (OIDC + more)               |
| Configuration | Discovery URL, Client ID/Secret | Project ID, Flow ID                 |
| Auth Methods  | Depends on OIDC provider        | Any (configured in Descope Console) |
| Session Mgmt  | OIDC tokens                     | Descope SDK validation              |
| Integration   | Flask hooks + WSGI middleware   | Same pattern                        |
| Complexity    | ~2000 LOC                       | ~500 LOC (Flow-based)               |

Both follow the same architectural pattern of wrapping MLflow's Flask app.
