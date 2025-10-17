# Replicated Python SDK API Reference

## Installation

```bash
pip install replicated
```

## Quick Start

### Synchronous Usage

```python
from replicated import ReplicatedClient, InstanceStatus

client = ReplicatedClient(
    publishable_key="replicated_pk_...", 
    app_slug="my-app"
)

customer = client.customer.get_or_create(email_address="user@example.com")
instance = customer.get_or_create_instance()

instance.send_metric("cpu_usage", 0.83)
instance.set_status(InstanceStatus.RUNNING)
instance.set_version("1.2.0")
```

### Asynchronous Usage

```python
from replicated import AsyncReplicatedClient, InstanceStatus

async with AsyncReplicatedClient(
    publishable_key="replicated_pk_...",
    app_slug="my-app"
) as client:
    customer = await client.customer.get_or_create(email_address="user@example.com")
    instance = await customer.get_or_create_instance()
    
    await instance.send_metric("cpu_usage", 0.83)
    await instance.set_status(InstanceStatus.RUNNING)
    await instance.set_version("1.2.0")
```

## API Reference

### ReplicatedClient

The main synchronous client for interacting with the Replicated API.

#### Constructor

```python
ReplicatedClient(
    publishable_key: str,
    app_slug: str,
    base_url: str = "https://replicated.app",
    timeout: float = 30.0,
    state_directory: Optional[str] = None
)
```

**Parameters:**
- `publishable_key`: Your publishable API key from the Vendor Portal
- `app_slug`: Your application slug
- `base_url`: Base URL for the API (optional, defaults to "https://replicated.app")
- `timeout`: Request timeout in seconds (optional, defaults to 30.0)
- `state_directory`: Custom directory for state storage (optional). If not provided, uses platform-specific defaults. Supports `~` expansion and relative paths.

#### Methods

- `client.customer.get_or_create(email_address: str, channel: str = None) -> Customer`

### AsyncReplicatedClient

The asynchronous version of ReplicatedClient with identical API but requiring `await`.

#### Constructor

Same parameters as `ReplicatedClient`.

#### Context Manager

```python
async with AsyncReplicatedClient(...) as client:
    # Use client here
```

### Customer

Represents a Replicated customer.

#### Properties

- `customer_id: str` - Unique customer identifier
- `email_address: str` - Customer email address
- `channel: Optional[str]` - Release channel

#### Methods

- `get_or_create_instance() -> Instance` (sync) / `-> AsyncInstance` (async)

### Instance / AsyncInstance

Represents a customer instance.

#### Properties

- `customer_id: str` - Associated customer ID
- `instance_id: Optional[str]` - Unique instance identifier

#### Methods

**Metrics:**
- `send_metric(name: str, value: Union[int, float, str]) -> None`
- `delete_metric(name: str) -> None`

**Status and Version:**
- `set_status(status: InstanceStatus) -> None`
- `set_version(version: str) -> None`

### InstanceStatus

Enumeration for instance status values.

#### Values

- `InstanceStatus.RUNNING` - Instance is running normally
- `InstanceStatus.DEGRADED` - Instance is running but degraded

### Exceptions

All exceptions inherit from `ReplicatedError`.

#### Exception Hierarchy

```
ReplicatedError
├── ReplicatedAPIError      # API returned an error
├── ReplicatedAuthError     # Authentication failed (401)
├── ReplicatedRateLimitError # Rate limit exceeded (429)
└── ReplicatedNetworkError  # Network communication failed
```

#### Exception Properties

All exceptions include:
- `message: str` - Error message
- `http_status: Optional[int]` - HTTP status code
- `http_body: Optional[str]` - Raw response body
- `json_body: Optional[Dict]` - Parsed JSON response
- `headers: Optional[Dict]` - Response headers
- `code: Optional[str]` - Error code from API

## State Management

The SDK automatically manages local state for:
- Customer ID caching
- Instance ID caching  
- Dynamic token storage

### State Directory

State is stored in platform-specific directories by default:
- **macOS:** `~/Library/Application Support/Replicated/<app_slug>`
- **Linux:** `${XDG_STATE_HOME:-~/.local/state}/replicated/<app_slug>`
- **Windows:** `%APPDATA%\Replicated\<app_slug>`

You can override the state directory by providing the `state_directory` parameter:

```python
client = ReplicatedClient(
    publishable_key="...",
    app_slug="my-app",
    state_directory="/custom/path/to/state"
)
```

**Path Handling:**
- The SDK automatically expands `~` to your home directory
- Relative paths are resolved to absolute paths
- The directory will be created automatically if it doesn't exist

**Use Cases for Custom Directories:**
- **Testing:** Use temporary directories for isolated test runs
- **Containers:** Mount persistent volumes at custom paths
- **Multi-tenant:** Isolate state per tenant in separate directories
- **Development:** Use project-local directories for development state

## Machine Fingerprinting

The SDK generates unique machine fingerprints using:
- **macOS:** IOPlatformUUID
- **Linux:** D-Bus machine ID (`/var/lib/dbus/machine-id` or `/etc/machine-id`)
- **Windows:** Machine GUID from registry

All fingerprints are SHA256 hashed for privacy.

## Error Handling

```python
from replicated import ReplicatedClient, ReplicatedAuthError, ReplicatedAPIError

client = ReplicatedClient(publishable_key="...", app_slug="...")

try:
    customer = client.customer.get_or_create("user@example.com")
except ReplicatedAuthError:
    print("Authentication failed - check your publishable key")
except ReplicatedAPIError as e:
    print(f"API error: {e.message} (HTTP {e.http_status})")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Context Managers

Both sync and async clients support context managers for automatic resource cleanup:

```python
# Sync
with ReplicatedClient(...) as client:
    # client automatically closed

# Async  
async with AsyncReplicatedClient(...) as client:
    # client automatically closed
```

## Thread Safety

The synchronous client creates a new HTTP client per request and is thread-safe. For high-concurrency applications, consider using the async client with a single event loop.
