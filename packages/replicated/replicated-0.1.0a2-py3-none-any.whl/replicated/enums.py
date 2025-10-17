from enum import Enum


class InstanceStatus(Enum):
    """Instance status enumeration."""

    RUNNING = "running"
    DEGRADED = "degraded"
