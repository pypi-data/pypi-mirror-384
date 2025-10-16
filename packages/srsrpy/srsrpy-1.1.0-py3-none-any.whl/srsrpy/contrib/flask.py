"""Flask extension for automatic service registry integration.

Usage:
    from flask import Flask
    from srsrpy.contrib.flask import FlaskServiceRegistry

    app = Flask(__name__)
    FlaskServiceRegistry(app)

Or with application factory pattern:
    registry = FlaskServiceRegistry()

    def create_app():
        app = Flask(__name__)
        registry.init_app(app)
        return app

Configuration is read from environment variables (via from_env()):
    - SRSR_SERVICE_NAME: Service name (required)
    - SRSR_REGISTRY_URL: Registry address (optional)
    - SRSR_SERVICE_ADDRESS: Service address (optional)
    - SRSR_SERVICE_PORT: Service port (optional)
    - SRSR_HEARTBEAT_INTERVAL: Heartbeat interval in seconds (optional)
"""

import os

try:
    from flask import Flask
except ImportError:
    raise ImportError(
        "Flask is required to use srsrpy.contrib.flask. "
        "Install it with: pip install srsrpy[flask]"
    )

from srsrpy.srsrpy import ServiceRegistryClient


class FlaskServiceRegistry:
    """Flask extension for automatic service registry integration.

    Automatically registers the Flask application with the service registry
    on startup and deregisters on shutdown.
    """

    def __init__(self, app=None):
        """Initialize the extension.

        Args:
            app: Flask application instance (optional). If provided,
                 init_app() is called automatically.
        """
        self.client = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the extension with a Flask application.

        Args:
            app: Flask application instance

        If SRSR_SERVICE_NAME environment variable is not set,
        this method does nothing (allows graceful degradation).
        """
        if not isinstance(app, Flask):
            raise TypeError("app must be a Flask application instance")

        # Gracefully skip if not configured
        if not os.getenv('SRSR_SERVICE_NAME'):
            app.logger.debug(
                "SRSR_SERVICE_NAME not set, skipping service registry"
            )
            return

        # Create client from environment variables
        try:
            self.client = ServiceRegistryClient.from_env()
        except ValueError as e:
            app.logger.error(f"Failed to configure service registry: {e}")
            raise

        # Register with service registry
        success = self.client.register()
        if not success:
            app.logger.error("Failed to register with service registry")
            raise RuntimeError("Failed to register with service registry")

        app.logger.info(
            f"Registered with service registry as "
            f"'{os.getenv('SRSR_SERVICE_NAME')}'"
        )

        # Deregister on application teardown
        @app.teardown_appcontext
        def cleanup_registry(exception=None):
            if self.client and self.client.is_registered:
                self.client.deregister()
                app.logger.info("Deregistered from service registry")
