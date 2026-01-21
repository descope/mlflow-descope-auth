# MLflow Descope Authentication Plugin - Implementation Plan

## Overview

A Python plugin that integrates **Descope Flow-based authentication** into MLflow. Uses Descope's web component pattern where authentication flows are configured in Descope Console, not hardcoded in the application.

**Key Architecture Decision**: Flow-based pattern (like django-descope and flask examples) - authentication methods are configured in Descope Console, the plugin just embeds the flow.

---

## 1. Architecture

### Flow-Based Authentication Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Request Flow                            │
└─────────────────────────────────────────────────────────────────┘

1. User visits MLflow UI
2. Redirect to /auth/login (HTML page with <descope-wc>)
3. Descope Web Component loads flow from console
4. User completes authentication (whatever methods configured)
5. Web component emits 'success' event with JWT tokens
6. JavaScript stores tokens in cookies (DS, DSR)
7. Redirect to MLflow UI
8. Middleware validates session on each request
```

### Component Structure

```
mlflow-descope-auth/
├── mlflow_descope_auth/
│   ├── __init__.py
│   ├── app.py                    # FastAPI app factory (wraps MLflow)
│   ├── config.py                 # Configuration (PROJECT_ID, FLOW_ID)
│   ├── client.py                 # Descope SDK wrapper
│   ├── auth_routes.py            # /login, /callback, /logout
│   ├── middleware.py             # Session validation middleware
│   ├── store.py                  # MLflow user/permission adapter
│   └── templates/
│       └── login.html            # Login page with <descope-wc>
```

---

## 2. Core Components

### 2.1 Login Route (`auth_routes.py`)

Serves HTML page with Descope web component:

```python
@router.get("/auth/login")
async def login(request: Request):
    """Render login page with Descope Flow web component."""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "project_id": config.DESCOPE_PROJECT_ID,
        "flow_id": config.DESCOPE_FLOW_ID,
        "redirect_url": config.DESCOPE_REDIRECT_URL,
    })
```

### 2.2 Login Template (`templates/login.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/@descope/web-component@{version}/dist/index.js"></script>
</head>
<body>
    <descope-wc 
        id="descope-wc"
        project-id="{{ project_id }}"
        flow-id="{{ flow_id }}">
    </descope-wc>
    
    <script>
        const descopeWc = document.getElementById('descope-wc');
        descopeWc.addEventListener('success', (e) => {
            // Set cookies with JWT tokens
            document.cookie = `DS=${e.detail.sessionJwt}; path=/; secure; samesite=strict`;
            document.cookie = `DSR=${e.detail.refreshJwt}; path=/; secure; samesite=strict`;
            
            // Redirect to MLflow
            window.location.href = "{{ redirect_url }}";
        });
    </script>
</body>
</html>
```

### 2.3 Session Validation Middleware (`middleware.py`)

```python
async def dispatch(self, request: Request, call_next):
    """Validate Descope session on each request."""
    
    # Skip auth for public routes
    if self._is_public_route(request.url.path):
        return await call_next(request)
    
    # Get tokens from cookies
    session_token = request.cookies.get("DS")
    refresh_token = request.cookies.get("DSR")
    
    if not session_token:
        return RedirectResponse(url="/auth/login")
    
    # Validate with Descope SDK
    try:
        jwt_response = descope_client.validate_and_refresh_session(
            session_token, refresh_token
        )
        
        # Extract user info from JWT
        username = jwt_response["sessionToken"]["sub"]  # or "email"
        roles = jwt_response["sessionToken"].get("roles", [])
        permissions = jwt_response["sessionToken"].get("permissions", [])
        
        # Attach to request
        request.state.username = username
        request.state.roles = roles
        request.state.permissions = permissions
        request.state.is_admin = self._check_admin(roles)
        
        response = await call_next(request)
        
        # Update cookies if token was refreshed
        if jwt_response.get("cookieData"):
            response.set_cookie(
                "DS",
                jwt_response["sessionToken"]["jwt"],
                secure=True,
                httponly=True,
                samesite="strict"
            )
        
        return response
        
    except AuthException:
        return RedirectResponse(url="/auth/login")
```

### 2.4 Descope Client Wrapper (`client.py`)

```python
class DescopeClientWrapper:
    """Wrapper around Descope SDK for MLflow integration."""
    
    def __init__(self, project_id: str, management_key: str = None):
        self.client = DescopeClient(
            project_id=project_id,
            management_key=management_key
        )
    
    def validate_session(self, session_token: str, refresh_token: str):
        """Validate and refresh session."""
        return self.client.validate_and_refresh_session(
            session_token, refresh_token
        )
    
    def get_user_info(self, refresh_token: str):
        """Get user details from Descope."""
        return self.client.me(refresh_token)
    
    def validate_permissions(self, jwt_response: dict, permissions: list[str]):
        """Check if user has required permissions."""
        return self.client.validate_permissions(jwt_response, permissions)
    
    def validate_roles(self, jwt_response: dict, roles: list[str]):
        """Check if user has required roles."""
        return self.client.validate_roles(jwt_response, roles)
