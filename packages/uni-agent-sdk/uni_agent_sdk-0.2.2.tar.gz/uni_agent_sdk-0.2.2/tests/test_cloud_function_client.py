"""Tests for CloudFunctionClient."""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from uni_agent_sdk.build_system.cloud_function_client import (
    AuthenticationError,
    CloudFunctionClient,
    CloudFunctionError,
    ConfigurationError,
    NetworkError,
)


class TestCloudFunctionClient:
    """Test CloudFunctionClient functionality."""

    @pytest.fixture
    def mock_response(self) -> Mock:
        """Create a mock HTTP response."""
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.text = ""
        return response

    @pytest.fixture
    def valid_deploy_config(self) -> Dict[str, Any]:
        """Create valid deployment configuration."""
        return {
            "errCode": 0,
            "errMsg": "success",
            "data": {
                "robot_id": "robot-12345",
                "registry": {
                    "url": "registry.example.com:5000",
                    "username": "admin",
                    "password": "password123",
                    "namespace": "robots",
                },
                "node_server": {
                    "url": "http://node.example.com:8000",
                    "token": "bearer-token",
                },
                "config": {"max_retries": 3, "retry_delay_seconds": 5},
            },
        }

    @pytest.mark.asyncio
    async def test_get_deploy_config_success(
        self, mock_response: Mock, valid_deploy_config: Dict[str, Any]
    ) -> None:
        """Test successful deployment configuration retrieval."""
        mock_response.json.return_value = valid_deploy_config

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            result = await client.get_deploy_config("test-appkey")

            assert result["robot_id"] == "robot-12345"
            assert result["registry"]["url"] == "registry.example.com:5000"
            assert result["registry"]["username"] == "admin"
            assert result["registry"]["password"] == "password123"
            assert result["node_server"]["url"] == "http://node.example.com:8000"
            assert result["node_server"]["token"] == "bearer-token"

            # Verify request was made correctly
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://api.test.com/api/robot/deploy-config"
            assert call_args[1]["headers"]["X-Robot-AppKey"] == "test-appkey"

    @pytest.mark.asyncio
    async def test_get_deploy_config_authentication_error(
        self, mock_response: Mock
    ) -> None:
        """Test authentication error (401) raises AuthenticationError."""
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with pytest.raises(AuthenticationError) as exc_info:
                await client.get_deploy_config("invalid-appkey")

            assert "Authentication failed" in str(exc_info.value)
            assert "ROBOT_APPKEY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_deploy_config_network_error_retry(
        self, mock_response: Mock, valid_deploy_config: Dict[str, Any]
    ) -> None:
        """Test network error triggers retry and eventually succeeds."""
        mock_response.json.return_value = valid_deploy_config

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # First two attempts fail with network error, third succeeds
            mock_client.get = AsyncMock(
                side_effect=[
                    httpx.ConnectError("Connection refused"),
                    httpx.TimeoutException("Timeout"),
                    mock_response,
                ]
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com", max_retries=3)

            # Mock sleep to speed up test
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.get_deploy_config("test-appkey")

            assert result["robot_id"] == "robot-12345"
            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_get_deploy_config_network_error_exhausted(self) -> None:
        """Test network error raises NetworkError after all retries exhausted."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com", max_retries=3)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(NetworkError) as exc_info:
                    await client.get_deploy_config("test-appkey")

            assert "Network error after 3 attempts" in str(exc_info.value)
            assert "Connection refused" in str(exc_info.value)
            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_get_deploy_config_server_error_retry(
        self, mock_response: Mock, valid_deploy_config: Dict[str, Any]
    ) -> None:
        """Test server error (5xx) triggers retry."""
        server_error_response = Mock(spec=httpx.Response)
        server_error_response.status_code = 500

        success_response = Mock(spec=httpx.Response)
        success_response.status_code = 200
        success_response.json.return_value = valid_deploy_config

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=[server_error_response, success_response]
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.get_deploy_config("test-appkey")

            assert result["robot_id"] == "robot-12345"
            assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_get_deploy_config_incomplete_config(
        self, mock_response: Mock
    ) -> None:
        """Test incomplete configuration raises ConfigurationError."""
        incomplete_config = {
            "errCode": 0,
            "errMsg": "success",
            "data": {
                "robot_id": "robot-12345",
                "registry": {
                    "url": "registry.example.com:5000",
                    # Missing username and password
                },
            },
        }
        mock_response.json.return_value = incomplete_config

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with pytest.raises(ConfigurationError) as exc_info:
                await client.get_deploy_config("test-appkey")

            assert "incomplete configuration" in str(exc_info.value)
            assert "registry.username" in str(exc_info.value)
            assert "registry.password" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_deploy_config_cloud_function_error(
        self, mock_response: Mock
    ) -> None:
        """Test cloud function error response."""
        error_response = {
            "errCode": 1001,
            "errMsg": "Robot not found",
            "data": {},
        }
        mock_response.json.return_value = error_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with pytest.raises(CloudFunctionError) as exc_info:
                await client.get_deploy_config("test-appkey")

            assert "Robot not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_deploy_config_timeout(self) -> None:
        """Test timeout error triggers retry."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(
                base_url="http://api.test.com", timeout=10.0, max_retries=3
            )

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(NetworkError) as exc_info:
                    await client.get_deploy_config("test-appkey")

            assert "Timeout" in str(exc_info.value)
            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_notify_deployment_success(self, mock_response: Mock) -> None:
        """Test successful deployment notification."""
        mock_response.json.return_value = {
            "code": 0,
            "message": "Deployment notification received",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            deployment_data = {
                "image": "registry.example.com/robots/test:1.0.0",
                "version": "1.0.0",
                "status": "deploying",
            }

            result = await client.notify_deployment("robot-12345", deployment_data)

            assert result["code"] == 0
            assert result["message"] == "Deployment notification received"

            # Verify request
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://api.test.com/api/robot/deployment-notify"
            assert call_args[1]["json"]["robot_id"] == "robot-12345"
            assert (
                call_args[1]["json"]["image"]
                == "registry.example.com/robots/test:1.0.0"
            )

    @pytest.mark.asyncio
    async def test_notify_deployment_authentication_error(
        self, mock_response: Mock
    ) -> None:
        """Test deployment notification authentication error."""
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with pytest.raises(AuthenticationError):
                await client.notify_deployment("robot-12345", {})

    @pytest.mark.asyncio
    async def test_notify_deployment_network_error_retry(
        self, mock_response: Mock
    ) -> None:
        """Test deployment notification retries on network error."""
        mock_response.json.return_value = {"code": 0, "message": "Success"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[
                    httpx.ConnectError("Connection refused"),
                    mock_response,
                ]
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await client.notify_deployment("robot-12345", {})

            assert result["code"] == 0
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_context_manager(self, valid_deploy_config: Dict[str, Any]) -> None:
        """Test using CloudFunctionClient as context manager."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = valid_deploy_config

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            async with CloudFunctionClient(base_url="http://api.test.com") as client:
                result = await client.get_deploy_config("test-appkey")
                assert result["robot_id"] == "robot-12345"

            # Verify client was closed
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_response: Mock) -> None:
        """Test exponential backoff timing."""
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com", max_retries=3)

            sleep_times = []

            async def mock_sleep(delay: float) -> None:
                sleep_times.append(delay)

            with patch("asyncio.sleep", side_effect=mock_sleep):
                with pytest.raises(CloudFunctionError):
                    await client.get_deploy_config("test-appkey")

            # Verify exponential backoff: 2^0=1s, 2^1=2s
            assert len(sleep_times) == 2
            assert sleep_times[0] == 1  # 2^0
            assert sleep_times[1] == 2  # 2^1

    @pytest.mark.asyncio
    async def test_base_url_trailing_slash(
        self, mock_response: Mock, valid_deploy_config: Dict[str, Any]
    ) -> None:
        """Test base URL trailing slash is handled correctly."""
        mock_response.json.return_value = valid_deploy_config

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Test with trailing slash
            client = CloudFunctionClient(base_url="http://api.test.com/")
            await client.get_deploy_config("test-appkey")

            call_args = mock_client.get.call_args
            # Should not have double slash
            assert call_args[0][0] == "http://api.test.com/api/robot/deploy-config"

    @pytest.mark.asyncio
    async def test_client_error_4xx_no_retry(self, mock_response: Mock) -> None:
        """Test that 4xx errors (except 401) don't retry."""
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = CloudFunctionClient(base_url="http://api.test.com")

            with pytest.raises(CloudFunctionError) as exc_info:
                await client.get_deploy_config("test-appkey")

            # Should fail immediately without retry
            assert mock_client.get.call_count == 1
            assert "400" in str(exc_info.value)
