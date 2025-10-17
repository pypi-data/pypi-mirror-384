"""Cloud function client for robot build and publish system.

This module handles communication with cloud functions to retrieve
deployment configuration and notify deployment status.
"""

import asyncio
from typing import Any, Dict, Optional

import httpx


class CloudFunctionError(Exception):
    """Base exception for cloud function client errors."""

    pass


class AuthenticationError(CloudFunctionError):
    """Raised when authentication fails (401)."""

    pass


class NetworkError(CloudFunctionError):
    """Raised when network-related errors occur."""

    pass


class ConfigurationError(CloudFunctionError):
    """Raised when cloud function returns incomplete configuration."""

    pass


class CloudFunctionClient:
    """Client for communicating with cloud functions.

    This client handles:
    - Retrieving deployment configuration from cloud function
    - Notifying deployment status to cloud function
    - Automatic retry for network errors with exponential backoff

    Args:
        base_url: Cloud function base URL
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 3)
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize cloud function client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "CloudFunctionClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_deploy_config(self, appkey: str) -> Dict[str, Any]:
        """Get deployment configuration from cloud function.

        This method calls GET /api/robot/deploy-config with the robot appkey
        to retrieve registry credentials, node server information, and other
        deployment settings.

        Args:
            appkey: Robot appkey for authentication

        Returns:
            Deployment configuration dictionary with structure:
            {
                "robot_id": "robot-12345",
                "registry": {
                    "url": "registry.example.com:5000",
                    "username": "admin",
                    "password": "password123",
                    "namespace": "robots"  # optional
                },
                "node_server": {
                    "url": "http://node.example.com:8000",
                    "token": "bearer-token"
                },
                "config": {
                    "max_retries": 3,
                    "retry_delay_seconds": 5
                }
            }

        Raises:
            AuthenticationError: If appkey is invalid (401)
            NetworkError: If network error occurs after all retries
            ConfigurationError: If returned configuration is incomplete
            CloudFunctionError: For other errors
        """
        url = f"{self.base_url}/api/robot/deploy-config"
        headers = {"X-Robot-AppKey": appkey}

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                async with self._get_client() as client:
                    response = await client.get(url, headers=headers)

                    # Authentication error - don't retry
                    if response.status_code == 401:
                        raise AuthenticationError(
                            f"Authentication failed. Please check your ROBOT_APPKEY.\n"
                            f"URL: {url}\n"
                            f"Status: {response.status_code}"
                        )

                    # Server error - retry
                    if response.status_code >= 500:
                        error_msg = (
                            f"Server error (attempt {attempt + 1}/{self.max_retries})"
                        )
                        if attempt < self.max_retries - 1:
                            await self._wait_before_retry(attempt)
                            continue
                        raise CloudFunctionError(
                            f"Server error after {self.max_retries} attempts.\n"
                            f"URL: {url}\n"
                            f"Status: {response.status_code}"
                        )

                    # Client error (other than 401) - don't retry
                    if response.status_code >= 400:
                        raise CloudFunctionError(
                            f"Cloud function request failed.\n"
                            f"URL: {url}\n"
                            f"Status: {response.status_code}\n"
                            f"Response: {response.text}"
                        )

                    # Success - parse and validate response
                    response.raise_for_status()
                    data = response.json()

                    # Handle cloud function response format
                    if data.get("errCode") != 0:
                        raise CloudFunctionError(
                            f"Cloud function returned error: {data.get('errMsg', 'Unknown error')}"
                        )

                    config = data.get("data", {})
                    self._validate_deploy_config(config)

                    return config

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                # Network error - retry
                if attempt < self.max_retries - 1:
                    await self._wait_before_retry(attempt)
                    continue

                raise NetworkError(
                    f"Network error after {self.max_retries} attempts: {str(e)}\n"
                    f"URL: {url}\n"
                    f"Please check:\n"
                    f"  1. Cloud function URL is correct: {self.base_url}\n"
                    f"  2. Network connection is available\n"
                    f"  3. Cloud function service is running"
                ) from e

            except (AuthenticationError, ConfigurationError, CloudFunctionError):
                # Don't retry for these errors
                raise

            except Exception as e:
                # Unexpected error
                raise CloudFunctionError(
                    f"Unexpected error calling cloud function: {str(e)}"
                ) from e

        # Should not reach here, but just in case
        raise CloudFunctionError("Failed to get deploy config after all retries")

    async def notify_deployment(
        self, robot_id: str, deployment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Notify cloud function about deployment status.

        This is an optional method that can be called to inform the cloud
        function when a deployment starts or completes.

        Args:
            robot_id: Robot unique identifier
            deployment_data: Deployment information (image, version, status, etc.)

        Returns:
            Response from cloud function

        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If network error occurs after all retries
            CloudFunctionError: For other errors
        """
        url = f"{self.base_url}/api/robot/deployment-notify"

        payload = {"robot_id": robot_id, **deployment_data}

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                async with self._get_client() as client:
                    response = await client.post(url, json=payload)

                    # Authentication error - don't retry
                    if response.status_code == 401:
                        raise AuthenticationError(
                            "Authentication failed for deployment notification"
                        )

                    # Server error - retry
                    if response.status_code >= 500:
                        if attempt < self.max_retries - 1:
                            await self._wait_before_retry(attempt)
                            continue
                        raise CloudFunctionError(
                            f"Server error after {self.max_retries} attempts"
                        )

                    # Client error (other than 401) - don't retry
                    if response.status_code >= 400:
                        raise CloudFunctionError(
                            f"Deployment notification failed: {response.text}"
                        )

                    response.raise_for_status()
                    return response.json()

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                # Network error - retry
                if attempt < self.max_retries - 1:
                    await self._wait_before_retry(attempt)
                    continue

                raise NetworkError(
                    f"Network error after {self.max_retries} attempts: {str(e)}"
                ) from e

            except (AuthenticationError, CloudFunctionError):
                # Don't retry for these errors
                raise

            except Exception as e:
                # Unexpected error
                raise CloudFunctionError(
                    f"Unexpected error notifying deployment: {str(e)}"
                ) from e

        # Should not reach here
        raise CloudFunctionError("Failed to notify deployment after all retries")

    def _validate_deploy_config(self, config: Dict[str, Any]) -> None:
        """Validate deployment configuration completeness.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigurationError: If configuration is incomplete
        """
        missing = []

        # Check required fields
        if not config.get("robot_id"):
            missing.append("robot_id")

        # Check registry configuration
        registry = config.get("registry", {})
        if not registry.get("url"):
            missing.append("registry.url")
        if not registry.get("username"):
            missing.append("registry.username")
        if not registry.get("password"):
            missing.append("registry.password")

        if missing:
            raise ConfigurationError(
                f"Cloud function returned incomplete configuration.\n"
                f"Missing fields: {', '.join(missing)}\n"
                f"Please contact your administrator to configure these values."
            )

    async def _wait_before_retry(self, attempt: int) -> None:
        """Wait before retrying with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
        """
        # Exponential backoff: 2^attempt seconds (2s, 4s, 8s, ...)
        delay = 2**attempt
        await asyncio.sleep(delay)

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            HTTP client instance
        """
        if self._client is None:
            # Create a new client if not in context manager
            return httpx.AsyncClient(timeout=self.timeout)
        return self._client
