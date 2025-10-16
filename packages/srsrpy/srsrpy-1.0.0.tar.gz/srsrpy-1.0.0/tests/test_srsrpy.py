import pytest
import requests
from threading import Event
from httmock import all_requests, urlmatch, HTTMock
from os import path
import os
import sys
sys.path.append(path.dirname(path.realpath(__file__)) + "/../src")
from srsrpy import srsrpy  # noqa: E402


@pytest.fixture
def client():
    return srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000'
    )


@all_requests
def show_req(url, request):
    print(url.path)
    return {'status_code': 200,
            'content': '{"id":"foo"}'}


@urlmatch(path=r'/register$')
def register_mock(url, request):
    return {'status_code': 200,
            'content': '{"id":"123"}'}


@urlmatch(path=r'/deregister$')
def deregister_mock(url, request):
    return {'status_code': 200}


heart_event = Event()


@urlmatch(path=r'/heartbeat$')
def heartbeat_mock(url, request):
    heart_event.set()
    return {'status_code': 200}


def test_register(client):
    with HTTMock(register_mock):
        client.register()
    with HTTMock(deregister_mock):
        client.deregister()


def test_heartbeat(client):
    heart_event.clear()
    client.heartbeat_interval_seconds = 0.01
    with HTTMock(heartbeat_mock):
        with HTTMock(register_mock):
            client.register()

        heartbeat_sent = heart_event.wait(1)
        assert heartbeat_sent

        with HTTMock(deregister_mock):
            client.deregister()


def test_register_doesnt_throw_connectionerror(client):
    success = client.register()
    assert not success


def test_deregister_not_registered(client):
    client.deregister()


def test_deregister_doesnt_throw_connectionerror(client):
    with HTTMock(register_mock):
        client.register()

    client.deregister()


def test_heartbeat_doesnt_throw_connectionerror(client):
    client.heartbeat_interval_seconds = 0.01

    with HTTMock(register_mock):
        client.register()

    # Wait for a heartbeat, which should fail without throwing
    heart_event.clear()
    heart_event.wait(.05)

    with HTTMock(deregister_mock):
        client.deregister()


def test_heartbeat_error_handler():
    error_captured = Event()
    captured_error = None

    def error_handler(error):
        nonlocal captured_error
        captured_error = error
        error_captured.set()

    @urlmatch(path=r'/heartbeat$')
    def failing_heartbeat_mock(url, request):
        raise requests.exceptions.ConnectionError("Simulated connection error")

    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000',
        heartbeat_interval=0.01,
        heartbeat_error_handler=error_handler
    )

    with HTTMock(register_mock):
        client.register()

    # Now mock heartbeat to fail
    with HTTMock(failing_heartbeat_mock):
        # Wait for heartbeat error to be captured
        error_occurred = error_captured.wait(1)
        assert error_occurred
        assert captured_error is not None

    client.deregister()

    with HTTMock(deregister_mock):
        client.deregister()


def test_configurable_heartbeat_interval():
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000',
        heartbeat_interval=5
    )
    assert client.heartbeat_interval_seconds == 5


def test_default_registry_address():
    """Test that None registry_address uses default registry address"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        service_address='http://service:3000'
    )
    assert client.server_address == 'http://localhost:4214'


def test_env_var_registry_address():
    """Test that SRSR_REGISTRY_URL environment variable is used"""
    os.environ['SRSR_REGISTRY_URL'] = 'http://custom-registry:9999'
    try:
        client = srsrpy.ServiceRegistryClient(
            'my-service',
            service_address='http://service:3000'
        )
        assert client.server_address == 'http://custom-registry:9999'
    finally:
        del os.environ['SRSR_REGISTRY_URL']


def test_explicit_registry_address_overrides_env():
    """Test that explicit address takes precedence over env var"""
    os.environ['SRSR_REGISTRY_URL'] = 'http://env-registry:9999'
    try:
        client = srsrpy.ServiceRegistryClient(
            'my-service',
            registry_address='http://explicit-registry:8888',
            service_address='http://service:3000'
        )
        assert client.server_address == 'http://explicit-registry:8888'
    finally:
        del os.environ['SRSR_REGISTRY_URL']


def test_port_in_address_only():
    """Test valid configuration: port specified in address only"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://localhost:3000'
    )
    with HTTMock(register_mock):
        success = client.register()
        assert success
    with HTTMock(deregister_mock):
        client.deregister()


def test_port_as_separate_arg_only():
    """Test valid configuration: port specified as separate argument only"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://localhost',
        service_port='3000'
    )
    with HTTMock(register_mock):
        success = client.register()
        assert success
    with HTTMock(deregister_mock):
        client.deregister()


def test_no_port_specified():
    """Test valid configuration: no port specified anywhere"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://localhost'
    )
    with HTTMock(register_mock):
        success = client.register()
        assert success
    with HTTMock(deregister_mock):
        client.deregister()