```

### 2.5 Configuration (`config.py`)

```python
@dataclass
class Config:
    # Required
    DESCOPE_PROJECT_ID: str
    
    # Optional
    DESCOPE_MANAGEMENT_KEY: str = None
    DESCOPE_FLOW_ID: str = "sign-up-or-in"
    DESCOPE_REDIRECT_URL: str = "/"
    DESCOPE_WEB_COMPONENT_VERSION: str = "3.54.0"
    
    # MLflow integration
    MLFLOW_BACKEND_STORE_URI: str = "sqlite:///mlflow.db"
    MLFLOW_ARTIFACT_ROOT: str = "./mlartifacts"
    
    # Permission mapping
    ADMIN_ROLES: list[str] = field(default_factory=lambda: ["admin", "mlflow-admin"])
    DEFAULT_PERMISSION: str = "READ"
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            DESCOPE_PROJECT_ID=os.getenv("DESCOPE_PROJECT_ID"),
            DESCOPE_MANAGEMENT_KEY=os.getenv("DESCOPE_MANAGEMENT_KEY"),
            DESCOPE_FLOW_ID=os.getenv("DESCOPE_FLOW_ID", "sign-up-or-in"),
            # ... etc
        )
```

### 2.6 FastAPI App Factory (`app.py`)

```python
def create_app():
    """Create FastAPI app with Descope authentication."""
    
    # Load configuration
    config = Config.from_env()
    
    # Initialize Descope client
    descope_client = DescopeClientWrapper(
        project_id=config.DESCOPE_PROJECT_ID,
        management_key=config.DESCOPE_MANAGEMENT_KEY
    )
    
    # Create FastAPI app
    app = FastAPI(title="MLflow with Descope Auth")
    
    # Add middleware
    app.add_middleware(SessionValidationMiddleware, descope_client=descope_client)
    
    # Include auth routes
    app.include_router(auth_router)
    
    # Mount MLflow Flask app
    mlflow_app = _get_mlflow_app()
    app.mount("/", WSGIMiddleware(mlflow_app))
    
    return app

# Entry point for MLflow plugin
app = create_app()
```

### 2.7 User Store Adapter (`store.py`)

```python
class DescopeUserStore:
    """Adapter between Descope and MLflow user management."""
    
    def __init__(self, descope_client: DescopeClientWrapper):
        self.descope = descope_client
        # Initialize SQLAlchemy for local user cache (optional)
    
    def get_or_create_user(self, jwt_response: dict):
        """Get or create user from JWT response."""
        token = jwt_response["sessionToken"]
        username = token["sub"]  # or token["email"]
        display_name = token.get("name", username)
        roles = token.get("roles", [])
        
        is_admin = any(role in config.ADMIN_ROLES for role in roles)
        
        # Create/update user in MLflow database
        # (This depends on MLflow's auth store interface)
        return User(
            username=username,
            display_name=display_name,
            is_admin=is_admin,
            roles=roles
        )
    
    def map_permissions(self, roles: list[str]) -> str:
        """Map Descope roles to MLflow permission level."""
        if any(role in config.ADMIN_ROLES for role in roles):
            return "MANAGE"
        # Add more mapping logic
        return config.DEFAULT_PERMISSION
```

---

## 3. Implementation Steps

### Phase 1: Project Setup (Day 1)

- [ ] Initialize repository with structure
- [ ] Create `pyproject.toml` with dependencies:
  - `mlflow >= 2.0.0`
  - `descope >= 0.9.0`
  - `fastapi >= 0.100.0`
  - `jinja2 >= 3.1.0`
- [ ] Set up development environment
- [ ] Create `.env.example` with required config

### Phase 2: Core Authentication (Days 2-3)

- [ ] Implement `config.py` with Config class
- [ ] Implement `client.py` with DescopeClientWrapper
- [ ] Create `templates/login.html` with web component
- [ ] Implement `auth_routes.py`:
  - [ ] GET `/auth/login` - Render login page
  - [ ] GET `/auth/logout` - Clear cookies and logout
  - [ ] GET `/health` - Health check endpoint

### Phase 3: Session Validation (Days 4-5)

- [ ] Implement `middleware.py` with SessionValidationMiddleware
- [ ] Add token validation logic
- [ ] Add automatic token refresh
- [ ] Implement user context attachment
- [ ] Handle authentication errors

### Phase 4: MLflow Integration (Days 6-7)

- [ ] Implement `store.py` with user management
- [ ] Implement `app.py` with FastAPI app factory
- [ ] Mount MLflow Flask app
- [ ] Configure entry point in `pyproject.toml`:
  ```toml
  [project.entry-points."mlflow.app"]
  descope-auth = "mlflow_descope_auth.app:app"
  ```
- [ ] Test with `mlflow server --app-name descope-auth`

### Phase 5: Testing (Days 8-9)

- [ ] Unit tests for configuration loading
- [ ] Unit tests for client wrapper (mocked)
- [ ] Integration tests for auth flow
- [ ] End-to-end test with real Descope project
- [ ] Test permission mapping

### Phase 6: Documentation (Day 10)

- [ ] README with setup instructions
- [ ] Configuration guide
- [ ] Quickstart tutorial
- [ ] Example `.env` file
- [ ] Troubleshooting guide

---

## 4. Configuration

### Environment Variables

```bash
# Required
DESCOPE_PROJECT_ID=P2XXXXX

