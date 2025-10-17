"""消息代理 - RabbitMQ消息监听与管理

将原本分散在智能体中的400+行RabbitMQ代码统一封装，
提供自动重连、错误恢复、JWT认证等企业级功能。

设计原则：
- 隐藏复杂性：开发者无需了解RabbitMQ细节
- 自动恢复：网络断线、认证失效自动处理
- 企业级：连接池、监控、日志等生产级特性
"""

import asyncio
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict, Optional

import aio_pika
import requests

from ..utils.config import Config
from ..utils.errors import NonRetryableError, RetryableError


class MessageBroker:
    """消息代理 - 统一的RabbitMQ消息处理

    封装所有RabbitMQ相关的复杂逻辑：
    - JWT Token获取与自动刷新
    - RabbitMQ连接与断线重连
    - 队列声明与消息消费
    - 错误处理与状态监控
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        config: Config,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]],
        logger: logging.Logger = None,
        jwt_token: str = None,
        token_expires_at: int = None,
        rabbitmq_config: Dict[str, Any] = None,
        developer_userid: str = None,
    ):
        """初始化消息代理

        Args:
            api_key: 智能体API密钥
            api_secret: 智能体API秘钥
            config: 配置对象
            message_handler: 消息处理回调函数
            logger: 日志记录器（可选，如果不提供则创建新的）
            jwt_token: JWT认证令牌（由Agent提供）
            token_expires_at: Token过期时间（由Agent提供）
            rabbitmq_config: RabbitMQ配置信息（由Agent提供）
            developer_userid: 开发者用户ID（由Agent提供，用于Token刷新）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config
        self.message_handler = message_handler

        # 使用传入的logger或创建新的logger
        self.logger = logger if logger is not None else logging.getLogger(api_key[:8])

        # JWT认证状态（由Agent提供）
        self.jwt_token = jwt_token
        self.token_expires_at = token_expires_at
        self.rabbit_config = rabbitmq_config
        # 安全地获取queue_name，避免 None 访问
        self.queue_name = (
            rabbitmq_config.get("queue_name")
            if rabbitmq_config and isinstance(rabbitmq_config, dict)
            else None
        )
        self.developer_userid = developer_userid

        # RabbitMQ连接状态
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None

        # 运行状态
        self._running = False
        self._reconnect_task: Optional[asyncio.Task] = None
        self._token_refresh_task: Optional[asyncio.Task] = None

        # 重连策略配置
        self.reconnect_delay = 1  # 初始延迟1秒
        self.max_reconnect_delay = 60  # 最大延迟60秒
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

        # 消息处理重试配置
        self.max_retries = config.message_max_retries
        self.retry_delays = config.message_retry_delays
        self.enable_dead_letter_queue = config.enable_dead_letter_queue

        # 重试统计
        self._retry_stats = {
            "total_messages": 0,  # 总处理消息数
            "successful": 0,  # 一次成功
            "retried_success": 0,  # 重试后成功
            "failed_to_dlq": 0,  # 失败进入死信队列
            "failed_immediate": 0,  # 立即失败（不可重试）
            "by_error_type": {},  # 按错误类型统计
        }

    # === JWT Token管理 ===

    async def _get_jwt_token(self) -> bool:
        """获取JWT Token并刷新RabbitMQ配置

        此方法用于Token刷新场景，需要developer_userid进行认证。

        正确的OAuth 2.0流程是：
        1. Agent通过register_robot()获取初始Token和developer_userid
        2. 将两者都传递给MessageBroker
        3. MessageBroker在Token即将过期时，使用developer_userid刷新Token
        """
        try:
            # 验证必需的认证信息
            if not self.developer_userid:
                self.logger.error("❌ 缺少developer_userid，无法刷新Token")
                self.logger.error(
                    "   请确保Agent已通过register_robot()获取developer_userid"
                )
                return False

            self.logger.info("🔑 从uni-im云函数刷新JWT Token...")

            url = f"{self.config.platform_base_url}/uni-im-co/getRabbitMQToken"
            data = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "developer_userid": self.developer_userid,  # 关键：传递developer_userid进行认证
            }

            # 添加CONNECTCODE头部进行S2S认证
            headers = {
                "Content-Type": "application/json",
                "Unicloud-S2s-Authorization": f"CONNECTCODE {self.config.connectcode}",
            }

            self.logger.debug(f"   请求URL: {url}")
            self.logger.debug(
                f"   请求数据: api_key={self.api_key[:10]}..., developer_userid={self.developer_userid}"
            )

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()

                if result.get("errCode") == 0:
                    token_data = result["data"]

                    self.jwt_token = token_data["token"]
                    self.token_expires_at = token_data["expires_at"]
                    self.rabbit_config = token_data["rabbitmq_config"]
                    self.queue_name = token_data["rabbitmq_config"]["queue_name"]

                    current_time = int(time.time())
                    remaining_seconds = self.token_expires_at - current_time
                    self.logger.info("✅ JWT Token从uni-im云函数刷新成功")
                    self.logger.info(f"   新Token有效期: {remaining_seconds}秒")
                    self.logger.debug(f"   队列: {self.queue_name}")

                    return True
                else:
                    self.logger.error(
                        f"❌ uni-im云函数返回错误: {result.get('errMsg')}"
                    )
                    self.logger.error(
                        f"   请检查developer_userid是否有效: {self.developer_userid}"
                    )
                    return False
            else:
                self.logger.error(
                    f"❌ uni-im云函数HTTP请求失败: {response.status_code}"
                )
                self.logger.error(f"   响应内容: {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 获取JWT Token失败: {e}")
            import traceback

            self.logger.debug(f"   错误详情: {traceback.format_exc()}")
            return False

    async def _token_refresh_loop(self):
        """JWT Token自动刷新循环"""
        while self._running:
            try:
                # 检查Token是否即将过期（提前5分钟刷新）
                current_time = int(time.time())
                if (
                    self.token_expires_at
                    and (self.token_expires_at - current_time) < 300
                ):
                    self.logger.warning(
                        f"⏰ Token即将过期 (还剩 {self.token_expires_at - current_time} 秒)，开始自动刷新..."
                    )
                    if await self._get_jwt_token():
                        self.logger.info("✅ Token已自动刷新，重新连接RabbitMQ...")
                        # Token刷新成功，重新连接
                        await self._reconnect_rabbitmq()
                    else:
                        self.logger.error("❌ Token自动刷新失败，将在30秒后重试")
                        await asyncio.sleep(30)
                        continue

                # 每分钟检查一次
                await asyncio.sleep(60)

            except Exception as e:
                self.logger.error(f"❌ Token刷新循环异常: {e}")
                await asyncio.sleep(60)

    # === RabbitMQ连接管理 ===

    async def _connect_rabbitmq(self) -> bool:
        """连接RabbitMQ"""
        try:
            self.logger.info("🔌 连接RabbitMQ...")

            # 确保JWT认证已完成
            if not self.jwt_token or not self.rabbit_config:
                self.logger.error("❌ JWT Token或RabbitMQ配置未获取，无法连接")
                return False

            # 使用JWT认证信息
            rabbit_config = self.rabbit_config
            if not rabbit_config:
                self.logger.error("❌ rabbit_config 为 None，无法连接")
                return False
            self.queue_name = rabbit_config.get("queue_name")
            if not self.queue_name:
                self.logger.error("❌ 无法从rabbit_config中获取queue_name")
                return False

            # 详细连接参数日志
            self.logger.info("📋 RabbitMQ连接参数:")
            self.logger.info(
                f"   🏠 主机: {rabbit_config['host']}:{rabbit_config['port']}"
            )
            self.logger.info(f"   🏡 虚拟主机: {rabbit_config['vhost']}")
            self.logger.info(f"   👤 用户名: {rabbit_config['username']}")
            self.logger.info(f"   🔒 密码: ***JWT认证***")
            self.logger.info(f"   📡 目标队列: {self.queue_name}")

            # 强制使用JWT OAuth认证（仅支持JWT认证）
            self.logger.info("🔐 使用JWT OAuth认证连接RabbitMQ")
            self.logger.info(
                f"🔑 JWT Token (前50字符): {self.jwt_token[:50] if self.jwt_token else 'None'}..."
            )
            self.logger.info(
                f"🔑 JWT Token (后50字符): ...{self.jwt_token[-50:] if self.jwt_token and len(self.jwt_token) > 50 else self.jwt_token}"
            )

            # 建立robust连接（自动重连）- 仅支持JWT认证
            self.connection = await aio_pika.connect_robust(
                host=rabbit_config["host"],
                port=rabbit_config["port"],
                login=rabbit_config["username"],  # OAuth用户名
                password=self.jwt_token,  # JWT token作为密码
                virtualhost=rabbit_config["vhost"],
                client_properties={
                    "connection_name": f"Agent-{self.api_key[:8]}",
                    "product": "uni-agent-sdk",
                    "version": "1.0.0",
                    "auth_type": "JWT_OAuth2",
                },
            )

            # 创建频道
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.config.prefetch_count)

            self.logger.info("✅ RabbitMQ连接成功")
            self.logger.info("📊 连接状态信息:")
            self.logger.info(
                f"   🔌 连接状态: {'已连接' if self.connection and not self.connection.is_closed else '未连接'}"
            )
            self.logger.info(
                f"   📺 频道状态: {'已打开' if self.channel and not self.channel.is_closed else '未打开'}"
            )
            self.logger.info(f"   🏡 实际虚拟主机: {self.config.rabbitmq_vhost}")
            self.logger.info(f"   📡 监听队列: {self.queue_name}")
            self.logger.info(f"   ⚡ QoS预取数量: {self.config.prefetch_count}")

            return True

        except Exception as e:
            self.logger.error(f"❌ RabbitMQ连接失败: {e}")
            return False

    async def _setup_queue_consumer(self) -> bool:
        """设置队列消费者"""
        try:
            self.logger.info("📡 设置队列消费者...")

            # 队列配置参数
            queue_config = {
                "x-message-ttl": 300000,  # 5分钟TTL
                "x-max-length": 10000,  # 最大消息数
                "x-overflow": "reject-publish",  # 队列满时拒绝发布
            }

            self.logger.info("📋 队列配置信息:")
            self.logger.info(f"   📡 队列名称: {self.queue_name}")
            self.logger.info(f"   🏡 虚拟主机: {self.config.rabbitmq_vhost}")
            self.logger.info(f"   💾 持久化: 是")
            self.logger.info(f"   ⏰ 消息TTL: {queue_config['x-message-ttl'] / 1000}秒")
            self.logger.info(f"   📊 最大消息数: {queue_config['x-max-length']}")
            self.logger.info(f"   🚫 溢出策略: {queue_config['x-overflow']}")

            # 声明队列（与云函数配置一致）
            self.queue = await self.channel.declare_queue(
                self.queue_name, durable=True, arguments=queue_config
            )

            # 设置消息处理器
            await self.queue.consume(self._process_message)

            self.logger.info("✅ 消费者设置完成")
            self.logger.info("📊 队列状态信息:")
            self.logger.info(f"   📡 监听队列: {self.queue_name}")
            self.logger.info(f"   🔄 消费者状态: 已启动")
            return True

        except Exception as e:
            self.logger.error(f"❌ 设置消费者失败: {e}")
            return False

    async def _process_message(self, message: aio_pika.IncomingMessage):
        """处理接收到的消息，支持智能重试和死信队列

        重试策略：
        - 可重试错误（RetryableError）：使用指数退避重试
        - 不可重试错误（NonRetryableError）：立即失败，发送到死信队列
        - 其他异常：默认为不可重试

        死信队列：重试失败后的消息发送到死信队列供人工处理
        """
        retry_count = 0
        message_data = None
        error_type = None

        while retry_count <= self.max_retries:
            try:
                async with message.process():
                    # 解析消息（只在第一次时进行）
                    if message_data is None:
                        try:
                            message_data = json.loads(message.body.decode())
                            self.logger.debug(f"🔥 收到原始消息: {message_data}")
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            # 消息解析失败 - 不可重试
                            self.logger.error(f"❌ 消息解析失败: {e}")
                            if self.enable_dead_letter_queue:
                                await self._send_to_dead_letter_queue(
                                    message, e, "MessageDecodeError"
                                )
                            self._retry_stats["failed_immediate"] += 1
                            self._update_error_type_stats("MessageDecodeError")
                            return

                    # 调用用户消息处理器
                    try:
                        await self.message_handler(message_data)

                        # 成功
                        if retry_count == 0:
                            self._retry_stats["successful"] += 1
                            self.logger.debug(f"✅ 消息处理成功")
                        else:
                            self._retry_stats["retried_success"] += 1
                            self.logger.info(f"✅ 重试{retry_count}次后成功")

                        self._retry_stats["total_messages"] += 1
                        return

                    except RetryableError as e:
                        # 可重试错误 - 记录并重试
                        error_type = type(e).__name__
                        retry_count += 1

                        if retry_count <= self.max_retries:
                            delay = (
                                self.retry_delays[retry_count - 1]
                                if retry_count - 1 < len(self.retry_delays)
                                else self.retry_delays[-1]
                            )
                            self.logger.warning(
                                f"⚠️ [{error_type}] 可重试错误: {e}, "
                                f"将在{delay}秒后重试({retry_count}/{self.max_retries})"
                            )
                            # 消息确认（避免重复处理）
                            await message.ack()
                            # 等待后重新处理
                            await asyncio.sleep(delay)
                        else:
                            # 达到最大重试次数
                            self.logger.error(
                                f"❌ [{error_type}] 重试{self.max_retries}次后仍失败: {e}"
                            )
                            if self.enable_dead_letter_queue:
                                await self._send_to_dead_letter_queue(
                                    message, e, error_type
                                )
                            self._retry_stats["failed_to_dlq"] += 1
                            self._update_error_type_stats(error_type)
                            self._retry_stats["total_messages"] += 1
                            return

                    except NonRetryableError as e:
                        # 不可重试错误 - 立即失败
                        error_type = type(e).__name__
                        self.logger.error(f"❌ [{error_type}] 不可重试错误: {e}")
                        if self.enable_dead_letter_queue:
                            await self._send_to_dead_letter_queue(
                                message, e, error_type
                            )
                        self._retry_stats["failed_immediate"] += 1
                        self._update_error_type_stats(error_type)
                        self._retry_stats["total_messages"] += 1
                        return

                    except Exception as e:
                        # 未分类的异常 - 当作不可重试错误处理
                        error_type = type(e).__name__
                        self.logger.error(f"❌ [{error_type}] 未预期的异常: {e}")
                        if self.enable_dead_letter_queue:
                            await self._send_to_dead_letter_queue(
                                message, e, error_type
                            )
                        self._retry_stats["failed_immediate"] += 1
                        self._update_error_type_stats(error_type)
                        self._retry_stats["total_messages"] += 1
                        return

            except Exception as e:
                # 消息处理上下文异常
                self.logger.error(f"❌ 消息处理上下文异常: {e}")
                self._retry_stats["failed_immediate"] += 1
                self._retry_stats["total_messages"] += 1
                return

    def _update_error_type_stats(self, error_type: str):
        """更新错误类型统计"""
        if error_type not in self._retry_stats["by_error_type"]:
            self._retry_stats["by_error_type"][error_type] = 0
        self._retry_stats["by_error_type"][error_type] += 1

    async def _send_to_dead_letter_queue(
        self, message: aio_pika.IncomingMessage, error: Exception, error_type: str
    ):
        """发送消息到死信队列供人工处理

        Args:
            message: 原始消息
            error: 导致失败的异常
            error_type: 错误类型名称
        """
        try:
            dead_letter_data = {
                "original_message": message.body.decode(),
                "error": str(error),
                "error_type": error_type,
                "error_traceback": None,
                "timestamp": int(time.time()),
                "routing_key": message.routing_key or "unknown",
                "message_id": (
                    message.message_id.decode()
                    if isinstance(message.message_id, bytes)
                    else str(message.message_id)
                ),
            }

            # 发送到死信队列
            dlq_name = f"{self.queue_name}.dead_letter"
            dead_letter_message = aio_pika.Message(
                body=json.dumps(dead_letter_data).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                timestamp=int(time.time()),
            )

            await self.channel.default_exchange.publish(
                dead_letter_message, routing_key=dlq_name
            )

            self.logger.info(f"✅ 消息已发送到死信队列: {dlq_name}")
            self.logger.debug(
                f"   原始消息: {dead_letter_data['original_message'][:100]}..."
            )
            self.logger.debug(f"   错误类型: {error_type}")
            self.logger.debug(f"   错误信息: {str(error)[:100]}...")

        except Exception as e:
            self.logger.error(f"❌ 发送死信队列失败: {e}")
            self.logger.error(f"   原始错误: {error}")

    async def _reconnect_rabbitmq(self):
        """重新连接RabbitMQ with exponential backoff"""
        try:
            # 计算退避延迟
            delay = min(
                self.reconnect_delay * (2**self.reconnect_attempts),
                self.max_reconnect_delay,
            )

            if self.reconnect_attempts > 0:
                self.logger.info(
                    f"⏰ 等待 {delay}s 后重连 (尝试 {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})"
                )
                await asyncio.sleep(delay)

            # 关闭现有连接
            if self.connection:
                await self.connection.close()

            # 尝试重连
            if await self._connect_rabbitmq():
                await self._setup_queue_consumer()
                self.logger.info("🔄 RabbitMQ重连成功")
                self.reconnect_attempts = 0  # 重置重连计数
            else:
                self.reconnect_attempts += 1
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    self.logger.error("❌ 达到最大重连次数，停止重连")
                    await self.stop()
                    raise Exception("RabbitMQ重连失败")
                else:
                    self.logger.error(f"🔄 RabbitMQ重连失败，将在下次循环重试")

        except Exception as e:
            self.logger.error(f"❌ 重连异常: {e}")
            self.reconnect_attempts += 1

    async def _connection_monitor(self):
        """连接状态监控"""
        while self._running:
            try:
                # 检查连接状态
                if not self.connection or self.connection.is_closed:
                    self.logger.warning("⚠️ 检测到连接断开，尝试重连...")
                    await self._reconnect_rabbitmq()

                # 每30秒检查一次
                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"❌ 连接监控异常: {e}")
                await asyncio.sleep(30)

    # === 外部接口 ===

    async def start(self):
        """启动消息代理"""
        self.logger.info("🚀 启动消息代理...")
        self._running = True

        try:
            # 1. 验证认证信息已由Agent提供
            if not self.jwt_token or not self.rabbit_config:
                raise Exception("未提供JWT Token或RabbitMQ配置信息，无法启动消息代理")

            self.logger.info("🔑 使用Agent提供的JWT认证信息")

            # 2. 连接RabbitMQ
            self.logger.info("🔌 开始连接RabbitMQ...")
            connect_result = await self._connect_rabbitmq()
            self.logger.info(f"🔌 RabbitMQ连接结果: {connect_result}")

            if not connect_result:
                raise Exception("RabbitMQ连接失败")

            # 3. 设置消费者
            self.logger.info("📡 开始设置队列消费者...")
            consumer_result = await self._setup_queue_consumer()
            self.logger.info(f"📡 消费者设置结果: {consumer_result}")

            if not consumer_result:
                raise Exception("设置消费者失败")

            # 4. 启动后台任务
            self._token_refresh_task = asyncio.create_task(self._token_refresh_loop())
            self._reconnect_task = asyncio.create_task(self._connection_monitor())

            self.logger.info("✅ 消息代理启动成功")

        except Exception as e:
            self.logger.error(f"❌ 启动消息代理失败: {e}")
            import traceback

            self.logger.error(f"❌ 错误详情: {traceback.format_exc()}")
            await self.stop()
            raise

    async def stop(self):
        """停止消息代理"""
        self.logger.info("📴 停止消息代理...")
        self._running = False

        try:
            # 取消后台任务
            if self._token_refresh_task:
                self._token_refresh_task.cancel()
                try:
                    await self._token_refresh_task
                except asyncio.CancelledError:
                    pass

            if self._reconnect_task:
                self._reconnect_task.cancel()
                try:
                    await self._reconnect_task
                except asyncio.CancelledError:
                    pass

            # 关闭RabbitMQ连接
            if self.connection:
                await self.connection.close()

            self.logger.info("✅ 消息代理已停止")

        except Exception as e:
            self.logger.error(f"停止消息代理时出错: {e}")

    def is_connected(self) -> bool:
        """检查连接状态"""
        return (
            self.connection is not None
            and not self.connection.is_closed
            and self.channel is not None
            and not self.channel.is_closed
        )

    def get_queue_info(self) -> Dict[str, Any]:
        """获取队列信息"""
        return {
            "queue_name": self.queue_name,
            "connected": self.is_connected(),
            "jwt_token_valid": self.token_expires_at
            and (self.token_expires_at > int(time.time())),
            "running": self._running,
        }

    def get_retry_stats(self) -> Dict[str, Any]:
        """获取消息处理重试统计

        Returns:
            包含以下字段的字典：
            - total_messages: 总处理消息数
            - successful: 一次成功的消息数
            - retried_success: 重试后成功的消息数
            - failed_to_dlq: 失败进入死信队列的消息数
            - failed_immediate: 立即失败（不可重试）的消息数
            - by_error_type: 按错误类型统计的详细信息
            - success_rate: 成功率（百分比）
            - retry_config: 重试配置信息
        """
        total = self._retry_stats["total_messages"]
        successful = (
            self._retry_stats["successful"] + self._retry_stats["retried_success"]
        )
        success_rate = (successful / total * 100) if total > 0 else 0

        return {
            "summary": {
                "total_messages": total,
                "successful": self._retry_stats["successful"],
                "retried_success": self._retry_stats["retried_success"],
                "failed_to_dlq": self._retry_stats["failed_to_dlq"],
                "failed_immediate": self._retry_stats["failed_immediate"],
                "success_rate": f"{success_rate:.2f}%",
            },
            "by_error_type": self._retry_stats["by_error_type"],
            "retry_config": {
                "max_retries": self.max_retries,
                "retry_delays": self.retry_delays,
                "enable_dead_letter_queue": self.enable_dead_letter_queue,
            },
            "timestamp": int(time.time()),
        }

    def reset_retry_stats(self):
        """重置重试统计数据"""
        self._retry_stats = {
            "total_messages": 0,
            "successful": 0,
            "retried_success": 0,
            "failed_to_dlq": 0,
            "failed_immediate": 0,
            "by_error_type": {},
        }
        self.logger.info("✅ 重试统计已重置")

    def __repr__(self) -> str:
        """字符串表示"""
        status = "运行中" if self._running else "已停止"
        connection_status = "已连接" if self.is_connected() else "未连接"
        return f"MessageBroker({self.queue_name}, {status}, {connection_status})"
