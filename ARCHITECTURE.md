# Architecture

## How MLflow Descope Auth Works

This plugin uses **MLflow's standard plugin system** to add Descope authentication to MLflow clients. It does NOT wrap or modify the MLflow server - it extends the client-side behavior.

### Plugin Architecture

```txt
┌─────────────────────────────────────────┐
│           MLflow Client                 │
│  (mlflow.set_tracking_uri(...))         │
├─────────────────────────────────────────┤
│  DescopeAuthProvider                    │  ← Adds Bearer token to requests
│  (mlflow.request_auth_provider)         │
├─────────────────────────────────────────┤
│  DescopeHeaderProvider                  │  ← Injects user context headers
│  (mlflow.request_header_provider)       │
├─────────────────────────────────────────┤
│  DescopeContextProvider                 │  ← Auto-tags runs with user info
│  (mlflow.run_context_provider)          │
├─────────────────────────────────────────┤
│           HTTP Request                  │
│  Authorization: Bearer <descope-token>  │
│  X-Descope-User-ID: ...                 │
│  X-Descope-Email: ...                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         MLflow Server                   │  ← Unmodified, standard MLflow
│  (receives authenticated requests)      │
└─────────────────────────────────────────┘
```

### Entry Points

The plugin registers three MLflow entry points in `pyproject.toml`:

```toml
[project.entry-points."mlflow.request_auth_provider"]
descope = "mlflow_descope_auth.auth_provider:DescopeAuthProvider"

[project.entry-points."mlflow.request_header_provider"]
descope = "mlflow_descope_auth.header_provider:DescopeHeaderProvider"

[project.entry-points."mlflow.run_context_provider"]
descope = "mlflow_descope_auth.context_provider:DescopeContextProvider"
```

### Authentication Flow

1. **Plugin Activation**

   ```bash
   export MLFLOW_TRACKING_AUTH=descope
   ```

   MLflow discovers and loads the `descope` auth provider.

2. **Token Injection**

   ```txt
   Client calls mlflow.log_metric(...)
        → DescopeAuthProvider.get_auth() called
        → Returns callable that adds Authorization header
        → Request sent with: Authorization: Bearer <DESCOPE_SESSION_TOKEN>
   ```

3. **Header Injection**

   ```txt
   DescopeHeaderProvider.request_headers() called
        → Decodes JWT token (without validation)
        → Extracts user info (sub, email, roles, etc.)
        → Returns headers: X-Descope-User-ID, X-Descope-Email, etc.
   ```

4. **Run Tagging**

   ```txt
   mlflow.start_run() called
        → DescopeContextProvider.in_context() → True (if token present)
        → DescopeContextProvider.tags() called
        → Returns tags: descope.user_id, descope.email, etc.
        → Tags automatically added to run
   ```

### Key Components

#### 1. `auth_provider.py` - Request Authentication

```python
class DescopeAuthProvider(RequestAuthProvider):
    def get_name(self) -> str:
        return "descope"
    
    def get_auth(self) -> Callable:
        # Returns function that adds Bearer token to requests
        token = os.environ.get("DESCOPE_SESSION_TOKEN")
        return lambda: ("Bearer", token)
```

#### 2. `header_provider.py` - Request Headers

```python
class DescopeHeaderProvider(RequestHeaderProvider):
    def in_context(self) -> bool:
        return bool(os.environ.get("DESCOPE_SESSION_TOKEN"))
    
    def request_headers(self) -> Dict[str, str]:
        # Decode JWT and return user info as headers
        return {
            "X-Descope-User-ID": user_id,
            "X-Descope-Email": email,
            # ...
        }
```

#### 3. `context_provider.py` - Run Tagging

```python
class DescopeContextProvider(RunContextProvider):
    def in_context(self) -> bool:
        return bool(os.environ.get("DESCOPE_SESSION_TOKEN"))
    
    def tags(self) -> Dict[str, str]:
        # Return tags to add to every run
        return {
            "descope.user_id": user_id,
            "descope.email": email,
            # ...
        }
```

#### 4. `client.py` - Descope SDK Wrapper

- Session validation with Descope API
- Token refresh handling
- User info extraction from validated tokens

#### 5. `config.py` - Configuration

- Environment variable management
- Default values and validation

### Why This Architecture?

1. **Non-Invasive**
   - Server runs unmodified
   - All logic is client-side
   - No middleware, no wrapping

2. **Standard MLflow Integration**
   - Uses official plugin entry points
   - Works with any MLflow server
   - Future-proof against MLflow updates

3. **Minimal Dependencies**
   - Only `descope` SDK required
   - No FastAPI, no ASGI/WSGI complexity

4. **Simple Configuration**
   - Just environment variables
   - No config files needed
   - Works in any environment (local, Docker, K8s)

### Comparison with Other Approaches

| Aspect              | Simple Plugin (This)      | Server Wrapper Approach     |
| ------------------- | ------------------------- | --------------------------- |
| **Where it runs**   | Client-side               | Server-side                 |
| **Server changes**  | None                      | Wraps entire server         |
| **Complexity**      | ~300 LOC                  | ~2000+ LOC                  |
| **Dependencies**    | descope SDK only          | FastAPI, ASGI, middleware   |
| **MLflow version**  | Any                       | May break on updates        |
| **Deployment**      | pip install               | Custom server setup         |

### Security Considerations

- Tokens are passed via environment variables (not committed to code)
- JWT decoding in header/context providers is for extracting claims only
- Actual token validation should happen server-side
- For server-side validation, use MLflow's built-in auth or a reverse proxy
