"""Basic usage example for MLflow Descope Auth plugin.

The recommended way to run MLflow with Descope authentication is:

    export DESCOPE_PROJECT_ID="P2XXXXX"
    mlflow server --app-name descope --host 0.0.0.0 --port 5000

This example shows how to programmatically create and run the app.
"""

import os

os.environ["DESCOPE_PROJECT_ID"] = "P2XXXXX"  # Replace with your project ID

from mlflow_descope_auth import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting MLflow with Descope authentication...")
    print("Visit http://localhost:5000 to login")
    app.run(host="0.0.0.0", port=5000)
