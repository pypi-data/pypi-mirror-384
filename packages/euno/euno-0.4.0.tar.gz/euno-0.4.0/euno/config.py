"""
Configuration management for the Euno SDK.

This module handles storing and retrieving user configuration including
API tokens, backend URLs, and account IDs.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class EunoConfig:
    """Manages Euno SDK configuration."""

    # Configuration key mappings: config_key -> (env_var_name, default_value)
    CONFIG_MAPPINGS = {
        "backend_url": ("EUNO_BACKEND", "https://api.app.euno.ai"),
        "token": ("EUNO_TOKEN", None),
        "account_id": ("EUNO_ACCOUNT", None),
    }

    def __init__(self):
        self.config_dir = Path.home() / ".euno"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self.config_dir.mkdir(exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, KeyError):
            return {}

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get(self, key: str) -> Optional[str]:
        """
        Get a configuration value,
        prioritizing environment variable over config file.
        """
        if key not in self.CONFIG_MAPPINGS:
            raise ValueError(f"Unknown configuration key: {key}")

        env_var_name, default_value = self.CONFIG_MAPPINGS[key]

        # First check environment variable
        env_value = os.getenv(env_var_name)
        if env_value:
            return env_value

        # Then check config file
        config = self._load_config()
        return config.get(key, default_value)

    def set(self, key: str, value: str) -> None:
        """Set a configuration value in the config file."""
        if key not in self.CONFIG_MAPPINGS:
            raise ValueError(f"Unknown configuration key: {key}")

        config = self._load_config()
        config[key] = value
        self._save_config(config)

    def clear(self, key: str) -> None:
        """Remove a configuration value from the config file."""
        if key not in self.CONFIG_MAPPINGS:
            raise ValueError(f"Unknown configuration key: {key}")

        config = self._load_config()
        config.pop(key, None)
        self._save_config(config)

    # Convenience methods for backward compatibility
    def get_backend_url(self) -> str:
        """Get the Euno backend URL."""
        result = self.get("backend_url")
        return result if result is not None else "https://api.app.euno.ai"

    def set_backend_url(self, backend_url: str) -> None:
        """Store the backend URL in config file."""
        self.set("backend_url", backend_url)

    def get_account_id(self) -> Optional[str]:
        """Get the stored account ID."""
        return self.get("account_id")

    def set_account_id(self, account_id: str) -> None:
        """Store the account ID in config file."""
        self.set("account_id", account_id)

    def get_token(self) -> Optional[str]:
        """Get the stored API token."""
        return self.get("token")

    def set_token(self, token: str) -> None:
        """Store the API token."""
        self.set("token", token)

    def clear_token(self) -> None:
        """Remove the stored API token."""
        self.clear("token")

    def is_configured(self) -> bool:
        """Check if the SDK is configured with a token."""
        return self.get_token() is not None


# Global config instance
config = EunoConfig()
