import os
import requests
from threading import Thread, Event
from urllib.parse import urlparse


# Default registry server address
DEFAULT_REGISTRY_ADDRESS = "http://localhost:4214"

# Environment variable for registry address
REGISTRY_ENV_VAR = "SRSR_REGISTRY_URL"


def _discover_registry_address():
    """Returns the registry address using environment variable or default."""
    return os.environ.get(REGISTRY_ENV_VAR, DEFAULT_REGISTRY_ADDRESS)


# ServiceRegistryClient encapsulates client registration,
# heartbeat, and deregistration.
class ServiceRegistryClient:
    def __init__(self, service_name, *,
                 registry_address=None,
                 service_address='',
                 service_port='',
                 heartbeat_interval=20,
                 heartbeat_error_handler=None):
        self.heartbeat_interval_seconds = heartbeat_interval
        self.server_address = registry_address or _discover_registry_address()
        self.client_name = service_name
        self.client_address = service_address
        self.client_port = service_port
        self.heartbeat_error_handler = heartbeat_error_handler

        self.is_registered = False
        self.client_id = ""
        self.heartbeat_thread = None
        self.stop = None

    def __enter__(self):
        """Enter context manager: register with the service registry.

        Returns:
            self: The ServiceRegistryClient instance

        Raises:
            RuntimeError: If registration fails
        """
        if not self.register():
            raise RuntimeError("Failed to register with service registry")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager: deregister from the service registry.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred

        Returns:
            None (does not suppress exceptions)
        """
        self.deregister()
        return None

    @classmethod
    def from_env(cls):
        """Create a ServiceRegistryClient from environment variables.

        Reads configuration from environment variables.

        Environment variables:
            SRSR_SERVICE_NAME: Service name (required)
            SRSR_REGISTRY_URL: Registry address (optional, has default)
            SRSR_SERVICE_ADDRESS: Service address (optional)
            SRSR_SERVICE_PORT: Service port (optional)
            SRSR_HEARTBEAT_INTERVAL: Heartbeat interval in seconds (optional)

        Returns:
            ServiceRegistryClient: Configured client instance

        Raises:
            ValueError: If SRSR_SERVICE_NAME is not set
        """
        service_name = os.environ.get('SRSR_SERVICE_NAME')
        if not service_name:
            raise ValueError(
                "SRSR_SERVICE_NAME environment variable is required"
            )

        registry_address = os.environ.get('SRSR_REGISTRY_URL')
        service_address = os.environ.get('SRSR_SERVICE_ADDRESS', '')
        service_port = os.environ.get('SRSR_SERVICE_PORT', '')
        heartbeat_interval = int(
            os.environ.get('SRSR_HEARTBEAT_INTERVAL', '20')
        )

        return cls(
            service_name,
            registry_address=registry_address,
            service_address=service_address,
            service_port=service_port,
            heartbeat_interval=heartbeat_interval
        )

    def register(self):
        # Validate address format and check for double port specification
        normalized_address = self.client_address
        if self.client_address:
            try:
                parsed = urlparse(self.client_address)
                if self.client_port and parsed.port is not None:
                    raise ValueError(
                        "invalid configuration: address already contains "
                        "port, cannot also specify separate port"
                    )
                # Use normalized URL from parser
                normalized_address = parsed.geturl()
            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"invalid service address format: {e}")

        reg_data = {
            'name': self.client_name,
            'address': normalized_address,
            'port': self.client_port
        }
        try:
            r = requests.post(self.server_address + "/register", json=reg_data)
            if r.status_code == requests.codes.ok:
                resp_json = r.json()
                if 'id' in resp_json:
                    self.client_id = resp_json['id']
                    self.is_registered = True
                    self.stop = Event()
                    self.heartbeat_thread = Thread(target=self.keep_alive)
                    self.heartbeat_thread.start()
                    return True
        except requests.exceptions.ConnectionError:
            pass
        return False

    def deregister(self):
        if self.is_registered:
            self.stop.set()
            self.heartbeat_thread.join()
            self.is_registered = False
            dereg_data = {'id': self.client_id}
            try:
                requests.post(self.server_address + "/deregister",
                              json=dereg_data)
            except requests.exceptions.ConnectionError:
                pass

    def keep_alive(self):
        heartbeat_data = {'id': self.client_id}
        while not self.stop.is_set():
            stop_flag = self.stop.wait(self.heartbeat_interval_seconds)
            if not stop_flag:
                try:
                    requests.post(self.server_address + "/heartbeat",
                                  json=heartbeat_data)
                except requests.exceptions.ConnectionError as e:
                    if self.heartbeat_error_handler:
                        self.heartbeat_error_handler(e)
                except Exception as e:
                    if self.heartbeat_error_handler:
                        self.heartbeat_error_handler(e)
