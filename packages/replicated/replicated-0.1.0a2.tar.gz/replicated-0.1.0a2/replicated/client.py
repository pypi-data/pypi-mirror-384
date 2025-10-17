from typing import Any, Dict, Optional

from .fingerprint import get_machine_fingerprint
from .http_client import SyncHTTPClient
from .services import CustomerService
from .state import StateManager


class ReplicatedClient:
    """Synchronous client for the Replicated SDK."""

    def __init__(
        self,
        publishable_key: str,
        app_slug: str,
        base_url: str = "https://replicated.app",
        timeout: float = 30.0,
        state_directory: Optional[str] = None,
    ) -> None:
        self.publishable_key = publishable_key
        self.app_slug = app_slug
        self.base_url = base_url
        self.timeout = timeout
        self.state_directory = state_directory
        self._machine_id = get_machine_fingerprint()

        self.http_client = SyncHTTPClient(
            base_url=base_url,
            timeout=timeout,
        )
        self.state_manager = StateManager(app_slug, state_directory=state_directory)
        self.customer = CustomerService(self)

    def __enter__(self) -> "ReplicatedClient":
        self.http_client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.http_client.__exit__(exc_type, exc_val, exc_tb)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        # Try to use dynamic token first, fall back to publishable key
        dynamic_token = self.state_manager.get_dynamic_token()
        if dynamic_token:
            # Service tokens are sent without Bearer prefix
            return {"Authorization": dynamic_token}
        else:
            # Publishable keys use Bearer prefix
            return {"Authorization": f"Bearer {self.publishable_key}"}
