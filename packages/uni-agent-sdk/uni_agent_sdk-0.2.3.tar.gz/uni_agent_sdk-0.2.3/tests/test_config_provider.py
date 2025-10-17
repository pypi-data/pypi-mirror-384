"""Tests for ConfigProvider."""

import os
import tempfile
from pathlib import Path

import pytest

from uni_agent_sdk.build_system.config_provider import ConfigProvider


class TestConfigProvider:
    """Test ConfigProvider functionality."""

    def test_load_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")
        monkeypatch.setenv("CLOUD_FUNCTION_URL", "http://api.test.com")
        monkeypatch.setenv("REGISTRY_URL", "registry.test.com:5000")
        monkeypatch.setenv("REGISTRY_USERNAME", "admin")
        monkeypatch.setenv("REGISTRY_PASSWORD", "password123")
        monkeypatch.setenv("NODE_SERVER_URL", "http://node.test.com")
        monkeypatch.setenv("NODE_SERVER_TOKEN", "token123")

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        assert config.get_robot_appkey() == "test-appkey"
        assert config.get_cloud_function_url() == "http://api.test.com"
        assert config.get_registry_url() == "registry.test.com:5000"
        assert config.get_registry_username() == "admin"
        assert config.get_registry_password() == "password123"
        assert config.get_node_server_url() == "http://node.test.com"
        assert config.get_node_server_token() == "token123"

    def test_load_from_file(self, tmp_path):
        """Test loading configuration from .env file."""
        env_file = tmp_path / ".env"
        env_content = """
# Configuration file
ROBOT_APPKEY=file-appkey
CLOUD_FUNCTION_URL=http://api.file.com
REGISTRY_URL=registry.file.com:5000
REGISTRY_USERNAME="file-user"
REGISTRY_PASSWORD='file-pass'
NODE_SERVER_URL=http://node.file.com
NODE_SERVER_TOKEN=file-token

# Comment line
INVALID_LINE_WITHOUT_EQUALS
"""
        env_file.write_text(env_content)

        config = ConfigProvider(env_file=env_file)

        assert config.get_robot_appkey() == "file-appkey"
        assert config.get_cloud_function_url() == "http://api.file.com"
        assert config.get_registry_url() == "registry.file.com:5000"
        assert config.get_registry_username() == "file-user"
        assert config.get_registry_password() == "file-pass"
        assert config.get_node_server_url() == "http://node.file.com"
        assert config.get_node_server_token() == "file-token"

    def test_config_priority(self, tmp_path, monkeypatch):
        """Test that environment variables override .env file."""
        # Create .env file with lower priority values
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
ROBOT_APPKEY=file-appkey
CLOUD_FUNCTION_URL=http://api.file.com
REGISTRY_URL=registry.file.com:5000
"""
        )

        # Set environment variables (higher priority)
        monkeypatch.setenv("ROBOT_APPKEY", "env-appkey")
        monkeypatch.setenv("CLOUD_FUNCTION_URL", "http://api.env.com")

        config = ConfigProvider(env_file=env_file)

        # Environment variables should override .env file
        assert config.get_robot_appkey() == "env-appkey"
        assert config.get_cloud_function_url() == "http://api.env.com"

        # Values only in .env file should still be available
        assert config.get_registry_url() == "registry.file.com:5000"

    def test_missing_required_config(self):
        """Test error when required config is missing."""
        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        with pytest.raises(ValueError) as exc_info:
            config.get_robot_appkey()

        assert "ROBOT_APPKEY" in str(exc_info.value)
        assert "not configured" in str(exc_info.value)

    def test_missing_cloud_function_url(self):
        """Test error when cloud function URL is missing."""
        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        with pytest.raises(ValueError) as exc_info:
            config.get_cloud_function_url()

        assert "CLOUD_FUNCTION_URL" in str(exc_info.value)

    def test_local_test_mode(self, monkeypatch):
        """Test local test mode behavior."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")

        config = ConfigProvider(
            env_file=Path("/nonexistent/.env"), local_test_mode=True
        )

        # Should still require appkey
        assert config.get_robot_appkey() == "test-appkey"

        # Should return dummy URL instead of raising error
        assert config.get_cloud_function_url() == "http://localhost:8080"

    def test_local_test_mode_missing_appkey(self):
        """Test that appkey is still required in local test mode."""
        config = ConfigProvider(
            env_file=Path("/nonexistent/.env"), local_test_mode=True
        )

        with pytest.raises(ValueError) as exc_info:
            config.get_robot_appkey()

        assert "ROBOT_APPKEY" in str(exc_info.value)
        assert "local test mode" in str(exc_info.value)

    def test_optional_config_returns_none(self):
        """Test that optional config returns None when not set."""
        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        assert config.get_registry_url() is None
        assert config.get_registry_username() is None
        assert config.get_registry_password() is None
        assert config.get_node_server_url() is None
        assert config.get_node_server_token() is None

    def test_update_from_cloud(self, monkeypatch):
        """Test updating configuration from cloud function response."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")
        monkeypatch.setenv("REGISTRY_URL", "local-registry.com")  # Local override

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        # Simulate cloud function response
        cloud_config = {
            "robot_id": "robot-12345",
            "registry": {
                "url": "cloud-registry.com:5000",
                "username": "cloud-user",
                "password": "cloud-pass",
            },
            "node_server": {
                "url": "http://node.cloud.com",
                "token": "cloud-token",
            },
        }

        config.update_from_cloud(cloud_config)

        # Local config should take precedence
        assert config.get_registry_url() == "local-registry.com"

        # Cloud config should fill in missing values
        assert config.get_registry_username() == "cloud-user"
        assert config.get_registry_password() == "cloud-pass"
        assert config.get_node_server_url() == "http://node.cloud.com"
        assert config.get_node_server_token() == "cloud-token"

    def test_validate_publish_config_success(self, monkeypatch):
        """Test validation passes when all required config is present."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")
        monkeypatch.setenv("REGISTRY_URL", "registry.test.com")
        monkeypatch.setenv("REGISTRY_USERNAME", "admin")
        monkeypatch.setenv("REGISTRY_PASSWORD", "password")

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        # Should not raise error
        config.validate_publish_config()

    def test_validate_publish_config_missing(self):
        """Test validation fails when required config is missing."""
        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        with pytest.raises(ValueError) as exc_info:
            config.validate_publish_config()

        error_msg = str(exc_info.value)
        assert "ROBOT_APPKEY" in error_msg
        assert "REGISTRY_URL" in error_msg
        assert "REGISTRY_USERNAME" in error_msg
        assert "REGISTRY_PASSWORD" in error_msg

    def test_validate_publish_config_partial(self, monkeypatch):
        """Test validation fails when only some required config is present."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")
        monkeypatch.setenv("REGISTRY_URL", "registry.test.com")

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        with pytest.raises(ValueError) as exc_info:
            config.validate_publish_config()

        error_msg = str(exc_info.value)
        assert "ROBOT_APPKEY" not in error_msg  # This one is present
        assert "REGISTRY_URL" not in error_msg  # This one is present
        assert "REGISTRY_USERNAME" in error_msg
        assert "REGISTRY_PASSWORD" in error_msg

    def test_get_all_config_masks_sensitive(self, monkeypatch):
        """Test that sensitive values are masked in get_all_config."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")
        monkeypatch.setenv("REGISTRY_PASSWORD", "secret-password")
        monkeypatch.setenv("NODE_SERVER_TOKEN", "secret-token")

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        all_config = config.get_all_config()

        assert all_config["robot_appkey"] == "test-appkey"
        assert all_config["registry_password"] == "●●●●●●"
        assert all_config["node_server_token"] == "●●●●●●"

    def test_env_file_with_quotes(self, tmp_path):
        """Test parsing .env file with quoted values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
ROBOT_APPKEY="quoted-appkey"
REGISTRY_USERNAME='single-quoted'
REGISTRY_PASSWORD=no-quotes
"""
        )

        config = ConfigProvider(env_file=env_file)

        assert config.get_robot_appkey() == "quoted-appkey"
        assert config.get_registry_username() == "single-quoted"
        assert config.get_registry_password() == "no-quotes"

    def test_env_file_with_empty_lines(self, tmp_path):
        """Test parsing .env file with empty lines and comments."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
# Comment at the start

ROBOT_APPKEY=test-appkey

# Another comment
CLOUD_FUNCTION_URL=http://api.test.com

"""
        )

        config = ConfigProvider(env_file=env_file)

        assert config.get_robot_appkey() == "test-appkey"
        assert config.get_cloud_function_url() == "http://api.test.com"

    def test_nonexistent_env_file(self):
        """Test that nonexistent .env file is handled gracefully."""
        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        # Should not raise error, just have no config from file
        assert config.get_registry_url() is None

    def test_update_from_cloud_empty_config(self, monkeypatch):
        """Test updating from cloud with empty/partial config."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))

        # Empty cloud config
        config.update_from_cloud({})

        # Should still have no registry config
        assert config.get_registry_url() is None

        # Partial cloud config (missing some fields)
        cloud_config = {"registry": {"url": "registry.com"}}
        config.update_from_cloud(cloud_config)

        assert config.get_registry_url() == "registry.com"
        assert config.get_registry_username() is None

    def test_load_from_env_method(self, monkeypatch):
        """Test load_from_env method directly."""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey")
        monkeypatch.setenv("REGISTRY_URL", "registry.test.com")

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))
        env_config = config.load_from_env()

        assert env_config["robot_appkey"] == "test-appkey"
        assert env_config["registry_url"] == "registry.test.com"
        assert "registry_username" not in env_config  # Not set

    def test_load_from_file_method(self, tmp_path):
        """Test load_from_file method directly."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
