"""Example of custom configuration for MLflow Descope Auth."""

from mlflow_descope_auth import Config, create_app, set_config

# Create custom configuration
config = Config(
    DESCOPE_PROJECT_ID="P2XXXXX",  # Replace with your project ID
    DESCOPE_FLOW_ID="sign-up-or-in",
    DESCOPE_REDIRECT_URL="/experiments",  # Custom redirect
    ADMIN_ROLES=["admin", "superuser", "mlflow-admin"],  # Custom admin roles
    DEFAULT_PERMISSION="EDIT",  # More permissive default (READ, EDIT, or MANAGE)
    USERNAME_CLAIM="email",  # Use email as username instead of 'sub'
)

# Set the custom configuration
set_config(config)

# Create the app with custom config
app = create_app()

if __name__ == "__main__":
    import uvicorn

    print("Starting MLflow with custom Descope configuration...")
    print(f"Admin roles: {config.ADMIN_ROLES}")
    print(f"Default permission: {config.DEFAULT_PERMISSION}")
    print(f"Redirect URL: {config.DESCOPE_REDIRECT_URL}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
    )
