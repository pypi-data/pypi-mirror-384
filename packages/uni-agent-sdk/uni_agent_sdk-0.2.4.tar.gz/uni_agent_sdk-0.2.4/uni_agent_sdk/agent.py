"""Agent基类 - 智能体开发框架核心抽象

基于ultra-analysis深度分析结果设计的革命性智能体基类。
将400+行基础设施代码简化为3行业务逻辑。

设计原则：
- KISS: 极致简洁的开发体验
- SOLID: 科学的架构设计原则
- DRY: 统一的基础设施管理
- YAGNI: 专注当前需求实现
"""

import asyncio
import json
import logging
import signal
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import aiohttp

from .core.context import MessageContext
from .core.lifecycle import LifecycleManager
from .core.message_broker import MessageBroker
from .models.message import Message, Response
from .services.file import FileService
from .services.llm import LLMService
from .services.platform import PlatformAPI
from .utils.config import Config
from .utils.errors import (
    AuthenticationError,
    BusinessLogicError,
    ConfigurationError,
    InvalidMessageError,
    LLMRateLimitError,
    LLMTimeoutError,
    MessageFormatError,
    NetworkError,
    NonRetryableError,
    RetryableError,
    ServiceUnavailableError,
)
from .utils.logger import AgentLogger, get_logger