ROBOT_APPKEY=file-appkey
CLOUD_FUNCTION_URL=http://api.file.com
"""
        )

        config = ConfigProvider(env_file=Path("/nonexistent/.env"))
        file_config = config.load_from_file(env_file)

        assert file_config["robot_appkey"] == "file-appkey"
        assert file_config["cloud_function_url"] == "http://api.file.com"

    def test_case_sensitivity(self, tmp_path):
        """Test that config keys are case-sensitive (uppercase in file)."""
        env_file = tmp_path / ".env"
        # Test with lowercase keys (should be ignored)
        env_file.write_text(
            """
ROBOT_APPKEY=correct-appkey
robot_appkey=wrong-appkey
Robot_AppKey=also-wrong
"""
        )

        config = ConfigProvider(env_file=env_file)

        # Should only pick up the uppercase version
        assert config.get_robot_appkey() == "correct-appkey"

    def test_config_with_special_characters(self, tmp_path):
        """Test config values with special characters."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
ROBOT_APPKEY=appkey-with-dashes-123
REGISTRY_PASSWORD="password=with=equals"
NODE_SERVER_URL=http://localhost:8000/api/v1
"""
        )

        config = ConfigProvider(env_file=env_file)

        assert config.get_robot_appkey() == "appkey-with-dashes-123"
        assert config.get_registry_password() == "password=with=equals"
        assert config.get_node_server_url() == "http://localhost:8000/api/v1"
