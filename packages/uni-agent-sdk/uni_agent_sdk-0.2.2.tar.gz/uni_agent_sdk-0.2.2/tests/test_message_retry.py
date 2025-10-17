"""消息重试机制单元测试

测试场景：
1. 消息处理成功（无需重试）
2. 可重试错误（如网络错误、超时）的重试流程
3. 不可重试错误（如消息格式错误）的立即失败
4. 达到最大重试次数后进入死信队列
5. 重试统计信息的准确性
"""

import asyncio
import json
import logging
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uni_agent_sdk.core.message_broker import MessageBroker
from uni_agent_sdk.utils.config import Config
from uni_agent_sdk.utils.errors import (
    BusinessLogicError,
    LLMTimeoutError,
    MessageFormatError,
    NetworkError,
    NonRetryableError,
    RetryableError,
)

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_message_retry")


class TestMessageRetry:
    """消息重试机制测试类"""

    @pytest.fixture
    def config(self):
        """配置fixture"""
        return Config(
            message_max_retries=3,
            message_retry_delays="1,1,1",  # 使用短延迟加快测试
            enable_dead_letter_queue=True,
        )

    @pytest.fixture
    def message_broker(self, config):
        """消息代理fixture"""
        handler = AsyncMock()
        broker = MessageBroker(
            api_key="test_api_key",
            api_secret="test_api_secret",
            config=config,
            message_handler=handler,
            logger=logger,
            jwt_token="test_token",
            token_expires_at=9999999999,
            rabbitmq_config={
                "host": "localhost",
                "port": 5673,
                "vhost": "/test",
                "username": "guest",
                "queue_name": "test_queue",
            },
            developer_userid="test_dev_user_123",  # 新增：developer_userid
        )
        broker.channel = AsyncMock()
        return broker

    @pytest.mark.asyncio
    async def test_successful_message_processing(self, message_broker):
        """测试消息处理成功（无需重试）"""

        # 创建模拟消息和上下文
        class ProcessContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        message = MagicMock()
        message.body = b'{"test": "data"}'
        message.message_id = b"msg_123"
        message.routing_key = "test.queue"
        message.ack = AsyncMock()
        message.process = MagicMock(return_value=ProcessContext())

        # 设置处理器成功
        message_broker.message_handler = AsyncMock()

        # 处理消息
        await message_broker._process_message(message)

        # 验证
        assert message_broker._retry_stats["successful"] == 1
        assert message_broker._retry_stats["retried_success"] == 0
        assert message_broker._retry_stats["total_messages"] == 1

    @pytest.mark.asyncio
    async def test_retryable_error_success_after_retry(self, message_broker):
        """测试可重试错误在重试后成功"""

        class ProcessContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        # 第一次抛出NetworkError，第二次成功
        call_count = [0]

        async def side_effect(data):
            call_count[0] += 1
            if call_count[0] == 1:
                raise NetworkError("Network timeout")
            # 第二次成功

        message = MagicMock()
        message.body = b'{"test": "data"}'
        message.message_id = b"msg_123"
        message.routing_key = "test.queue"
        message.ack = AsyncMock()
        message.process = MagicMock(return_value=ProcessContext())

        message_broker.message_handler = AsyncMock(side_effect=side_effect)

        # 处理消息
        await message_broker._process_message(message)

        # 验证：第一次失败+重试，第二次成功
        assert (
            message_broker._retry_stats["successful"]
            + message_broker._retry_stats["retried_success"]
            == 1
        )
        assert message_broker._retry_stats["retried_success"] == 1  # 由于重试后成功
        assert message_broker._retry_stats["total_messages"] == 1
        # 注意：重试成功时不会保存错误类型统计（因为最后成功了）

    @pytest.mark.asyncio
    async def test_non_retryable_error_immediate_failure(self, message_broker):
        """测试不可重试错误立即失败"""

        class ProcessContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        message = MagicMock()
        message.body = b'{"test": "data"}'  # 有效的 JSON
        message.message_id = b"msg_456"
        message.routing_key = "test.queue"
        message.ack = AsyncMock()
        message.process = MagicMock(return_value=ProcessContext())

        # 设置处理器抛出不可重试错误
        message_broker.message_handler = AsyncMock(
            side_effect=MessageFormatError("Invalid message format")
        )

        # 模拟发送到死信队列
        message_broker.channel.default_exchange = AsyncMock()
        message_broker.channel.default_exchange.publish = AsyncMock()

        # 处理消息
        await message_broker._process_message(message)

        # 验证：立即失败，无重试
        assert message_broker._retry_stats["successful"] == 0
        assert message_broker._retry_stats["failed_immediate"] == 1
        assert message_broker._retry_stats["total_messages"] == 1
        assert "MessageFormatError" in message_broker._retry_stats["by_error_type"]

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_to_dlq(self, message_broker):
        """测试达到最大重试次数后进入死信队列"""

        class ProcessContext:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        message = MagicMock()
        message.body = b'{"test": "data"}'
        message.message_id = b"msg_789"
        message.routing_key = "test.queue"
        message.ack = AsyncMock()
        message.process = MagicMock(return_value=ProcessContext())

        # 一直抛出可重试错误
        message_broker.message_handler = AsyncMock(
            side_effect=NetworkError("Persistent network error")
        )

        # 模拟发送到死信队列
        message_broker.channel.default_exchange = AsyncMock()
        message_broker.channel.default_exchange.publish = AsyncMock()

        # 处理消息
        await message_broker._process_message(message)

        # 验证：重试3次后失败进入DLQ
        assert message_broker._retry_stats["failed_to_dlq"] == 1
        assert message_broker._retry_stats["total_messages"] == 1
        # 验证发送到了死信队列
        message_broker.channel.default_exchange.publish.assert_called()

    def test_retry_stats_generation(self, message_broker):
        """测试重试统计信息生成"""
        # 设置一些统计数据
        message_broker._retry_stats = {
            "total_messages": 100,
            "successful": 80,
            "retried_success": 15,
            "failed_to_dlq": 3,
            "failed_immediate": 2,
            "by_error_type": {
                "NetworkError": 10,
                "LLMTimeoutError": 5,
                "MessageFormatError": 2,
            },
        }

        # 获取统计
        stats = message_broker.get_retry_stats()

        # 验证
        assert stats["summary"]["total_messages"] == 100
        assert stats["summary"]["successful"] == 80
        assert stats["summary"]["retried_success"] == 15
        assert stats["summary"]["failed_to_dlq"] == 3
        assert stats["summary"]["failed_immediate"] == 2
        assert stats["summary"]["success_rate"] == "95.00%"

        # 验证配置信息
        assert stats["retry_config"]["max_retries"] == 3
        assert stats["retry_config"]["retry_delays"] == [1, 1, 1]
        assert stats["retry_config"]["enable_dead_letter_queue"] is True

    def test_reset_retry_stats(self, message_broker):
        """测试重试统计重置"""
        # 设置一些统计数据
        message_broker._retry_stats = {
            "total_messages": 100,
            "successful": 80,
            "retried_success": 15,
            "failed_to_dlq": 3,
            "failed_immediate": 2,
            "by_error_type": {"NetworkError": 10},
        }

        # 重置
        message_broker.reset_retry_stats()

        # 验证
        assert message_broker._retry_stats["total_messages"] == 0
        assert message_broker._retry_stats["successful"] == 0
        assert message_broker._retry_stats["retried_success"] == 0
        assert message_broker._retry_stats["failed_to_dlq"] == 0
        assert message_broker._retry_stats["failed_immediate"] == 0
        assert message_broker._retry_stats["by_error_type"] == {}

    def test_error_type_update_stats(self, message_broker):
        """测试错误类型统计更新"""
        message_broker._update_error_type_stats("NetworkError")
        message_broker._update_error_type_stats("NetworkError")
        message_broker._update_error_type_stats("LLMTimeoutError")

        # 验证
        assert message_broker._retry_stats["by_error_type"]["NetworkError"] == 2
        assert message_broker._retry_stats["by_error_type"]["LLMTimeoutError"] == 1

    @pytest.mark.asyncio
    async def test_dead_letter_queue_structure(self, message_broker):
        """测试死信队列消息结构"""
        message = MagicMock()
        message.body = b'{"original": "data"}'
        message.message_id = b"msg_test"
        message.routing_key = "test.queue"

        error = NetworkError("Network connection failed")
        error_type = "NetworkError"

        # 模拟发送到死信队列
        message_broker.channel.default_exchange = AsyncMock()
        message_broker.channel.default_exchange.publish = AsyncMock()

        # 调用发送方法
        await message_broker._send_to_dead_letter_queue(message, error, error_type)

        # 验证发送被调用
        assert message_broker.channel.default_exchange.publish.called

        # 获取发送的消息
        call_args = message_broker.channel.default_exchange.publish.call_args
        sent_message = call_args[0][0]
        routing_key = call_args[1]["routing_key"]

        # 验证路由键
        assert routing_key == "test_queue.dead_letter"

        # 验证消息内容
        dlq_data = json.loads(sent_message.body.decode())
        assert dlq_data["error_type"] == "NetworkError"
        assert "original_message" in dlq_data
        assert "error" in dlq_data
        assert "timestamp" in dlq_data
        assert "message_id" in dlq_data


class TestRetryConfig:
    """重试配置测试类"""

    def test_default_retry_config(self):
        """测试默认重试配置"""
        config = Config()

        assert config.message_max_retries == 3
        assert config.message_retry_delays == [1, 2, 4]
        assert config.enable_dead_letter_queue is True

    def test_custom_retry_delays(self):
        """测试自定义重试延迟"""
        config = Config(message_retry_delays="2,3,5")

        assert config.message_retry_delays == [2, 3, 5]

    def test_invalid_retry_delays(self):
        """测试无效的重试延迟配置"""
        config = Config(message_retry_delays="invalid")

        # 应该返回默认值
        assert config.message_retry_delays == [1, 2, 4]

    def test_disable_dead_letter_queue(self):
        """测试禁用死信队列"""
        config = Config(enable_dead_letter_queue=False)

        assert config.enable_dead_letter_queue is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
