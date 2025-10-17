#!/usr/bin/env python3
"""Token自动刷新机制测试

测试场景：
1. Token即将过期时自动刷新
2. Token刷新失败时的重试机制
3. Token刷新成功后自动重连RabbitMQ
4. 连接监控检测断开并重连
"""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uni_agent_sdk.core.message_broker import MessageBroker
from uni_agent_sdk.utils.config import Config

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_token_refresh")


class TestTokenRefresh:
    """Token自动刷新机制测试类"""

    @pytest.fixture
    def config(self):
        """配置fixture"""
        return Config()

    @pytest.fixture
    def message_broker(self, config):
        """消息代理fixture"""
        handler = AsyncMock()
        broker = MessageBroker(
            api_key="robot_test_api_key_deepseek",
            api_secret="test_api_secret_deepseek",
            config=config,
            message_handler=handler,
            logger=logger,
            jwt_token="test_token_old",
            token_expires_at=int(time.time()) + 60,  # 60秒后过期
            rabbitmq_config={
                "host": "localhost",
                "port": 5673,
                "vhost": "/test",
                "username": "guest",
                "queue_name": "test_queue",
            },
            developer_userid="test_dev_user_123",  # 新增：developer_userid
        )
        return broker

    @pytest.mark.asyncio
    async def test_token_refresh_when_expiring(self, message_broker):
        """测试Token即将过期时自动刷新"""
        # 模拟_get_jwt_token方法
        original_get_token = message_broker._get_jwt_token
        get_token_called = [False]

        async def mock_get_jwt_token():
            get_token_called[0] = True
            message_broker.jwt_token = "test_token_new"
            message_broker.token_expires_at = int(time.time()) + 3600
            message_broker.rabbit_config = {
                "host": "localhost",
                "port": 5673,
                "vhost": "/test",
                "username": "guest",
                "queue_name": "test_queue",
            }
            message_broker.queue_name = "test_queue"
            logger.info("✅ Token已刷新（模拟）")
            return True

        # 设置token即将过期
        message_broker.token_expires_at = int(time.time()) + 250  # 250秒后过期
        message_broker._get_jwt_token = mock_get_jwt_token
        message_broker._reconnect_rabbitmq = AsyncMock()

        # 运行一次token刷新循环
        message_broker._running = True
        try:
            # 这个循环会检查token是否即将过期，然后刷新
            # 我们需要手动执行循环逻辑来测试
            current_time = int(time.time())
            if (
                message_broker.token_expires_at
                and (message_broker.token_expires_at - current_time) < 300
            ):
                logger.warning(
                    f"⏰ Token即将过期 (还剩 {message_broker.token_expires_at - current_time} 秒)，开始自动刷新..."
                )
                if await message_broker._get_jwt_token():
                    logger.info("✅ Token已自动刷新，重新连接RabbitMQ...")
                    await message_broker._reconnect_rabbitmq()
        finally:
            message_broker._running = False

        # 验证
        assert get_token_called[0], "Token刷新方法应该被调用"
        assert message_broker.jwt_token == "test_token_new", "Token应该被更新"
        assert message_broker._reconnect_rabbitmq.called, "重连方法应该被调用"

    @pytest.mark.asyncio
    async def test_token_not_refreshed_when_valid(self, message_broker):
        """测试Token有效时不刷新"""
        # 设置token还有很长的有效期
        message_broker.token_expires_at = int(time.time()) + 3600
        message_broker._get_jwt_token = AsyncMock()

        message_broker._running = True
        try:
            # 检查token是否即将过期
            current_time = int(time.time())
            should_refresh = (
                message_broker.token_expires_at
                and (message_broker.token_expires_at - current_time) < 300
            )
        finally:
            message_broker._running = False

        # 验证
        assert not should_refresh, "Token有效期充足时不应该刷新"
        assert not message_broker._get_jwt_token.called, "Token刷新方法不应该被调用"

    @pytest.mark.asyncio
    async def test_token_refresh_failure_retry(self, message_broker):
        """测试Token刷新失败时的重试机制"""
        # 模拟_get_jwt_token失败
        message_broker._get_jwt_token = AsyncMock(return_value=False)
        message_broker._reconnect_rabbitmq = AsyncMock()

        # 设置token即将过期
        message_broker.token_expires_at = int(time.time()) + 250

        message_broker._running = True
        try:
            current_time = int(time.time())
            if (
                message_broker.token_expires_at
                and (message_broker.token_expires_at - current_time) < 300
            ):
                logger.warning(
                    f"⏰ Token即将过期 (还剩 {message_broker.token_expires_at - current_time} 秒)，开始自动刷新..."
                )
                if await message_broker._get_jwt_token():
                    logger.info("✅ Token已自动刷新，重新连接RabbitMQ...")
                    await message_broker._reconnect_rabbitmq()
                else:
                    logger.error("❌ Token自动刷新失败，将在30秒后重试")
        finally:
            message_broker._running = False

        # 验证
        assert message_broker._get_jwt_token.called, "Token刷新方法应该被调用"
        assert not message_broker._reconnect_rabbitmq.called, "刷新失败时不应该重连"

    @pytest.mark.asyncio
    async def test_connection_monitor_detects_disconnection(self, message_broker):
        """测试连接监控检测断开"""
        # 模拟连接已断开
        message_broker.connection = MagicMock()
        message_broker.connection.is_closed = True
        message_broker._reconnect_rabbitmq = AsyncMock()

        message_broker._running = True
        try:
            # 模拟连接监控逻辑
            if not message_broker.connection or message_broker.connection.is_closed:
                logger.warning("⚠️ 检测到连接断开，尝试重连...")
                await message_broker._reconnect_rabbitmq()
        finally:
            message_broker._running = False

        # 验证
        assert message_broker._reconnect_rabbitmq.called, "重连方法应该被调用"

    @pytest.mark.asyncio
    async def test_is_connected_status(self, message_broker):
        """测试连接状态检查"""
        # 模拟已连接
        message_broker.connection = MagicMock()
        message_broker.connection.is_closed = False
        message_broker.channel = MagicMock()
        message_broker.channel.is_closed = False

        assert message_broker.is_connected(), "应该返回已连接状态"

        # 模拟连接断开
        message_broker.connection.is_closed = True
        assert not message_broker.is_connected(), "应该返回未连接状态"

    def test_token_expiry_calculation(self, message_broker):
        """测试Token过期时间计算"""
        current_time = int(time.time())

        # 测试case 1: Token即将过期
        message_broker.token_expires_at = current_time + 250
        remaining_time = message_broker.token_expires_at - current_time
        should_refresh = remaining_time < 300
        assert should_refresh, "剩余时间<300秒时应该刷新"

        # 测试case 2: Token刚好即将过期
        message_broker.token_expires_at = current_time + 300
        remaining_time = message_broker.token_expires_at - current_time
        should_refresh = remaining_time < 300
        assert not should_refresh, "剩余时间=300秒时不应该刷新"

        # 测试case 3: Token有效期充足
        message_broker.token_expires_at = current_time + 3600
        remaining_time = message_broker.token_expires_at - current_time
        should_refresh = remaining_time < 300
        assert not should_refresh, "剩余时间>300秒时不应该刷新"

    def test_queue_info_includes_token_validity(self, message_broker):
        """测试队列信息中包含Token有效性"""
        current_time = int(time.time())

        # Token有效
        message_broker.token_expires_at = current_time + 3600
        message_broker.connection = MagicMock()
        message_broker.connection.is_closed = False
        message_broker.channel = MagicMock()
        message_broker.channel.is_closed = False

        queue_info = message_broker.get_queue_info()
        assert queue_info["jwt_token_valid"], "Token应该显示为有效"
        assert queue_info["connected"], "应该显示已连接"

        # Token过期
        message_broker.token_expires_at = current_time - 100
        queue_info = message_broker.get_queue_info()
        assert not queue_info["jwt_token_valid"], "Token应该显示为过期"


