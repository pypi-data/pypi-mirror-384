"""死信队列处理示例

本示例展示如何从死信队列中消费失败的消息，进行人工处理或恢复。

使用场景：
1. 监控和告警 - 实时检测失败消息
2. 人工审查 - 检查不可重试的错误
3. 消息恢复 - 在修复根本原因后重新处理消息
4. 数据分析 - 分析错误模式，改进系统
"""

import asyncio
import json
import logging
from datetime import datetime

import aio_pika

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DeadLetterHandler')


class DeadLetterQueueHandler:
    """死信队列处理器

    从死信队列读取失败消息，支持：
    - 消息分类和分析
    - 错误统计
    - 消息恢复
    - 告警通知
    """

    def __init__(
        self,
        queue_name: str,
        rabbitmq_host: str = '115.190.75.7',
        rabbitmq_port: int = 5673,
        rabbitmq_vhost: str = '/dev',
        username: str = 'guest',
        password: str = 'guest'
    ):
        """初始化死信队列处理器

        Args:
            queue_name: 原始队列名称
            rabbitmq_host: RabbitMQ主机
            rabbitmq_port: RabbitMQ端口
            rabbitmq_vhost: RabbitMQ虚拟主机
            username: 用户名
            password: 密码
        """
        self.dlq_name = f"{queue_name}.dead_letter"
        self.queue_name = queue_name
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_vhost = rabbitmq_vhost
        self.username = username
        self.password = password

        self.connection = None
        self.channel = None
        self.queue = None

        # 统计信息
        self.stats = {
            'total_processed': 0,
            'by_error_type': {},
            'recent_errors': []  # 最近的10个错误
        }

    async def connect(self) -> bool:
        """连接到RabbitMQ"""
        try:
            logger.info(f"🔌 连接RabbitMQ: {self.rabbitmq_host}:{self.rabbitmq_port}")

            self.connection = await aio_pika.connect_robust(
                host=self.rabbitmq_host,
                port=self.rabbitmq_port,
                login=self.username,
                password=self.password,
                virtualhost=self.rabbitmq_vhost,
                client_properties={
                    "connection_name": "DeadLetterQueueHandler",
                    "product": "uni-agent-sdk",
                    "version": "1.0.0"
                }
            )

            self.channel = await self.connection.channel()
            logger.info("✅ RabbitMQ连接成功")
            return True

        except Exception as e:
            logger.error(f"❌ RabbitMQ连接失败: {e}")
            return False

    async def setup_queue(self) -> bool:
        """设置死信队列"""
        try:
            logger.info(f"📡 设置死信队列: {self.dlq_name}")

            self.queue = await self.channel.declare_queue(
                self.dlq_name,
                durable=True
            )

            logger.info(f"✅ 死信队列设置完成")
            return True

        except Exception as e:
            logger.error(f"❌ 设置死信队列失败: {e}")
            return False

    async def process_dead_letter(self, message: aio_pika.IncomingMessage):
        """处理一条死信消息

        Args:
            message: RabbitMQ消息对象
        """
        try:
            async with message.process():
                # 解析消息
                data = json.loads(message.body.decode())

                self.stats['total_processed'] += 1

                # 提取信息
                error_type = data.get('error_type', 'Unknown')
                original_message = data.get('original_message', 'N/A')
                error = data.get('error', 'N/A')
                timestamp = data.get('timestamp', 0)

                # 更新统计
                if error_type not in self.stats['by_error_type']:
                    self.stats['by_error_type'][error_type] = 0
                self.stats['by_error_type'][error_type] += 1

                # 保存最近的错误
                error_entry = {
                    'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                    'error_type': error_type,
                    'message_id': data.get('message_id', 'N/A'),
                    'error': error[:100]  # 截断长错误信息
                }
                self.stats['recent_errors'].append(error_entry)
                if len(self.stats['recent_errors']) > 10:
                    self.stats['recent_errors'].pop(0)

                # 打印详细信息
                logger.warning(f"💔 死信消息 #{self.stats['total_processed']}")
                logger.warning(f"   🏷️ 错误类型: {error_type}")
                logger.warning(f"   📨 原始消息: {original_message[:100]}...")
                logger.warning(f"   ⚠️ 错误信息: {error[:100]}...")
                logger.warning(f"   🕐 时间戳: {datetime.fromtimestamp(timestamp).isoformat()}")

                # 根据错误类型进行不同处理
                await self._handle_by_error_type(error_type, data)

        except Exception as e:
            logger.error(f"❌ 处理死信消息失败: {e}")

    async def _handle_by_error_type(self, error_type: str, data: dict):
        """根据错误类型进行相应处理

        Args:
            error_type: 错误类型
            data: 完整的死信数据
        """
        if error_type == 'NetworkError':
            # 网络错误 - 可能需要重试
            logger.info("   💡 建议: 检查网络连接，可能需要重新处理")

        elif error_type == 'LLMTimeoutError':
            # LLM超时 - 可能需要增加超时时间
            logger.info("   💡 建议: 增加超时时间或联系LLM服务提供商")

        elif error_type == 'LLMRateLimitError':
            # 限流错误 - 需要降低请求频率
            logger.warning("   ⚠️ 建议: 降低请求频率，等待限流恢复")

        elif error_type == 'MessageFormatError':
            # 消息格式错误 - 需要人工审查
            logger.error("   🔧 建议: 检查消息格式，可能需要修复发送端")

        elif error_type == 'BusinessLogicError':
            # 业务逻辑错误 - 需要人工审查
            logger.error("   🔧 建议: 检查业务逻辑，可能需要修复代码")

        elif error_type == 'AuthenticationError':
            # 认证错误 - 需要更新凭证
            logger.error("   🔑 建议: 检查认证凭证，更新API密钥或权限")

        else:
            logger.warning(f"   ❓ 未知错误类型，需要人工审查")

    async def consume(self, max_messages: int = None):
        """消费死信队列中的消息

        Args:
            max_messages: 最大处理消息数，None表示无限
        """
        try:
            if not await self.connect():
                logger.error("无法连接到RabbitMQ，退出")
                return

            if not await self.setup_queue():
                logger.error("无法设置死信队列，退出")
                return

            logger.info(f"👂 开始监听死信队列: {self.dlq_name}")
            logger.info("=" * 60)

            message_count = 0

            async def process_messages(message: aio_pika.IncomingMessage):
                nonlocal message_count
                if max_messages is not None and message_count >= max_messages:
                    logger.info(f"⏹️ 已处理 {message_count} 条消息，停止消费")
                    await self.stop()
                    return

                await self.process_dead_letter(message)
                message_count += 1

            # 设置消费者
            await self.queue.consume(process_messages)

            # 保持运行
            logger.info("✅ 等待死信消息...")
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("👋 用户中断")
        except Exception as e:
            logger.error(f"❌ 消费过程异常: {e}")
        finally:
            await self.stop()

    async def stop(self):
        """停止处理器"""
        logger.info("📴 停止处理器...")

        if self.connection:
            await self.connection.close()

        logger.info("✅ 处理器已停止")

    def print_stats(self):
        """打印统计信息"""
        logger.info("=" * 60)
        logger.info("📊 死信队列统计")
        logger.info("=" * 60)
        logger.info(f"总处理消息数: {self.stats['total_processed']}")

        if self.stats['by_error_type']:
            logger.info("\n按错误类型统计:")
            for error_type, count in sorted(
                self.stats['by_error_type'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                logger.info(f"  - {error_type}: {count}")

        if self.stats['recent_errors']:
            logger.info("\n最近的错误:")
            for error in self.stats['recent_errors'][-5:]:
                logger.info(f"  - {error['timestamp']}: {error['error_type']} - {error['error']}")

        logger.info("=" * 60)


async def main():
    """主函数"""
    # 创建处理器（使用默认配置）
    handler = DeadLetterQueueHandler(
        queue_name='agent_messages',  # 修改为实际的队列名
        rabbitmq_host='115.190.75.7',
        rabbitmq_port=5673,
        rabbitmq_vhost='/dev',
        username='guest',
        password='guest'
    )

    try:
        # 开始消费死信队列
        await handler.consume()
    except KeyboardInterrupt:
        pass
    finally:
        # 打印最终统计
        handler.print_stats()


if __name__ == '__main__':
    asyncio.run(main())
