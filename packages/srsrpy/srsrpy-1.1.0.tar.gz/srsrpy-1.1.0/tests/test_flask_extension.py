"""Tests for Flask extension."""

import pytest
import os
from httmock import urlmatch, HTTMock

# Flask is optional, skip tests if not installed
flask = pytest.importorskip("flask")

from srsrpy.contrib.flask import FlaskServiceRegistry  # noqa: E402


@urlmatch(path=r'/register$')
def register_mock(url, request):
    return {'status_code': 200, 'content': '{"id":"test-flask-123"}'}


@urlmatch(path=r'/deregister$')
def deregister_mock(url, request):
    return {'status_code': 200}


@urlmatch(path=r'/heartbeat$')
def heartbeat_mock(url, request):
    return {'status_code': 200}


def test_flask_extension_basic_usage():
    """Test basic Flask extension usage with direct initialization."""
    os.environ['SRSR_SERVICE_NAME'] = 'test-flask-service'
    os.environ['SRSR_REGISTRY_URL'] = 'http://registry:4214'
    os.environ['SRSR_SERVICE_ADDRESS'] = 'http://localhost:5000'

    try:
        app = flask.Flask(__name__)

        with HTTMock(register_mock, deregister_mock, heartbeat_mock):
            registry = FlaskServiceRegistry(app)

            # Should be registered
            assert registry.client is not None
            assert registry.client.is_registered

            # Simulate app context teardown
            with app.app_context():
                pass

            # Should deregister on teardown
            assert not registry.client.is_registered
    finally:
        del os.environ['SRSR_SERVICE_NAME']
        del os.environ['SRSR_REGISTRY_URL']
        del os.environ['SRSR_SERVICE_ADDRESS']


def test_flask_extension_init_app_pattern():
    """Test Flask extension with init_app() pattern."""
    os.environ['SRSR_SERVICE_NAME'] = 'test-flask-service'

    try:
        app = flask.Flask(__name__)
        registry = FlaskServiceRegistry()

        # Should not be registered yet
        assert registry.client is None

        with HTTMock(register_mock, deregister_mock, heartbeat_mock):
            registry.init_app(app)

            # Now should be registered
            assert registry.client is not None
            assert registry.client.is_registered

            # Simulate app context teardown
            with app.app_context():
                pass

            # Should deregister on teardown
            assert not registry.client.is_registered
    finally:
        del os.environ['SRSR_SERVICE_NAME']


def test_flask_extension_graceful_degradation_no_service_name():
    """Test extension does nothing if SRSR_SERVICE_NAME not set."""
    # Make sure SRSR_SERVICE_NAME is not set
    if 'SRSR_SERVICE_NAME' in os.environ:
        del os.environ['SRSR_SERVICE_NAME']

    app = flask.Flask(__name__)
    registry = FlaskServiceRegistry(app)

    # Should not create a client - graceful degradation
    assert registry.client is None


def test_flask_extension_registration_failure():
    """Test that extension raises if registration fails."""
    os.environ['SRSR_SERVICE_NAME'] = 'test-flask-service'

    try:
        app = flask.Flask(__name__)

        # No mock - registration will fail
        with pytest.raises(RuntimeError) as excinfo:
            FlaskServiceRegistry(app)

        assert "Failed to register with service registry" in str(excinfo.value)
    finally:
        del os.environ['SRSR_SERVICE_NAME']


def test_flask_extension_invalid_app_type():
    """Test that init_app raises TypeError if app is not Flask instance."""
    os.environ['SRSR_SERVICE_NAME'] = 'test-flask-service'

    try:
        registry = FlaskServiceRegistry()

        with pytest.raises(TypeError) as excinfo:
            registry.init_app("not a flask app")

        assert "app must be a Flask application instance" in str(excinfo.value)
    finally:
        del os.environ['SRSR_SERVICE_NAME']


def test_flask_extension_with_all_env_vars():
    """Test Flask extension with all environment variables configured."""
    os.environ['SRSR_SERVICE_NAME'] = 'test-flask-service'
    os.environ['SRSR_REGISTRY_URL'] = 'http://custom-registry:9999'
    os.environ['SRSR_SERVICE_ADDRESS'] = 'http://my-service:8080'
    os.environ['SRSR_HEARTBEAT_INTERVAL'] = '15'

    try:
        app = flask.Flask(__name__)

        with HTTMock(register_mock, deregister_mock, heartbeat_mock):
            registry = FlaskServiceRegistry(app)

            # Verify client was configured correctly
            assert registry.client.client_name == 'test-flask-service'
            assert (registry.client.server_address ==
                    'http://custom-registry:9999')
            assert registry.client.client_address == 'http://my-service:8080'
            assert registry.client.heartbeat_interval_seconds == 15
            assert registry.client.is_registered

            # Clean up
            with app.app_context():
                pass

            assert not registry.client.is_registered
    finally:
        del os.environ['SRSR_SERVICE_NAME']
        del os.environ['SRSR_REGISTRY_URL']
        del os.environ['SRSR_SERVICE_ADDRESS']
        del os.environ['SRSR_HEARTBEAT_INTERVAL']