class Agent(ABC):
    """智能体基类

    提供极简的智能体开发体验：

    示例：
        from uni_agent_sdk import Agent, Response

        class MyAgent(Agent):
            async def handle_message(self, message, context):
                return Response.text("你好！")

        MyAgent("api_key", "api_secret").run()
    """

    def __init__(self, api_key: str, api_secret: str, **config_kwargs):
        """初始化智能体

        Args:
            api_key: 智能体API密钥
            api_secret: 智能体API秘钥
            **config_kwargs: 额外配置参数
        """
        self.api_key = api_key
        self.api_secret = api_secret

        # 初始化配置
        self.config = Config(**config_kwargs)

        # 使用新的日志模块 - 为每个智能体类创建专用日志器
        self.logger = get_logger(f"{self.__class__.__name__}-{api_key[:8]}")

        # 初始化状态
        self._running = False
        self._robot_info = None

        # 认证信息（通过register_robot获取）
        self._developer_userid = None
        self._jwt_token = None
        self._token_expires_at = None
        self._rabbitmq_config = None
        self._file_service_config = None

        # 延迟加载的服务（依赖注入）
        self._platform: Optional[PlatformAPI] = None
        self._llm: Optional[LLMService] = None
        self._files: Optional[FileService] = None
        self._message_broker: Optional[MessageBroker] = None
        self._lifecycle: Optional[LifecycleManager] = None

    # === 服务依赖注入（延迟加载） ===

    @property
    def platform(self) -> PlatformAPI:
        """平台API服务"""
        if self._platform is None:
            self._platform = PlatformAPI(self.api_key, self.api_secret, self.config)
            # 如果已有认证信息，立即设置
            if self._developer_userid and self._jwt_token:
                self._platform.set_auth_info(self._developer_userid, self._jwt_token)
        return self._platform

    @property
    def llm(self) -> LLMService:
        """LLM推理服务"""
        if self._llm is None:
            self._llm = LLMService(self.config)
        return self._llm

    @property
    def files(self) -> FileService:
        """增强文件处理服务"""
        if self._files is None:
            self._files = FileService(self.config)
        return self._files

    @property
    def message_broker(self) -> MessageBroker:
        """消息代理服务"""
        if self._message_broker is None:
            self._message_broker = MessageBroker(
                self.api_key,
                self.api_secret,
                self.config,
                self._on_message_received,
                self.logger,  # 传递Agent的logger
                self._jwt_token,  # 传递JWT Token
                self._token_expires_at,  # 传递Token过期时间
                self._rabbitmq_config,  # 传递RabbitMQ配置
                self._developer_userid,  # 传递developer_userid（用于Token刷新）
            )
        return self._message_broker

    @property
    def lifecycle(self) -> LifecycleManager:
        """生命周期管理器"""
        if self._lifecycle is None:
            self._lifecycle = LifecycleManager(self)
        return self._lifecycle

    # === 核心抽象方法 ===

    @abstractmethod
    async def handle_message(
        self, message: Message, context: MessageContext
    ) -> Optional[Response]:
        """处理接收到的消息（子类必须实现）

        Args:
            message: 接收到的消息对象
            context: 消息上下文（包含用户信息、会话状态等）

        Returns:
            响应对象，None表示不响应
        """
        pass

    # === 生命周期钩子（可选覆盖） ===

    async def on_startup(self):
        """启动钩子 - 智能体启动完成后调用"""
        self.logger.info(f"🚀 智能体 {self.api_key[:8]} 启动完成")

    async def on_shutdown(self):
        """关闭钩子 - 智能体停止前调用"""
        self.logger.info(f"📴 智能体 {self.api_key[:8]} 正在停止")

    async def on_error(
        self, error: Exception, context: Optional[MessageContext] = None
    ):
        """错误处理钩子 - 发生异常时调用"""
        self.logger.error(f"❌ 智能体错误: {error}")
        if context:
            self.logger.error(f"   上下文: {context.conversation_id}")

    # === 内部消息处理机制 ===

    async def _on_message_received(self, raw_message: Dict[str, Any]):
        """内部消息接收处理器

        处理流程：
        1. 解析原始消息（可能抛出 MessageFormatError）
        2. 创建消息上下文
        3. 调用用户处理逻辑（可能抛出各类可重试/不可重试错误）
        4. 发送响应

        此方法不处理重试逻辑，所有异常都由 MessageBroker 的 _process_message 捕获
        并根据错误类型决定是否重试。
        """
        context = None
        try:
            # 第一步：解析消息（可能失败）
            self.logger.debug(f"🔍 原始消息: {raw_message}")

            try:
                message = Message.from_dict(raw_message)
                self.logger.debug(
                    f"📝 解析后消息: id={message.id}, conversation_id={message.conversation_id}, from_uid={message.from_uid}"
                )
            except json.JSONDecodeError as e:
                # 消息格式错误 - 不可重试
                raise MessageFormatError(f"消息JSON解析失败: {e}")
            except (KeyError, TypeError, ValueError) as e:
                # 消息字段缺失或类型错误 - 不可重试
                raise InvalidMessageError(f"消息字段错误: {e}")

            # 第二步：创建上下文
            try:
                context = await MessageContext.create(
                    message=message, platform_api=self.platform, config=self.config
                )
            except Exception as e:
                # 上下文创建失败 - 根据具体错误分类
                if "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                    raise AuthenticationError(f"权限或认证错误: {e}")
                raise BusinessLogicError(f"创建消息上下文失败: {e}")

            self.logger.info(f"📩 收到消息: {message.content[:50]}...")
            self.logger.debug(f"   发送者: {context.user_nickname}")
            self.logger.debug(f"   会话: {message.conversation_id}")

            # 第三步：调用用户处理逻辑
            try:
                response = await self.handle_message(message, context)
            except asyncio.TimeoutError as e:
                # 处理超时 - 通常可重试
                raise LLMTimeoutError(f"消息处理超时: {e}")
            except aiohttp.ClientConnectorError as e:
                # 网络连接错误 - 可重试
                raise NetworkError(f"网络连接失败: {e}")
            except aiohttp.ClientSSLError as e:
                # SSL错误 - 可重试
                raise NetworkError(f"SSL连接失败: {e}")
            except Exception as e:
                # 检查是否包含特定的错误标记
                error_str = str(e).lower()

                if "rate limit" in error_str or "429" in error_str:
                    raise LLMRateLimitError(f"LLM限流: {e}")
                elif "timeout" in error_str:
                    raise LLMTimeoutError(f"处理超时: {e}")
                elif "connection" in error_str or "network" in error_str:
                    raise NetworkError(f"网络错误: {e}")
                elif "service unavailable" in error_str or "503" in error_str:
                    raise ServiceUnavailableError(f"服务不可用: {e}")
                elif "unauthorized" in error_str or "authentication" in error_str:
                    raise AuthenticationError(f"认证失败: {e}")
                elif "invalid" in error_str or "malformed" in error_str:
                    raise InvalidMessageError(f"无效数据: {e}")

                # 默认为业务逻辑错误 - 不可重试
                raise BusinessLogicError(f"业务处理失败: {e}")

            # 第四步：发送响应
            if response is not None:
                try:
                    await self.platform.send_response(
                        conversation_id=message.conversation_id,
                        response=response,
                        to_uid=message.from_uid,
                    )
                    self.logger.info(f"✅ 响应已发送: {response.content[:50]}...")
                except aiohttp.ClientError as e:
                    # 发送响应时网络错误 - 可重试
                    raise NetworkError(f"发送响应失败: {e}")
                except Exception as e:
                    # 其他发送错误
                    raise BusinessLogicError(f"发送响应异常: {e}")
            else:
                self.logger.debug("⏭️ 无需响应")

        except (RetryableError, NonRetryableError) as e:
            # 已分类的错误，直接抛出让 MessageBroker 处理
            await self.on_error(e, context)
            raise
        except Exception as e:
            # 未预期的异常，默认为不可重试
            await self.on_error(e, context)
            raise NonRetryableError(f"未预期的异常: {e}")

    # === 智能体运行控制 ===

    def run(self):
        """启动智能体（阻塞运行）

        这是主要的入口方法，设置信号处理并启动异步事件循环。
        """
        try:
            # 设置信号处理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.logger.info(f"🎯 启动智能体 {self.api_key[:8]}")
            self.logger.info("=" * 60)

            # 启动异步事件循环
            asyncio.run(self._run_async())

        except KeyboardInterrupt:
            self.logger.info("👋 用户手动停止")
        except Exception as e:
            import traceback
            self.logger.error(f"❌ 智能体运行错误: {e}")
            self.logger.error(f"❌ 完整堆栈跟踪:\n{traceback.format_exc()}")
        finally:
            self.logger.info("🏁 智能体已停止")

    async def _run_async(self):
        """异步运行逻辑"""
        try:
            self._running = True

            # 启动生命周期管理
            await self.lifecycle.startup()

            # 第一步：注册机器人并获取完整认证信息
            self.logger.info("🔐 执行机器人注册和认证...")
            registration_result = await self.platform.register_robot()
            self.logger.debug(f"注册响应: {registration_result}")

            # 增强的错误处理
            if registration_result is None:
                raise Exception("机器人注册API返回None，可能是网络错误或响应格式问题")

            if not isinstance(registration_result, dict):
                raise Exception(f"机器人注册API返回非字典格式: {type(registration_result)}")

            if registration_result.get("errCode") != 0:
                raise Exception(f"机器人注册失败: {registration_result.get('errMsg')}")
            self.logger.info("✅ 机器人注册API调用成功")

            # 保存注册信息 (使用OAuth2标准字段名)
            if "data" not in registration_result:
                raise Exception("机器人注册响应缺少data字段")

            reg_data = registration_result["data"]
            if reg_data is None:
                raise Exception("机器人注册响应中data为None")
            self._developer_userid = reg_data.get("developer_userid")
            self._jwt_token = reg_data.get("token")  # OAuth2标准字段名
            self._token_expires_at = reg_data.get("expires_at")  # OAuth2标准字段名
            self._rabbitmq_config = reg_data.get("rabbitmq_config")
            self._file_service_config = reg_data.get("file_service_config")

            # 详细的调试信息
            self.logger.info("🔍 注册返回的详细信息:")
            self.logger.info(f"   👤 开发者ID: {self._developer_userid}")
            self.logger.info(
                f"   🔑 JWT Token: {self._jwt_token[:50] if self._jwt_token else 'None'}..."
            )
            self.logger.info(f"   ⏰ Token过期时间: {self._token_expires_at}")
            self.logger.info(f"   🐰 RabbitMQ配置: {self._rabbitmq_config}")
            self.logger.info(
                f"   📁 文件服务配置: {'已获取' if self._file_service_config else '未获取'}"
            )

            # 初始化文件服务配置
            if self._file_service_config:
                await self.files.init_from_platform_config(self._file_service_config)
                self.logger.info(
                    "✅ 文件服务配置已初始化，密钥有效期至: {}".format(
                        self._file_service_config.get("expires_at")
                    )
                )
            else:
                self.logger.error("❌ 未获取到文件服务配置，文件上传功能不可用")

            # 更新PlatformAPI的认证信息
            self.platform.set_auth_info(self._developer_userid, self._jwt_token)

            # 如果注册直接返回了robot_info，使用它；否则调用get_robot_info
            if "robot_info" in reg_data and reg_data["robot_info"] is not None:
                self._robot_info = reg_data["robot_info"]
                self.logger.info("🎉 机器人注册成功！")
                self.logger.info(f"👤 开发者ID: {self._developer_userid}")
                self.logger.info(
                    f"🤖 智能体: {self._robot_info.get('name', 'Unknown')}"
                )
                self.logger.info(f"🔑 JWT令牌已获取")
            else:
                # 第二步：使用JWT令牌获取详细的机器人信息（如果需要）
                self.logger.info("🔍 获取详细机器人信息...")
                robot_info = await self.platform.get_robot_info()
                if robot_info.get("errCode") != 0:
                    raise Exception(f"获取智能体信息失败: {robot_info.get('errMsg')}")

                self._robot_info = robot_info["data"]
                self.logger.info(
                    f"🤖 智能体: {self._robot_info.get('name', 'Unknown')}"
                )

            # 启动消息代理
            self.logger.info("准备启动消息代理...")
            self.logger.info(f"🔍 消息代理实例: {self.message_broker}")
            self.logger.info("🔄 开始调用消息代理start方法...")
            try:
                await self.message_broker.start()
                self.logger.info("✅ 消息代理start方法调用成功")
            except Exception as e:
                self.logger.error(f"❌ 消息代理启动异常: {e}")
                import traceback

                self.logger.error(f"❌ 异常堆栈: {traceback.format_exc()}")
                raise
            self.logger.info("消息代理启动完成")

            # 调用用户启动钩子
            await self.on_startup()

            # 保持运行
            while self._running:
                await asyncio.sleep(1)

        except Exception as e:
            await self.on_error(e)
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self):
        """清理资源"""
        try:
            # 调用用户关闭钩子
            await self.on_shutdown()

            # 停止消息代理
            if self._message_broker:
                await self.message_broker.stop()

            # 关闭服务连接
            if self._platform:
                await self.platform.close()

            # 关闭文件服务
            if self._files:
                await self.files.close()

            # 停止生命周期管理
            if self._lifecycle:
                await self.lifecycle.shutdown()

        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info(f"收到信号 {signum}")
        self.stop()

    def stop(self):
        """停止智能体"""
        self._running = False
        self.logger.info("⏹️ 收到停止信号")

    # === SDK功能增强方法 ===

    async def send_html_report(
        self,
        title: str,
        content: str,
        conversation_id: str,
        to_uid: str,
        summary: str = None,
        options: dict = None,
    ) -> dict:
        """生成HTML报告并发送给用户

        Args:
            title: 报告标题
            content: 完整的HTML内容
            conversation_id: 会话ID
            to_uid: 接收用户ID
            summary: 报告摘要，用于消息预览
            options: 额外选项

        Returns:
            发送结果，包含上传的文件信息和消息发送状态
        """

        async def _upload_and_send():
            # 第一步：将HTML内容转换为bytes并上传到云存储
            html_bytes = content.encode("utf-8")
            file_result = await self.upload_file(html_bytes, f"{title}.html")

            self.logger.info(f"HTML报告已上传: {file_result.get('file_url')}")

            # 第二步：格式化HTML报告消息
            message_data = self.message_service.format_html_report_message(
                title=title,
                file_url=file_result["file_url"],
                summary=summary or f"📊 {title}",
            )

            # 第三步：创建Response对象并发送给用户
            response = Response(
                content=f"📊 **{title}**\n\n{summary or '点击下方链接查看完整HTML报告'}\n\n🔗 [查看报告]({file_result['file_url']})",
                message_type="markdown",
                attachments=[
                    {
                        "type": "html_report",
                        "title": title,
                        "url": file_result["file_url"],
                        "summary": summary,
                    }
                ],
            )

            # 第四步：通过平台API发送消息
            send_result = await self.platform.send_response(
                conversation_id=conversation_id, response=response, to_uid=to_uid
            )

            self.logger.info(f"HTML报告消息已发送: {title}")

            return {
                "success": True,
                "file_info": file_result,
                "message_info": send_result,
                "report_url": file_result["file_url"],
            }

        return await _upload_and_send()

    async def create_html_report_response(
        self, title: str, content: str, summary: str = None, options: dict = None
    ) -> Response:
        """创建HTML报告响应对象（用于handle_message中返回）

        Args:
            title: 报告标题
            content: 完整的HTML内容
            summary: 报告摘要，用于消息预览
            options: 额外选项

        Returns:
            Response对象，可在handle_message中直接返回
        """

        async def _upload_and_create_response():
            self.logger.info(
                f"🔍 [create_html_report_response] 接收到options: {options}"
            )

            # 检查options中是否已有文件URL
            if options and options.get("file_url"):
                self.logger.info(
                    f"📁 [发现已上传文件] 使用现有文件URL: {options.get('file_url')}"
                )
                file_result = {
                    "file_url": options.get("file_url"),
                    "filename": options.get("file_name", f"{title}.html"),
                    "size": options.get("file_size", 0),
                }
            else:
                # 将HTML内容转换为bytes并上传到云存储
                self.logger.info(f"📤 [第二次上传] 开始上传HTML内容到云存储...")
                html_bytes = content.encode("utf-8")
                file_result = await self.upload_file(html_bytes, f"{title}.html")
                self.logger.info(
                    f"📁 [第二次上传] HTML报告已上传: {file_result.get('file_url')}"
                )

            self.logger.info(f"🔗 [最终文件URL] {file_result.get('file_url')}")

            # 创建HTML报告卡片响应对象
            # content 必须是字符串，结构化数据放在 metadata 中
            metadata = {
                "title": title,
                "summary": summary
                or "这是一份智能体生成的HTML报告，点击查看完整内容。",
                "file_url": file_result.get("file_url"),
                "url": file_result.get("file_url"),
                "display_text": (
                    options.get("display_text")
                    if options
                    else f"点击查看完整的智能体测试报告，包含性能指标、功能验证等详细信息。"
                ),
                "file_name": file_result.get(
                    "filename", options.get("file_name") if options else f"{title}.html"
                ),
                "file_size": file_result.get(
                    "size", options.get("file_size") if options else 0
                ),
                "file_info": file_result,
            }

            self.logger.info(f"📋 [元数据创建] metadata: {metadata}")

            return Response(
                content=f"📊 {title}", response_type="htmlReport", metadata=metadata
            )

        return await _upload_and_create_response()

    def create_markdown_response(self, content: str) -> Response:
        """创建Markdown响应对象（用于handle_message中返回）

        Args:
            content: Markdown内容

        Returns:
            Response对象，可在handle_message中直接返回
        """
        return Response(content=content, message_type="markdown")

    async def send_markdown(self, content: str, options: dict = None) -> dict:
        """发送Markdown格式消息

        Args:
            content: Markdown内容
            options: 额外选项

        Returns:
            消息数据
        """
        return await self.message_service.send_markdown(content, options)

    async def send_message(
        self, content: str, message_type: str = "text", options: dict = None
    ) -> dict:
        """统一的消息发送接口

        Args:
            content: 消息内容
            message_type: 消息类型 ('text', 'markdown', 'image', 'file')
            options: 额外选项

        Returns:
            消息数据
        """
        if message_type == "markdown":
            return await self.send_markdown(content, options)
        else:
            return await self.message_service.send_message(
                content, message_type, options
            )

    async def upload_file(
        self, file_data: bytes, filename: str, options: dict = None
    ) -> dict:
        """上传文件数据到云存储

        Args:
            file_data: 文件二进制数据
            filename: 文件名
            options: 额外选项

        Returns:
            上传结果，包含file_url等信息
        """

        async def _upload_with_temp_file():
            import os
            import tempfile

            # 验证文件大小
            max_size = (
                options.get("max_size", 10 * 1024 * 1024)
                if options
                else 10 * 1024 * 1024
            )
            if len(file_data) > max_size:
                raise ValueError(f"文件过大: {len(file_data)} bytes > {max_size} bytes")

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(filename)[1]
            ) as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name

            try:
                # 使用增强的文件服务上传（带重试）
                result = await self.files.upload_file_with_retry(
                    file_path=temp_file_path, filename=filename, max_retries=3
                )
                return result
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)

        return await _upload_with_temp_file()

    # === 便捷方法 ===

    def is_running(self) -> bool:
        """检查智能体是否运行中"""
        return self._running

    def get_robot_info(self) -> Optional[Dict[str, Any]]:
        """获取智能体信息"""
        return self._robot_info

    def __repr__(self) -> str:
        """字符串表示"""
        status = "运行中" if self._running else "已停止"
        return f"Agent({self.api_key[:8]}..., {status})"