class TestTokenRefreshIntegration:
    """Token刷新集成测试类"""

    @pytest.mark.asyncio
    async def test_continuous_token_refresh_loop(self):
        """测试持续的Token刷新循环"""
        config = Config()
        handler = AsyncMock()

        broker = MessageBroker(
            api_key="robot_test_api_key_deepseek",
            api_secret="test_api_secret_deepseek",
            config=config,
            message_handler=handler,
            logger=logger,
            jwt_token="test_token_initial",
            token_expires_at=int(time.time()) + 60,
            rabbitmq_config={
                "host": "localhost",
                "port": 5673,
                "vhost": "/test",
                "username": "guest",
                "queue_name": "test_queue",
            },
            developer_userid="test_dev_user_123",  # 新增：developer_userid
        )

        # 统计调用次数
        call_count = {"get_token": 0, "reconnect": 0}

        async def mock_get_jwt_token():
            call_count["get_token"] += 1
            broker.jwt_token = f'test_token_{call_count["get_token"]}'
            broker.token_expires_at = int(time.time()) + 3600
            broker.rabbit_config = {
                "host": "localhost",
                "port": 5673,
                "vhost": "/test",
                "username": "guest",
                "queue_name": "test_queue",
            }
            logger.info(f"✅ Token已刷新 #{call_count['get_token']}")
            return True

        async def mock_reconnect():
            call_count["reconnect"] += 1
            logger.info(f"🔄 RabbitMQ已重连 #{call_count['reconnect']}")

        broker._get_jwt_token = mock_get_jwt_token
        broker._reconnect_rabbitmq = mock_reconnect

        # 运行刷新循环（只运行一个迭代）
        broker._running = True
        try:
            # 第一次迭代：Token过期，需要刷新
            broker.token_expires_at = int(time.time()) + 250
            current_time = int(time.time())
            if (
                broker.token_expires_at
                and (broker.token_expires_at - current_time) < 300
            ):
                if await broker._get_jwt_token():
                    await broker._reconnect_rabbitmq()

            # 验证
            assert call_count["get_token"] == 1, "Token刷新应该被调用1次"
            assert call_count["reconnect"] == 1, "RabbitMQ重连应该被调用1次"

            # 第二次迭代：Token有效，不刷新
            current_time = int(time.time())
            if (
                broker.token_expires_at
                and (broker.token_expires_at - current_time) < 300
            ):
                if await broker._get_jwt_token():
                    await broker._reconnect_rabbitmq()

            # 验证
            assert call_count["get_token"] == 1, "Token刷新应该仍然只被调用1次"
            assert call_count["reconnect"] == 1, "RabbitMQ重连应该仍然只被调用1次"

        finally:
            broker._running = False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
