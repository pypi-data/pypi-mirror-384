import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from replicated import AsyncReplicatedClient, ReplicatedClient


class TestReplicatedClient:
    def test_client_initialization(self):
        client = ReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        assert client.publishable_key == "pk_test_123"
        assert client.app_slug == "my-app"
        assert client.base_url == "https://replicated.app"

    def test_context_manager(self):
        with ReplicatedClient(
            publishable_key="pk_test_123", app_slug="my-app"
        ) as client:
            assert client is not None

    @patch("replicated.http_client.httpx.Client")
    def test_customer_creation(self, mock_httpx):
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "customer": {
                "id": "customer_123",
                "email": "test@example.com",
                "name": "test user",
                "serviceToken": "service_token_123",
                "instanceId": "instance_123",
            }
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_httpx.return_value = mock_client

        client = ReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")

        customer = client.customer.get_or_create("test@example.com")
        assert customer.customer_id == "customer_123"
        assert customer.email_address == "test@example.com"

    def test_custom_state_directory(self):
        """Test client with custom absolute state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_state"
            client = ReplicatedClient(
                publishable_key="pk_test_123",
                app_slug="my-app",
                state_directory=str(custom_dir),
            )
            # Resolve both paths to handle symlinks
            # (e.g., /var vs /private/var on macOS)
            assert client.state_manager._state_dir == custom_dir.resolve()
            expected_file = custom_dir.resolve() / "state.json"
            assert client.state_manager._state_file == expected_file
            assert custom_dir.exists()

    def test_custom_state_directory_with_tilde(self):
        """Test that ~ expansion works in custom state directory."""
        client = ReplicatedClient(
            publishable_key="pk_test_123",
            app_slug="my-app",
            state_directory="~/test-replicated-state",
        )
        # Should be expanded to actual home directory
        assert "~" not in str(client.state_manager._state_dir)
        assert str(client.state_manager._state_dir).startswith(str(Path.home()))

    def test_custom_state_directory_relative_path(self):
        """Test that relative paths are resolved in custom state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory and use relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                client = ReplicatedClient(
                    publishable_key="pk_test_123",
                    app_slug="my-app",
                    state_directory="./relative_state",
                )
                # Should be resolved to absolute path
                assert client.state_manager._state_dir.is_absolute()
                assert str(tmpdir) in str(client.state_manager._state_dir)
            finally:
                os.chdir(original_cwd)

    def test_default_state_directory_unchanged(self):
        """Test that default behavior is unchanged when state_directory not provided."""
        client = ReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        # Should use platform-specific directory
        state_dir_str = str(client.state_manager._state_dir)
        assert "my-app" in state_dir_str
        assert "Replicated" in state_dir_str

    def test_client_has_machine_id(self):
        """Test that client initializes with a machine_id."""
        client = ReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        assert hasattr(client, "_machine_id")
        assert client._machine_id is not None
        assert isinstance(client._machine_id, str)
        assert len(client._machine_id) == 64  # SHA256 hash

    @patch("replicated.http_client.httpx.Client")
    def test_instance_has_machine_id_from_client(self, mock_httpx):
        """Test that instances created from client have the client's machine_id."""
        from replicated.resources import Instance

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "customer": {
                "id": "customer_123",
                "email": "test@example.com",
                "name": "test user",
                "serviceToken": "service_token_123",
                "instanceId": "instance_123",
            }
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_httpx.return_value = mock_client

        client = ReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        customer = client.customer.get_or_create("test@example.com")
        instance = customer.get_or_create_instance()

        assert isinstance(instance, Instance)
        assert hasattr(instance, "_machine_id")
        assert instance._machine_id == client._machine_id

    @patch("replicated.http_client.httpx.Client")
    def test_instance_uses_machine_id_in_headers(self, mock_httpx):
        """Test that instance methods use machine_id as cluster ID in headers."""
        from replicated.resources import Instance

        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {}

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_httpx.return_value = mock_client

        client = ReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        instance = Instance(client, "customer_123", "instance_123")

        # Send a metric
        instance.send_metric("test_metric", 42)

        # Verify the request was made with correct headers
        call_args = mock_client.request.call_args
        headers = call_args[1]["headers"]
        assert "X-Replicated-ClusterID" in headers
        assert headers["X-Replicated-ClusterID"] == client._machine_id


