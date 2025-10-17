import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional


class StateManager:
    """Manages local SDK state for idempotency and caching."""

    def __init__(self, app_slug: str, state_directory: Optional[str] = None) -> None:
        self.app_slug = app_slug

        # Use provided directory or derive platform-specific one
        if state_directory:
            # Normalize path: expand ~ and resolve relative paths
            self._state_dir = Path(state_directory).expanduser().resolve()
        else:
            self._state_dir = self._get_state_directory()

        self._state_file = self._state_dir / "state.json"
        self._ensure_state_dir()

    def _get_state_directory(self) -> Path:
        """Get the platform-specific state directory."""
        system = platform.system().lower()

        if system == "darwin":
            # macOS: ~/Library/Application Support/Replicated/<app_slug>
            base_dir = Path.home() / "Library" / "Application Support"
        elif system == "windows":
            # Windows: %APPDATA%\Replicated\<app_slug>
            default_path = Path.home() / "AppData" / "Roaming"
            appdata = os.environ.get("APPDATA", default_path)
            base_dir = Path(appdata)
        else:
            # Linux: ${XDG_STATE_HOME:-~/.local/state}/replicated/<app_slug>
            xdg_state = os.environ.get("XDG_STATE_HOME")
            if xdg_state:
                base_dir = Path(xdg_state)
            else:
                base_dir = Path.home() / ".local" / "state"

        return base_dir / "Replicated" / self.app_slug

    def _ensure_state_dir(self) -> None:
        """Ensure the state directory exists."""
        self._state_dir.mkdir(parents=True, exist_ok=True)

    def get_state(self) -> Dict[str, Any]:
        """Get the current state."""
        if self._state_file.exists():
            try:
                with open(self._state_file, "r") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state to disk."""
        try:
            with open(self._state_file, "w") as f:
                json.dump(state, f, indent=2)
        except OSError:
            pass  # Silently ignore write errors

    def get_customer_id(self) -> Optional[str]:
        """Get the cached customer ID."""
        state = self.get_state()
        return state.get("customer_id")

    def set_customer_id(self, customer_id: str) -> None:
        """Set the customer ID in state."""
        state = self.get_state()
        state["customer_id"] = customer_id
        self.save_state(state)

    def get_instance_id(self) -> Optional[str]:
        """Get the cached instance ID."""
        state = self.get_state()
        return state.get("instance_id")

    def set_instance_id(self, instance_id: str) -> None:
        """Set the instance ID in state."""
        state = self.get_state()
        state["instance_id"] = instance_id
        self.save_state(state)

    def get_dynamic_token(self) -> Optional[str]:
        """Get the cached dynamic client token."""
        state = self.get_state()
        return state.get("dynamic_token")

    def set_dynamic_token(self, token: str) -> None:
        """Set the dynamic client token in state."""
        state = self.get_state()
        state["dynamic_token"] = token
        self.save_state(state)

    def get_customer_email(self) -> Optional[str]:
        """Get the cached customer email."""
        state = self.get_state()
        return state.get("customer_email")

    def set_customer_email(self, email: str) -> None:
        """Set the customer email in state."""
        state = self.get_state()
        state["customer_email"] = email
        self.save_state(state)

    def clear_state(self) -> None:
        """Clear all cached state."""
        if self._state_file.exists():
            try:
                self._state_file.unlink()
            except OSError:
                pass