# Optional
DESCOPE_MANAGEMENT_KEY=K2XXXXX
DESCOPE_FLOW_ID=sign-up-or-in
DESCOPE_REDIRECT_URL=/

# MLflow
MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow.db
MLFLOW_ARTIFACT_ROOT=./mlartifacts

# Permission Mapping
DESCOPE_ADMIN_ROLES=admin,mlflow-admin
DESCOPE_DEFAULT_PERMISSION=READ
```

### Usage

```bash
# Install plugin
pip install mlflow-descope-auth

# Set environment variables
export DESCOPE_PROJECT_ID=P2XXXXX
export DESCOPE_FLOW_ID=sign-up-or-in

# Run MLflow with Descope auth
mlflow server --app-name descope-auth --host 0.0.0.0 --port 5000
```

---

## 5. Key Differences from Previous Plan

| Previous (❌)                               | Flow-Based (✅)                                 |
| ------------------------------------------- | ----------------------------------------------- |
| Hardcode OAuth/SAML/MagicLink methods       | Single flow ID, configured in Descope Console   |
| Complex route handling for each auth method | Simple: login page + callback                   |
| Manual redirect URL construction            | Web component handles everything                |
| Multiple callback endpoints                 | One success event handler                       |
| ~2000 lines of code                         | ~500 lines of code                              |
| 6 weeks implementation                      | 1.5-2 weeks implementation                      |

---

## 6. Testing Strategy

### Unit Tests

```python
# test_client.py
def test_validate_session_success(mock_descope):
    client = DescopeClientWrapper(project_id="test")
    result = client.validate_session("token", "refresh")
    assert result["sessionToken"]["sub"] == "user@example.com"

# test_middleware.py
async def test_middleware_validates_session(mock_request):
    middleware = SessionValidationMiddleware(descope_client)
    response = await middleware.dispatch(mock_request, mock_call_next)
    assert mock_request.state.username == "user@example.com"
```

### Integration Tests

```python
# test_integration.py
def test_full_auth_flow(test_client):
    # 1. Visit login page
    response = test_client.get("/auth/login")
    assert response.status_code == 200
    assert "descope-wc" in response.text
    
    # 2. Simulate successful auth (mock tokens)
    test_client.cookies.set("DS", "mock_session_token")
    test_client.cookies.set("DSR", "mock_refresh_token")
    
    # 3. Access protected route
    response = test_client.get("/")
    assert response.status_code == 200
```

---

## 7. Deployment Example

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

---

## 8. Success Criteria

### MVP (v0.1.0)
- [x] Flow-based authentication working
- [x] Session validation middleware
- [x] Token refresh automatic
- [x] Basic user management
- [x] Configuration via environment variables
- [x] Can run with `mlflow server --app-name descope-auth`
- [x] Documentation with quickstart

### Future Enhancements (v0.2.0+)
- [ ] Multi-tenant support
- [ ] Advanced permission mapping
- [ ] User sync from Descope
- [ ] Admin UI for user management
- [ ] Audit logging
- [ ] SSO-specific flows (e.g., separate admin flow)

---

## 9. References

- **Flask Example**: [python-sdk/samples/flask_authentication.py](https://github.com/descope/python-sdk/blob/6ca4fab2fef0623a4be4b5c7ca104de3c17a1c40/samples/flask_authentication.py)
- **Django Integration**: [django-descope](https://github.com/descope/django-descope/blob/315b3060072f6a42fc692e5d785baaf2542afedc/)
- **MLflow OIDC Plugin**: [mlflow-oidc-auth](https://github.com/mlflow-oidc/mlflow-oidc-auth)
- **Descope Web Component**: https://docs.descope.com/build/guides/client_sdks/web_comp/

---

## 10. Timeline

**Total: 10 days (2 weeks)**

| Phase | Days | Deliverable |
|-------|------|-------------|
| Project Setup | 1 | Repository initialized |
| Core Auth | 2 | Login flow working |
| Session Validation | 2 | Middleware validates sessions |
| MLflow Integration | 2 | Plugin installable and runnable |
| Testing | 2 | Tests passing, coverage >80% |
| Documentation | 1 | README, quickstart, examples |

**Ready to ship v0.1.0 in 2 weeks!**