class TestAsyncReplicatedClient:
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        client = AsyncReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        assert client.publishable_key == "pk_test_123"
        assert client.app_slug == "my-app"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with AsyncReplicatedClient(
            publishable_key="pk_test_123", app_slug="my-app"
        ) as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_custom_state_directory(self):
        """Test async client with custom state directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_state"
            client = AsyncReplicatedClient(
                publishable_key="pk_test_123",
                app_slug="my-app",
                state_directory=str(custom_dir),
            )
            # Resolve both paths to handle symlinks
            # (e.g., /var vs /private/var on macOS)
            assert client.state_manager._state_dir == custom_dir.resolve()
            expected_file = custom_dir.resolve() / "state.json"
            assert client.state_manager._state_file == expected_file
            assert custom_dir.exists()

    @pytest.mark.asyncio
    async def test_custom_state_directory_with_tilde(self):
        """Test that ~ expansion works in async client custom state directory."""
        client = AsyncReplicatedClient(
            publishable_key="pk_test_123",
            app_slug="my-app",
            state_directory="~/test-replicated-state",
        )
        # Should be expanded to actual home directory
        assert "~" not in str(client.state_manager._state_dir)
        assert str(client.state_manager._state_dir).startswith(str(Path.home()))

    @pytest.mark.asyncio
    async def test_custom_state_directory_relative_path(self):
        """Test that relative paths are resolved in async client."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory and use relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                client = AsyncReplicatedClient(
                    publishable_key="pk_test_123",
                    app_slug="my-app",
                    state_directory="./relative_state",
                )
                # Should be resolved to absolute path
                assert client.state_manager._state_dir.is_absolute()
                assert str(tmpdir) in str(client.state_manager._state_dir)
            finally:
                os.chdir(original_cwd)

    @pytest.mark.asyncio
    async def test_default_state_directory_unchanged(self):
        """Test that async client default behavior is unchanged."""
        client = AsyncReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        state_dir_str = str(client.state_manager._state_dir)
        assert "my-app" in state_dir_str
        assert "Replicated" in state_dir_str

    @pytest.mark.asyncio
    async def test_client_has_machine_id(self):
        """Test that async client initializes with a machine_id."""
        client = AsyncReplicatedClient(publishable_key="pk_test_123", app_slug="my-app")
        assert hasattr(client, "_machine_id")
        assert client._machine_id is not None
        assert isinstance(client._machine_id, str)
        assert len(client._machine_id) == 64  # SHA256 hash

    @pytest.mark.asyncio
    async def test_instance_has_machine_id_from_client(self):
        """Test that async instances have the client's machine_id."""
        from replicated.resources import AsyncInstance

        with patch("replicated.http_client.httpx.AsyncClient") as mock_httpx:
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.json.return_value = {
                "customer": {
                    "id": "customer_123",
                    "email": "test@example.com",
                    "name": "test user",
                    "serviceToken": "service_token_123",
                    "instanceId": "instance_123",
                }
            }

            mock_client = Mock()
            mock_client.request.return_value = mock_response
            mock_httpx.return_value = mock_client

            client = AsyncReplicatedClient(
                publishable_key="pk_test_123", app_slug="my-app"
            )
            customer = await client.customer.get_or_create("test@example.com")
            instance = await customer.get_or_create_instance()

            assert isinstance(instance, AsyncInstance)
            assert hasattr(instance, "_machine_id")
            assert instance._machine_id == client._machine_id

    @pytest.mark.asyncio
    async def test_instance_uses_machine_id_in_headers(self):
        """Test that async instance methods use machine_id as cluster ID in headers."""
        from unittest.mock import AsyncMock

        from replicated.resources import AsyncInstance

        with patch("replicated.http_client.httpx.AsyncClient") as mock_httpx:
            mock_response = Mock()
            mock_response.is_success = True
            mock_response.json.return_value = {}

            mock_client = Mock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_client

            client = AsyncReplicatedClient(
                publishable_key="pk_test_123", app_slug="my-app"
            )
            instance = AsyncInstance(client, "customer_123", "instance_123")

            # Send a metric
            await instance.send_metric("test_metric", 42)

            # Verify the request was made with correct headers
            call_args = mock_client.request.call_args
            headers = call_args[1]["headers"]
            assert "X-Replicated-ClusterID" in headers
            assert headers["X-Replicated-ClusterID"] == client._machine_id
