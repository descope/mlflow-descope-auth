"""Basic usage example for MLflow Descope Auth plugin."""

import os

# Set environment variables (alternatively use .env file)
os.environ["DESCOPE_PROJECT_ID"] = "P2XXXXX"  # Replace with your project ID
os.environ["DESCOPE_FLOW_ID"] = "sign-up-or-in"
os.environ["DESCOPE_ADMIN_ROLES"] = "admin,mlflow-admin"

# Import and run the app
from mlflow_descope_auth import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    print("Starting MLflow with Descope authentication...")
    print("Visit http://localhost:5000 to login")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
    )
