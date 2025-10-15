from .async_client import AsyncReplicatedClient
from .client import ReplicatedClient
from .enums import InstanceStatus
from .exceptions import (
    ReplicatedAPIError,
    ReplicatedAuthError,
    ReplicatedError,
    ReplicatedNetworkError,
    ReplicatedRateLimitError,
)

# Try to get version from package metadata, fall back to hardcoded version
try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("replicated") + "+python"
except Exception:
    # Fallback for development or if package isn't installed
    __version__ = "1.0.0+python"
__all__ = [
    "ReplicatedClient",
    "AsyncReplicatedClient",
    "InstanceStatus",
    "ReplicatedError",
    "ReplicatedAPIError",
    "ReplicatedAuthError",
    "ReplicatedRateLimitError",
    "ReplicatedNetworkError",
]