def test_port_in_both_places_raises_error():
    """Test that specifying port in both address and arg raises ValueError"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://localhost:3000',
        service_port='3000'
    )
    with pytest.raises(ValueError) as excinfo:
        client.register()
    assert "address already contains port" in str(excinfo.value)


def test_context_manager_successful_registration():
    """Test that context manager registers on enter and deregisters on exit"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000'
    )

    with HTTMock(register_mock, deregister_mock):
        with client as c:
            assert c is client
            assert client.is_registered

        # After exiting context, should be deregistered
        assert not client.is_registered


@urlmatch(path=r'/register$')
def failing_register_mock(url, request):
    return {'status_code': 500}


def test_context_manager_registration_failure():
    """Test that context manager raises exception when registration fails"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000'
    )

    with HTTMock(failing_register_mock):
        with pytest.raises(RuntimeError) as excinfo:
            with client:
                pass

        assert "Failed to register" in str(excinfo.value)
        assert not client.is_registered


def test_context_manager_deregisters_on_exception():
    """Test that context manager deregisters even when exception occurs inside block"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000'
    )

    with HTTMock(register_mock, deregister_mock):
        with pytest.raises(ValueError):
            with client:
                assert client.is_registered
                # Raise an exception inside the context
                raise ValueError("Test exception")

        # After exception, should still be deregistered
        assert not client.is_registered


def test_context_manager_does_not_suppress_exceptions():
    """Test that context manager does not suppress exceptions from within the block"""
    client = srsrpy.ServiceRegistryClient(
        'my-service',
        registry_address='http://registry:4214',
        service_address='http://service:3000'
    )

    exception_message = "Custom error message"

    with HTTMock(register_mock, deregister_mock):
        with pytest.raises(RuntimeError) as excinfo:
            with client:
                raise RuntimeError(exception_message)

        # Verify the exact exception propagated out
        assert str(excinfo.value) == exception_message


def test_new_signature_minimal():
    """Test new Pythonic signature with just service name"""
    client = srsrpy.ServiceRegistryClient('my-service')

    assert client.client_name == 'my-service'
    assert client.server_address == 'http://localhost:4214'
    assert client.client_address == ''
    assert client.client_port == ''
    assert client.heartbeat_interval_seconds == 20


def test_from_env_minimal():
    """Test from_env() with just SRSR_SERVICE_NAME"""
    os.environ['SRSR_SERVICE_NAME'] = 'my-service'
    try:
        client = srsrpy.ServiceRegistryClient.from_env()

        assert client.client_name == 'my-service'
        assert client.server_address == 'http://localhost:4214'
        assert client.client_address == ''
        assert client.client_port == ''
        assert client.heartbeat_interval_seconds == 20
    finally:
        del os.environ['SRSR_SERVICE_NAME']


def test_from_env_all_vars():
    """Test from_env() with all environment variables set"""
    os.environ['SRSR_SERVICE_NAME'] = 'my-service'
    os.environ['SRSR_REGISTRY_URL'] = 'http://custom-registry:9999'
    os.environ['SRSR_SERVICE_ADDRESS'] = 'http://service:3000'
    os.environ['SRSR_SERVICE_PORT'] = '8080'
    os.environ['SRSR_HEARTBEAT_INTERVAL'] = '15'
    try:
        client = srsrpy.ServiceRegistryClient.from_env()

        assert client.client_name == 'my-service'
        assert client.server_address == 'http://custom-registry:9999'
        assert client.client_address == 'http://service:3000'
        assert client.client_port == '8080'
        assert client.heartbeat_interval_seconds == 15
    finally:
        del os.environ['SRSR_SERVICE_NAME']
        del os.environ['SRSR_REGISTRY_URL']
        del os.environ['SRSR_SERVICE_ADDRESS']
        del os.environ['SRSR_SERVICE_PORT']
        del os.environ['SRSR_HEARTBEAT_INTERVAL']


def test_from_env_missing_service_name():
    """Test from_env() raises ValueError when SRSR_SERVICE_NAME is missing"""
    # Make sure SRSR_SERVICE_NAME is not set
    if 'SRSR_SERVICE_NAME' in os.environ:
        del os.environ['SRSR_SERVICE_NAME']

    with pytest.raises(ValueError) as excinfo:
        srsrpy.ServiceRegistryClient.from_env()

    assert "SRSR_SERVICE_NAME environment variable is required" in str(excinfo.value)
