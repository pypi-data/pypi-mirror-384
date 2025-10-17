#!/usr/bin/env python3
"""Example of using CloudFunctionClient to retrieve deployment configuration.

This example demonstrates:
1. Creating a CloudFunctionClient instance
2. Retrieving deployment configuration from cloud function
3. Handling errors (authentication, network, configuration)
4. Using the client as an async context manager
"""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from uni_agent_sdk.build_system import (
    AuthenticationError,
    CloudFunctionClient,
    ConfigurationError,
    NetworkError,
)
from uni_agent_sdk.build_system.config_provider import ConfigProvider


async def example_basic_usage():
    """Basic usage example."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Load configuration
    config = ConfigProvider()

    try:
        appkey = config.get_robot_appkey()
        cloud_url = config.get_cloud_function_url()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease set the following environment variables:")
        print("  export ROBOT_APPKEY=your-appkey")
        print("  export CLOUD_FUNCTION_URL=http://api.example.com")
        return

    print(f"📋 Configuration:")
    print(f"   Cloud URL: {cloud_url}")
    print(f"   AppKey: {appkey[:20]}...")
    print()

    # Create client
    client = CloudFunctionClient(base_url=cloud_url)

    try:
        print("🔗 Fetching deployment configuration...")
        deploy_config = await client.get_deploy_config(appkey)

        print("✅ Configuration retrieved successfully!")
        print()
        print(f"📊 Deployment Configuration:")
        print(f"   Robot ID: {deploy_config['robot_id']}")
        print(
            f"   Registry URL: {deploy_config['registry']['url']}"
        )
        print(
            f"   Registry Username: {deploy_config['registry']['username']}"
        )
        print(
            f"   Node Server URL: {deploy_config.get('node_server', {}).get('url', 'Not configured')}"
        )

    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPlease check your ROBOT_APPKEY is correct.")

    except NetworkError as e:
        print(f"❌ Network error: {e}")
        print("\nPlease check your network connection and cloud function URL.")

    except ConfigurationError as e:
        print(f"❌ Configuration incomplete: {e}")
        print("\nPlease contact your administrator.")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def example_context_manager():
    """Example using context manager."""
    print("\n" + "=" * 60)
    print("Example 2: Using Context Manager")
    print("=" * 60)

    config = ConfigProvider()

    try:
        appkey = config.get_robot_appkey()
        cloud_url = config.get_cloud_function_url()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    # Use as context manager for automatic cleanup
    async with CloudFunctionClient(base_url=cloud_url) as client:
        try:
            print("🔗 Fetching configuration with context manager...")
            deploy_config = await client.get_deploy_config(appkey)

            print(f"✅ Robot ID: {deploy_config['robot_id']}")
            print("✅ Client will be automatically closed on exit")

        except Exception as e:
            print(f"❌ Error: {e}")


async def example_with_retry():
    """Example demonstrating retry behavior."""
    print("\n" + "=" * 60)
    print("Example 3: Retry Mechanism")
    print("=" * 60)

    config = ConfigProvider()

    try:
        appkey = config.get_robot_appkey()
        cloud_url = config.get_cloud_function_url()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    print("📋 Client configured with:")
    print("   Max retries: 3")
    print("   Timeout: 10 seconds")
    print("   Exponential backoff: 2^n seconds")
    print()

    # Create client with custom retry settings
    client = CloudFunctionClient(
        base_url=cloud_url, timeout=10.0, max_retries=3
    )

    try:
        print("🔗 Attempting to fetch configuration...")
        print("   (Will retry on network errors with exponential backoff)")
        deploy_config = await client.get_deploy_config(appkey)

        print(f"✅ Success! Robot ID: {deploy_config['robot_id']}")

    except NetworkError as e:
        print(f"❌ Failed after all retries: {e}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_notify_deployment():
    """Example of notifying deployment status."""
    print("\n" + "=" * 60)
    print("Example 4: Notify Deployment")
    print("=" * 60)

    config = ConfigProvider()

    try:
        cloud_url = config.get_cloud_function_url()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    async with CloudFunctionClient(base_url=cloud_url) as client:
        try:
            deployment_data = {
                "image": "registry.example.com/robots/my-robot:1.0.0",
                "version": "1.0.0",
                "status": "deploying",
            }

            print("🚀 Notifying deployment start...")
            result = await client.notify_deployment(
                "robot-12345", deployment_data
            )

            print(f"✅ Notification sent: {result}")

        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    print("🚀 CloudFunctionClient Examples")
    print()

    # Run examples
    await example_basic_usage()
    await example_context_manager()
    await example_with_retry()
    await example_notify_deployment()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
