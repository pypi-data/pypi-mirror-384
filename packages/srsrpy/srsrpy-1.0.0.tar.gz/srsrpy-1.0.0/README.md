# SRSR Python Client

Python client library for the [srsr service registry](https://github.com/ifIMust/srsr).

The client automatically handles registration, heartbeat maintenance, and deregistration with the service registry server. It supports configurable heartbeat intervals and error handling for robust service discovery in microservice architectures.

> **Note**: See [ROADMAP.md](ROADMAP.md) for planned improvements including context manager support, improved API ergonomics, and 12-factor app patterns.

## Installation

```bash
pip install srsrpy
```

## Configuration

### Registry Address

The service registry address can be specified in three ways (in order of precedence):

1. **Explicitly in code**: Pass the address to `ServiceRegistryClient`
2. **Environment variable**: Set `SRSR_REGISTRY_URL` (e.g., `export SRSR_REGISTRY_URL=http://localhost:4214`)
3. **Default**: Uses `http://localhost:4214` if not specified

```python
# Explicit address
client = srsrpy.ServiceRegistryClient('my-service', registry_address='http://registry:4214', service_address='http://localhost:3000')

# Use environment variable or default
client = srsrpy.ServiceRegistryClient('my-service', service_address='http://localhost:3000')
```

### Service Port Specification Rules

When registering your service, the service's port can be specified in different ways:

1. **In the service address**: `service_address='http://localhost:3000'`
2. **As a separate argument**: `service_port='3000'` (without port in address)
3. **Omitted entirely**: The registry server will deduce your service's address from the connection

**Important**: Port cannot be specified in both the address and as a separate argument - this raises a `ValueError`.

```python
# Valid: Port in service address
client = srsrpy.ServiceRegistryClient('my-service', service_address='http://localhost:3000')

# Valid: Port as separate argument (address without port)
client = srsrpy.ServiceRegistryClient('my-service', service_address='http://localhost', service_port='3000')

# Valid: Port as separate argument (no address)
client = srsrpy.ServiceRegistryClient('my-service', service_port='3000')

# Valid: No port specified - server deduces service address from connection
client = srsrpy.ServiceRegistryClient('my-service', service_address='http://localhost')

# Invalid: Port in both places - raises ValueError
client = srsrpy.ServiceRegistryClient('my-service', service_address='http://localhost:3000', service_port='3000')
```

## Basic Usage

### Using Environment Variables with from_env()

For cloud-native and containerized applications, you can configure the client entirely through environment variables using the `from_env()` factory method:

```python
from srsrpy import srsrpy

# Set environment variables (e.g., in your deployment config, Dockerfile, or .env)
# export SRSR_SERVICE_NAME=my-service
# export SRSR_REGISTRY_URL=http://registry:4214  # Optional, defaults to localhost:4214
# export SRSR_SERVICE_ADDRESS=http://localhost:3000  # Optional
# export SRSR_HEARTBEAT_INTERVAL=20  # Optional

def main():
    # Configuration comes entirely from environment variables
    with srsrpy.ServiceRegistryClient.from_env():
        # Your service runs here...
        run_service()

if __name__ == "__main__":
    main()
```

**Environment Variables:**
- `SRSR_SERVICE_NAME` - Service name (required)
- `SRSR_REGISTRY_URL` - Registry address (optional, defaults to `http://localhost:4214`)
- `SRSR_SERVICE_ADDRESS` - Service address (optional)
- `SRSR_SERVICE_PORT` - Service port (optional)
- `SRSR_HEARTBEAT_INTERVAL` - Heartbeat interval in seconds (optional, defaults to 20)

### Using Context Manager (Recommended)

The recommended approach is to use the context manager pattern, which automatically handles registration and deregistration:

```python
from srsrpy import srsrpy

def main():
    # Using 'with' automatically registers on entry and deregisters on exit
    with srsrpy.ServiceRegistryClient(
        'my-service',                           # Service name (required)
        registry_address='http://localhost:4214',  # Registry server address (optional)
        service_address='http://localhost:3000'    # This service's address (optional)
    ):
        # Your service runs here...
        # Heartbeats are sent automatically every 20 seconds
        run_service()

    # Deregistration happens automatically, even if an exception occurs

if __name__ == "__main__":
    main()
```

The context manager will:
- Register with the service registry when entering the `with` block
- Raise a `RuntimeError` if registration fails
- Automatically deregister when exiting the block (even if an exception occurs)
- Not suppress any exceptions that occur within the block

### Manual Registration (Alternative)

You can also manage registration manually if needed:

```python
from srsrpy import srsrpy

def main():
    # Connect to registry at localhost:4214, register this service at localhost:3000
    client = srsrpy.ServiceRegistryClient(
        'my-service',                           # Service name (required)
        registry_address='http://localhost:4214',  # Registry server address (optional)
        service_address='http://localhost:3000'    # This service's address (optional)
    )

    # Register and start automatic heartbeats
    success = client.register()
    if not success:
        print("Failed to register with service registry")
        return

    try:
        # Your service runs here...
        # Heartbeats are sent automatically every 20 seconds
        run_service()
    finally:
        # Always deregister on shutdown
        client.deregister()

if __name__ == "__main__":
    main()
```

### Port-Only Registration

If your service cannot determine its full address, you can register with just a port:

```python
from srsrpy import srsrpy

# The server will deduce the client IP and use http scheme
client = srsrpy.ServiceRegistryClient(
    'my-service',                           # Service name
    registry_address='http://localhost:4214',  # Registry server (optional)
    service_port='3000'                     # Just the port - server deduces IP
)

success = client.register()
```

## Advanced Configuration

```python
from srsrpy import srsrpy

def heartbeat_error_handler(error):
    print(f"Service registry heartbeat failed: {error}")

def main():
    client = srsrpy.ServiceRegistryClient(
        'my-service',                               # Service name
        registry_address='http://localhost:4214',   # Registry server (optional)
        service_address='http://localhost:3000',    # Service address (optional)
        heartbeat_interval=10,                      # Custom interval in seconds (default: 20)
        heartbeat_error_handler=heartbeat_error_handler  # Optional error callback
    )

    success = client.register()
    if success:
        # Service logic here...
        pass
```

## Configuration Options

### `heartbeat_interval` (int)
Sets how often heartbeats are sent to the registry in seconds. Default is 20 seconds.

### `heartbeat_error_handler` (callable)
Sets an optional callback function that will be called whenever heartbeat requests fail. The handler receives the error that occurred. By default, heartbeat failures are silently ignored.

```python
# Example: Log heartbeat failures and update metrics
def error_handler(error):
    logger.error(f"Registry heartbeat failed: {error}")
    metrics.increment_counter("registry_heartbeat_failures")

client = srsrpy.ServiceRegistryClient(
    'my-service',
    registry_address='http://localhost:4214',
    service_address='http://localhost:3000',
    heartbeat_error_handler=error_handler
)
```

## Interface

### `register() -> bool`
Registers the service with the registry and starts automatic heartbeat maintenance. Returns `True` if registration succeeds, `False` otherwise.

### `deregister() -> None`
Stops heartbeat maintenance and deregisters the service from the registry. Safe to call multiple times.

## Error Handling

The client handles various error conditions gracefully:

- **Network failures during registration**: Registration returns `False`
- **Network failures during heartbeat**: By default, silently ignored (service will timeout and be deregistered). Optionally surfaced through `heartbeat_error_handler`
- **Invalid responses**: Handled appropriately (e.g., missing ID field)
- **Connection errors**: Caught and handled without crashing the application

### Heartbeat Error Handling

By default, heartbeat failures are silently ignored to prevent noisy logging. However, you can provide a custom error handler to:
- Log heartbeat failures for debugging
- Update metrics or monitoring systems
- Take application-specific actions

## Signal Handler Example

For graceful shutdown, the context manager pattern automatically handles cleanup. If you need to preserve existing signal handlers for manual registration:

```python
import signal
from srsrpy import srsrpy

client = srsrpy.ServiceRegistryClient(
    'my-service',
    registry_address='http://localhost:4214',
    service_address='http://localhost:3000'
)

success = client.register()
if success:
    # Save the original handler and set up graceful shutdown
    prev_handler = signal.getsignal(signal.SIGINT)

    def handle_sigint(sig, frame):
        client.deregister()

        # Call the original handler if it existed
        if prev_handler:
            prev_handler(sig, frame)

    signal.signal(signal.SIGINT, handle_sigint)
```

Note: When using the context manager pattern, cleanup is automatic and signal handlers are typically not needed for deregistration.
