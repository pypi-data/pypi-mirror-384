from typing import Any, Dict, Optional


class ReplicatedError(Exception):
    """Base exception for all Replicated SDK errors."""

    def __init__(
        self,
        message: str,
        http_body: Optional[str] = None,
        http_status: Optional[int] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body
        self.headers = headers
        self.code = code

    def __str__(self) -> str:
        if self.http_status and self.code:
            return f"{self.http_status} {self.code}: {self.message}"
        elif self.http_status:
            return f"{self.http_status}: {self.message}"
        return self.message


class ReplicatedAPIError(ReplicatedError):
    """Raised when the API returns an error response."""

    pass


class ReplicatedAuthError(ReplicatedError):
    """Raised when authentication fails."""

    pass


class ReplicatedRateLimitError(ReplicatedError):
    """Raised when rate limit is exceeded."""

    pass


class ReplicatedNetworkError(ReplicatedError):
    """Raised when network communication fails."""

    pass
