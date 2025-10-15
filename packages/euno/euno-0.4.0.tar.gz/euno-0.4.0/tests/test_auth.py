"""
Test cases for the Euno SDK authentication and configuration functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner

from euno.auth import init_command, status_command, logout_command
from euno.config import EunoConfig
from euno.api import EunoAPIClient


class TestEunoConfig:
    """Test cases for configuration management."""

    def test_get_backend_url_default(self):
        """Test default backend URL."""
        with patch.dict(os.environ, {}, clear=True):
            config = EunoConfig()
            assert config.get_backend_url() == "https://api.app.euno.ai"

    def test_get_backend_url_from_env(self):
        """Test backend URL from environment variable."""
        with patch.dict(os.environ, {"EUNO_BACKEND": "https://custom.euno.ai"}):
            config = EunoConfig()
            assert config.get_backend_url() == "https://custom.euno.ai"

    def test_get_backend_url_from_config(self):
        """Test backend URL from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Write config with backend URL
            config_data = {"backend_url": "https://config.euno.ai"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Test without environment variable
            with patch.dict(os.environ, {}, clear=True):
                assert test_config.get_backend_url() == "https://config.euno.ai"

    def test_set_backend_url(self):
        """Test setting backend URL in config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Set backend URL
            test_config.set_backend_url("https://custom.euno.ai")

            # Verify it was saved
            with open(config_file, "r") as f:
                config_data = json.load(f)
                assert config_data["backend_url"] == "https://custom.euno.ai"

    def test_get_token_from_env(self):
        """Test token retrieval from environment variable."""
        with patch.dict(os.environ, {"EUNO_TOKEN": "env-token-123"}):
            config = EunoConfig()
            assert config.get_token() == "env-token-123"
            assert config.is_configured()

    def test_get_token_from_config(self):
        """Test token retrieval from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Write config with token
            config_data = {"token": "config-token-123"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Test without environment variable
            with patch.dict(os.environ, {}, clear=True):
                assert test_config.get_token() == "config-token-123"
                assert test_config.is_configured()

    def test_token_env_overrides_config(self):
        """Test that environment variable overrides config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Write config with token
            config_data = {"token": "config-token-123"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Test with environment variable (should override config)
            with patch.dict(os.environ, {"EUNO_TOKEN": "env-token-456"}):
                assert test_config.get_token() == "env-token-456"
                assert test_config.is_configured()

    def test_get_account_id_from_env(self):
        """Test account ID retrieval from environment variable."""
        with patch.dict(os.environ, {"EUNO_ACCOUNT": "env-account-123"}):
            config = EunoConfig()
            assert config.get_account_id() == "env-account-123"

    def test_get_account_id_from_config(self):
        """Test account ID retrieval from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Write config with account ID
            config_data = {"account_id": "config-account-123"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Test without environment variable
            with patch.dict(os.environ, {}, clear=True):
                assert test_config.get_account_id() == "config-account-123"

    def test_account_id_env_overrides_config(self):
        """Test that environment variable overrides config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Write config with account ID
            config_data = {"account_id": "config-account-123"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Test with environment variable (should override config)
            with patch.dict(os.environ, {"EUNO_ACCOUNT": "env-account-456"}):
                assert test_config.get_account_id() == "env-account-456"

    def test_set_account_id(self):
        """Test setting account ID in config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Set account ID
            test_config.set_account_id("test-account-123")

            # Verify it was saved
            with open(config_file, "r") as f:
                config_data = json.load(f)
                assert config_data["account_id"] == "test-account-123"

    def test_token_storage(self):
        """Test token storage and retrieval."""
        # Create a temporary config instance for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Initially no token
            assert test_config.get_token() is None
            assert not test_config.is_configured()

            # Set token
            test_config.set_token("test-token-123")
            assert test_config.get_token() == "test-token-123"
            assert test_config.is_configured()

            # Clear token
            test_config.clear_token()
            assert test_config.get_token() is None
            assert not test_config.is_configured()

    def test_generic_get_set_methods(self):
        """Test the generic get/set methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / ".euno"
            config_file = config_dir / "config.json"

            # Create a test config instance
            test_config = EunoConfig()
            test_config.config_dir = config_dir
            test_config.config_file = config_file

            # Ensure the config directory exists
            config_dir.mkdir(exist_ok=True)

            # Test generic get/set for all config keys
            test_config.set("backend_url", "https://test.euno.ai")
            test_config.set("token", "test-token-456")
            test_config.set("account_id", "test-account-789")

            assert test_config.get("backend_url") == "https://test.euno.ai"
            assert test_config.get("token") == "test-token-456"
            assert test_config.get("account_id") == "test-account-789"

            # Test clear method
            test_config.clear("token")
            assert test_config.get("token") is None

            # Test invalid key
            with pytest.raises(ValueError, match="Unknown configuration key"):
                test_config.get("invalid_key")

            with pytest.raises(ValueError, match="Unknown configuration key"):
                test_config.set("invalid_key", "value")


class TestEunoAPIClient:
    """Test cases for API client."""

    def test_init_default_backend(self):
        """Test API client initialization with default backend."""
        client = EunoAPIClient()
        assert client.backend_url == "https://api.app.euno.ai"

    def test_init_custom_backend(self):
        """Test API client initialization with custom backend."""
        client = EunoAPIClient("https://custom.euno.ai")
        assert client.backend_url == "https://custom.euno.ai"

    def test_get_headers(self):
        """Test header generation."""
        client = EunoAPIClient()
        headers = client._get_headers("test-token")

        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"
        assert "euno-sdk" in headers["User-Agent"]

    @patch("requests.Session.get")
    def test_validate_token_success(self, mock_get):
        """Test successful token validation."""
        mock_response = Mock()
        mock_response.json.return_value = {"email": "test@example.com", "id": "123"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = EunoAPIClient()
        result = client.validate_token("valid-token")

        assert result["email"] == "test@example.com"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_validate_token_failure(self, mock_get):
        """Test token validation failure."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_get.return_value = mock_response

        client = EunoAPIClient()

        with pytest.raises(Exception):
            client.validate_token("invalid-token")

    @patch("requests.Session.get")
    def test_get_account_permissions_success(self, mock_get):
        """Test successful account permissions retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"permission": "read"},
            {"permission": "write"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = EunoAPIClient()
        result = client.get_account_permissions("valid-token", "account-123")

        assert len(result) == 2
        assert result[0]["permission"] == "read"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_get_account_permissions_failure(self, mock_get):
        """Test account permissions retrieval failure."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Forbidden")
        mock_get.return_value = mock_response

        client = EunoAPIClient()

        with pytest.raises(Exception):
            client.get_account_permissions("invalid-token", "account-123")


class TestAuthCommands:
    """Test cases for authentication commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("euno.auth.config")
    @patch("euno.auth.api_client")
    def test_init_command_success(self, mock_api_client, mock_config):
        """Test successful init command."""
        mock_config.is_configured.return_value = False
        mock_config.get_backend_url.return_value = "https://api.app.euno.ai"

        mock_client = Mock()
        mock_client.validate_token.return_value = {"email": "test@example.com"}
        mock_api_client.__class__.return_value = mock_client

        # Test the function directly instead of using CliRunner
        with patch("click.prompt") as mock_prompt, patch("click.confirm") as mock_confirm, patch("click.echo"):
            # Mock prompt to return token first, then account ID
            mock_prompt.side_effect = ["test-token", "test-account-123"]
            mock_confirm.return_value = False

            init_command()

            mock_config.set_token.assert_called_once_with("test-token")
            mock_config.set_account_id.assert_called_once_with("test-account-123")

    @patch("euno.auth.config")
    def test_status_command_not_configured(self, mock_config):
        """Test status command when not configured."""
        mock_config.is_configured.return_value = False

        with patch("click.echo") as mock_echo:
            status_command()

            # Check that appropriate messages were echoed
            echo_calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("not configured" in call for call in echo_calls)

    @patch("euno.auth.config")
    @patch("euno.auth.api_client")
    def test_status_command_configured(self, mock_api_client, mock_config):
        """Test status command when configured."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = "test-token-123"
        mock_config.get_backend_url.return_value = "https://api.app.euno.ai"
        mock_config.get_account_id.return_value = "test-account-123"

        mock_api_client.validate_token.return_value = {"email": "test@example.com"}
        mock_api_client.get_account_permissions.return_value = [{"permission": "read"}]

        with patch("click.echo") as mock_echo:
            status_command()

            # Check that appropriate messages were echoed
            echo_calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("configured" in call for call in echo_calls)
            assert any("test@example.com" in call for call in echo_calls)
            assert any("test-account-123" in call for call in echo_calls)
            assert any("Account permissions: OK" in call for call in echo_calls)

    @patch("euno.auth.config")
    @patch("euno.auth.api_client")
    def test_status_command_no_permissions(self, mock_api_client, mock_config):
        """Test status command when user has no account permissions."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = "test-token-123"
        mock_config.get_backend_url.return_value = "https://api.app.euno.ai"
        mock_config.get_account_id.return_value = "test-account-123"

        mock_api_client.validate_token.return_value = {"email": "test@example.com"}
        mock_api_client.get_account_permissions.return_value = []

        with patch("click.echo") as mock_echo:
            status_command()

            # Check that appropriate messages were echoed
            echo_calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("User has no role in the account" in call for call in echo_calls)

    @patch("euno.auth.config")
    @patch("euno.auth.api_client")
    def test_status_command_permissions_error(self, mock_api_client, mock_config):
        """Test status command when account permissions check fails."""
        mock_config.is_configured.return_value = True
        mock_config.get_token.return_value = "test-token-123"
        mock_config.get_backend_url.return_value = "https://api.app.euno.ai"
        mock_config.get_account_id.return_value = "test-account-123"

        mock_api_client.validate_token.return_value = {"email": "test@example.com"}
        mock_api_client.get_account_permissions.side_effect = Exception("Forbidden")

        with patch("click.echo") as mock_echo:
            status_command()

            # Check that appropriate messages were echoed
            echo_calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("User has no role in the account" in call for call in echo_calls)

    @patch("euno.auth.config")
    def test_logout_command(self, mock_config):
        """Test logout command."""
        mock_config.is_configured.return_value = True

        with patch("click.confirm") as mock_confirm, patch("click.echo"):
            mock_confirm.return_value = True

            logout_command()

            mock_config.clear_token.assert_called_once()
