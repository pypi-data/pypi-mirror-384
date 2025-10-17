"""Configuration provider for robot build and publish system.

This module manages configuration from multiple sources with proper priority:
1. CLI arguments (highest priority)
2. Environment variables
3. .env files
4. Cloud function (lowest priority)
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigProvider:
    """Provides configuration for robot build and publish operations.

    Configuration priority (highest to lowest):
    - CLI arguments (provided externally)
    - Environment variables
    - .env file
    - Cloud function response

    Args:
        env_file: Path to .env file (default: .env in current directory)
        local_test_mode: If True, skip cloud function validation
    """

    def __init__(
        self,
        env_file: Optional[Path] = None,
        local_test_mode: bool = False,
    ) -> None:
        """Initialize configuration provider."""
        self.env_file = env_file or Path(".env")
        self.local_test_mode = local_test_mode
        self._config: Dict[str, str] = {}

        # Load from .env file first (lowest priority)
        if self.env_file.exists():
            self._config.update(self.load_from_file(self.env_file))

        # Load from environment variables (higher priority)
        self._config.update(self.load_from_env())

    def load_from_env(self) -> Dict[str, str]:
        """Load configuration from environment variables.

        Returns:
            Dictionary of configuration values found in environment
        """
        config = {}

        # Required configuration
        if appkey := os.getenv("ROBOT_APPKEY"):
            config["robot_appkey"] = appkey

        if cloud_url := os.getenv("CLOUD_FUNCTION_URL"):
            config["cloud_function_url"] = cloud_url

        # Optional configuration (for local testing)
        if registry_url := os.getenv("REGISTRY_URL"):
            config["registry_url"] = registry_url

        if registry_username := os.getenv("REGISTRY_USERNAME"):
            config["registry_username"] = registry_username

        if registry_password := os.getenv("REGISTRY_PASSWORD"):
            config["registry_password"] = registry_password

        if node_server_url := os.getenv("NODE_SERVER_URL"):
            config["node_server_url"] = node_server_url

        if node_server_token := os.getenv("NODE_SERVER_TOKEN"):
            config["node_server_token"] = node_server_token

        return config

    def load_from_file(self, filepath: Path) -> Dict[str, str]:
        """Load configuration from .env file.

        Args:
            filepath: Path to .env file

        Returns:
            Dictionary of configuration values from file
        """
        config = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE format
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # Map to internal config keys (lowercase with underscores)
                        if key in [
                            "ROBOT_APPKEY",
                            "CLOUD_FUNCTION_URL",
                            "REGISTRY_URL",
                            "REGISTRY_USERNAME",
                            "REGISTRY_PASSWORD",
                            "NODE_SERVER_URL",
                            "NODE_SERVER_TOKEN",
                        ]:
                            config[key.lower()] = value
        except Exception as e:
            # Silently ignore file read errors (file might not exist)
            pass

        return config

    def get_robot_appkey(self) -> str:
        """Get robot appkey (required).

        Returns:
            Robot appkey

        Raises:
            ValueError: If appkey is not configured
        """
        if appkey := self._config.get("robot_appkey"):
            return appkey

        if self.local_test_mode:
            raise ValueError(
                "ROBOT_APPKEY is required even in local test mode. "
                "Please set ROBOT_APPKEY environment variable or add it to .env file."
            )

        raise ValueError(
            "ROBOT_APPKEY is not configured. "
            "Please set ROBOT_APPKEY environment variable or add it to .env file.\n"
            "Example: export ROBOT_APPKEY=your-appkey"
        )

    def get_cloud_function_url(self) -> Optional[str]:
        """Get cloud function base URL (optional if local config is available).

        Returns:
            Cloud function URL or None if not configured but local config is complete

        Raises:
            ValueError: If cloud function URL is not configured and local config is incomplete
        """
        if url := self._config.get("cloud_function_url"):
            return url

        # Check if local configuration is complete (direct registry/node-server config)
        if self._is_local_config_complete():
            return None  # Don't need cloud function

        if self.local_test_mode:
            # Return a dummy URL for local testing
            return "http://localhost:8080"

        raise ValueError(
            "CLOUD_FUNCTION_URL is not configured and local configuration is incomplete.\n"
            "Please either:\n"
            "  1. Set CLOUD_FUNCTION_URL environment variable, or\n"
            "  2. Configure REGISTRY_URL, REGISTRY_USERNAME, REGISTRY_PASSWORD directly\n"
            "Example: export CLOUD_FUNCTION_URL=http://api.example.com"
        )

    def _is_local_config_complete(self) -> bool:
        """Check if local configuration has all required deploy parameters.

        Returns:
            True if all registry and node server configs are available locally
        """
        has_registry = all([
            self._config.get("registry_url"),
            self._config.get("registry_username"),
            self._config.get("registry_password"),
        ])
        has_robot_appkey = self._config.get("robot_appkey")
        return has_registry and has_robot_appkey

    def get_registry_url(self) -> Optional[str]:
        """Get registry URL (optional, from cloud function or local config).

        Returns:
            Registry URL or None if not configured
        """
        return self._config.get("registry_url")

    def get_registry_username(self) -> Optional[str]:
        """Get registry username (optional).

        Returns:
            Registry username or None if not configured
        """
        return self._config.get("registry_username")

    def get_registry_password(self) -> Optional[str]:
        """Get registry password (optional).

        Returns:
            Registry password or None if not configured
        """
        return self._config.get("registry_password")

    def get_node_server_url(self) -> Optional[str]:
        """Get node server URL (optional).

        Returns:
            Node server URL or None if not configured
        """
        return self._config.get("node_server_url")

    def get_node_server_token(self) -> Optional[str]:
        """Get node server authentication token (optional).

        Returns:
            Node server token or None if not configured
        """
        return self._config.get("node_server_token")

    def update_from_cloud(self, cloud_config: Dict[str, Any]) -> None:
        """Update configuration from cloud function response.

        This is called after fetching deploy config from cloud function.
        Cloud config has lowest priority and won't override existing config.

        Args:
            cloud_config: Configuration dictionary from cloud function
        """
        # Extract registry config
        if registry := cloud_config.get("registry"):
            if "url" in registry and "registry_url" not in self._config:
                self._config["registry_url"] = registry["url"]
            if "username" in registry and "registry_username" not in self._config:
                self._config["registry_username"] = registry["username"]
            if "password" in registry and "registry_password" not in self._config:
                self._config["registry_password"] = registry["password"]

        # Extract node server config
        if node_server := cloud_config.get("node_server"):
            if "url" in node_server and "node_server_url" not in self._config:
                self._config["node_server_url"] = node_server["url"]
            if "token" in node_server and "node_server_token" not in self._config:
                self._config["node_server_token"] = node_server["token"]

    def validate_publish_config(self) -> None:
        """Validate that all required configuration for publish is available.

        Raises:
            ValueError: If required configuration is missing
        """
        missing = []

        # Check required config
        if not self._config.get("robot_appkey"):
            missing.append("ROBOT_APPKEY")

        # Check registry config
        if not self._config.get("registry_url"):
            missing.append("REGISTRY_URL")
        if not self._config.get("registry_username"):
            missing.append("REGISTRY_USERNAME")
        if not self._config.get("registry_password"):
            missing.append("REGISTRY_PASSWORD")

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                "Please configure these values in environment variables, .env file, "
                "or ensure cloud function returns them.\n"
                "Contact your administrator if cloud function configuration is incomplete."
            )

    def get_all_config(self) -> Dict[str, str]:
        """Get all configuration (for debugging).

        Note: Sensitive values (passwords, tokens) are masked.

        Returns:
            Dictionary of all configuration with masked sensitive values
        """
        config = self._config.copy()

        # Mask sensitive values
        if "registry_password" in config:
            config["registry_password"] = "●●●●●●"
        if "node_server_token" in config:
            config["node_server_token"] = "●●●●●●"

        return config
