"""Example of custom configuration for MLflow Descope Auth.

The recommended way to run MLflow with Descope authentication is:

    export DESCOPE_PROJECT_ID="P2XXXXX"
    export DESCOPE_ADMIN_ROLES="admin,superuser"
    mlflow server --app-name descope --host 0.0.0.0 --port 5000

This example shows how to programmatically configure and run the app.
"""

import os

os.environ["DESCOPE_PROJECT_ID"] = "P2XXXXX"  # Replace with your project ID

from mlflow_descope_auth import Config, create_app, set_config

config = Config(
    DESCOPE_PROJECT_ID="P2XXXXX",
    DESCOPE_FLOW_ID="sign-up-or-in",
    DESCOPE_REDIRECT_URL="/experiments",
    ADMIN_ROLES=["admin", "superuser", "mlflow-admin"],
    DEFAULT_PERMISSION="EDIT",
    USERNAME_CLAIM="email",
)

set_config(config)

app = create_app()

if __name__ == "__main__":
    print("Starting MLflow with custom Descope configuration...")
    print(f"Admin roles: {config.ADMIN_ROLES}")
    print(f"Default permission: {config.DEFAULT_PERMISSION}")
    app.run(host="0.0.0.0", port=5000)
