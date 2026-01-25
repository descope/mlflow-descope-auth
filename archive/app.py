"""FastAPI application factory for MLflow with Descope authentication."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import MLflow Flask app
from mlflow.server import app as mlflow_flask_app

from .auth_routes import router as auth_router
from .client import get_descope_client
from .config import get_config
from .middleware import AuthenticationMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This function:
    1. Initializes the Descope client
    2. Creates a FastAPI application
    3. Adds authentication middleware
    4. Registers authentication routes
    5. Configures CORS if needed

    Returns:
        FastAPI: The configured FastAPI application.
    """
    # Load configuration
    config = get_config()

    logger.info("Initializing MLflow Descope Auth plugin")
    logger.info(f"Descope Project ID: {config.DESCOPE_PROJECT_ID}")
    logger.info(f"Flow ID: {config.DESCOPE_FLOW_ID}")

    # Initialize Descope client
    descope_client = get_descope_client()

    # Create FastAPI app
    app = FastAPI(
        title="MLflow with Descope Authentication",
        description="MLflow Tracking Server with Descope Flow-based authentication",
        version="0.1.0",
        docs_url="/docs" if config.DESCOPE_PROJECT_ID else None,  # Disable docs in prod
    )

    # Add CORS middleware (configure as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add authentication middleware
    app.add_middleware(AuthenticationMiddleware, descope_client=descope_client)

    # Include authentication routes
    app.include_router(auth_router)

    # Mount MLflow Flask app at root with auth-aware middleware
    from .wsgi_middleware import AuthAwareWSGIMiddleware

    app.mount("/", AuthAwareWSGIMiddleware(mlflow_flask_app))
    logger.info("Mounted MLflow Flask app at / with auth-aware WSGI middleware")

    logger.info("MLflow Descope Auth plugin initialized successfully")

    return app


# Create the app instance for MLflow plugin entry point
app = create_app()


# This function is called by MLflow when using: mlflow server --app-name descope-auth
def get_app():
    """Get the FastAPI application instance.

    This is the entry point for MLflow plugin system.

    Returns:
        FastAPI: The configured application.
    """
    return app
