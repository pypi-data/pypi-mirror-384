"""生命周期管理 - 智能体启动和关闭流程控制

统一管理智能体的生命周期，包括启动顺序、依赖检查、
健康监控、优雅关闭等企业级功能。

设计原则：
- 确保启动顺序：配置 -> 连接 -> 服务 -> 监听
- 健康检查：定期检查各组件状态
- 优雅关闭：确保资源正确释放
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ..agent import Agent


class LifecycleManager:
    """生命周期管理器

    管理智能体的完整生命周期：
    - 启动阶段：配置验证、服务初始化、连接建立
    - 运行阶段：健康检查、状态监控、性能统计
    - 关闭阶段：优雅停止、资源清理、状态保存
    """

    def __init__(self, agent: "Agent"):
        """初始化生命周期管理器

        Args:
            agent: 智能体实例
        """
        self.agent = agent
        self.logger = logging.getLogger(f"Lifecycle-{agent.api_key[:8]}")

        # 生命周期状态
        self.startup_time: Optional[float] = None
        self.shutdown_time: Optional[float] = None
        self.health_stats: Dict[str, Any] = {}

        # 健康检查任务
        self._health_check_task: Optional[asyncio.Task] = None
        self._stats_task: Optional[asyncio.Task] = None

    async def startup(self):
        """启动流程"""
        try:
            self.startup_time = time.time()
            self.logger.info("🚀 开始智能体启动流程...")

            # 1. 配置验证
            await self._validate_config()

            # 2. 初始化健康统计
            await self._init_health_stats()

            # 3. 启动监控任务
            await self._start_monitoring()

            self.logger.info("✅ 智能体启动流程完成")

        except Exception as e:
            self.logger.error(f"❌ 启动流程失败: {e}")
            raise

    async def shutdown(self):
        """关闭流程"""
        try:
            self.shutdown_time = time.time()
            self.logger.info("📴 开始智能体关闭流程...")

            # 1. 停止监控任务
            await self._stop_monitoring()

            # 2. 保存统计信息
            await self._save_stats()

            # 3. 显示运行统计
            await self._show_runtime_stats()

            self.logger.info("✅ 智能体关闭流程完成")

        except Exception as e:
            self.logger.error(f"❌ 关闭流程失败: {e}")

    # === 配置验证 ===

    async def _validate_config(self):
        """验证配置"""
        self.logger.info("🔧 验证配置...")

        # 验证必需配置
        errors = self.agent.config.validate()
        if errors:
            error_msg = "\n".join([f"  - {k}: {v}" for k, v in errors.items()])
            raise Exception(f"配置验证失败:\n{error_msg}")

        # 验证API密钥格式
        if not self.agent.api_key or len(self.agent.api_key) < 8:
            raise Exception("API密钥无效")

        # 验证平台连接（可选）
        # try:
        #     await self.agent.platform.get_robot_info()
        # except Exception as e:
        #     self.logger.warning(f"平台连接检查失败: {e}")

        self.logger.info("✅ 配置验证通过")

    # === 健康监控 ===

    async def _init_health_stats(self):
        """初始化健康统计"""
        self.health_stats = {
            "startup_time": self.startup_time,
            "message_count": 0,
            "response_count": 0,
            "error_count": 0,
            "last_message_time": None,
            "last_error_time": None,
            "connection_status": "unknown",
            "platform_status": "unknown",
            "memory_usage": 0,
            "uptime": 0,
        }

    async def _start_monitoring(self):
        """启动监控任务"""
        self.logger.info("📊 启动健康监控...")

        # 启动健康检查任务
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        # 启动统计任务
        self._stats_task = asyncio.create_task(self._stats_update_loop())

    async def _stop_monitoring(self):
        """停止监控任务"""
        self.logger.info("📊 停止健康监控...")

        # 取消健康检查任务
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # 取消统计任务
        if self._stats_task:
            self._stats_task.cancel()
            try:
                await self._stats_task
            except asyncio.CancelledError:
                pass

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await self._update_health_status()
                await asyncio.sleep(30)  # 每30秒检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查异常: {e}")
                await asyncio.sleep(30)

    async def _stats_update_loop(self):
        """统计更新循环"""
        while True:
            try:
                await self._update_stats()
                await asyncio.sleep(60)  # 每分钟更新一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"统计更新异常: {e}")
                await asyncio.sleep(60)

    async def _update_health_status(self):
        """更新健康状态"""
        try:
            # 检查RabbitMQ连接状态
            if hasattr(self.agent, "_message_broker") and self.agent._message_broker:
                self.health_stats["connection_status"] = (
                    "connected"
                    if self.agent.message_broker.is_connected()
                    else "disconnected"
                )
            else:
                self.health_stats["connection_status"] = "not_initialized"

            # 检查平台API状态（简化检查）
            self.health_stats["platform_status"] = "available"

            # 更新运行时间
            if self.startup_time:
                self.health_stats["uptime"] = int(time.time() - self.startup_time)

        except Exception as e:
            self.logger.debug(f"健康状态更新异常: {e}")

    async def _update_stats(self):
        """更新统计信息"""
        try:
            # 获取内存使用情况（简化）
            import os

            import psutil

            process = psutil.Process(os.getpid())
            self.health_stats["memory_usage"] = (
                process.memory_info().rss / 1024 / 1024
            )  # MB

        except ImportError:
            # psutil未安装时跳过内存监控
            pass
        except Exception as e:
            self.logger.debug(f"统计更新异常: {e}")

    # === 事件记录 ===

    def record_message_received(self):
        """记录消息接收"""
        self.health_stats["message_count"] += 1
        self.health_stats["last_message_time"] = time.time()

    def record_response_sent(self):
        """记录响应发送"""
        self.health_stats["response_count"] += 1

    def record_error(self, error: Exception):
        """记录错误"""
        self.health_stats["error_count"] += 1
        self.health_stats["last_error_time"] = time.time()
        self.logger.debug(f"记录错误: {error}")

    # === 统计报告 ===

    async def _save_stats(self):
        """保存统计信息"""
        # 简化实现：只记录到日志
        # 生产环境可以保存到文件或数据库
        self.logger.info(f"📊 运行统计: {self.health_stats}")

    async def _show_runtime_stats(self):
        """显示运行时统计"""
        if not self.startup_time:
            return

        runtime = time.time() - self.startup_time
        hours = int(runtime // 3600)
        minutes = int((runtime % 3600) // 60)
        seconds = int(runtime % 60)

        self.logger.info("📈 智能体运行统计:")
        self.logger.info(f"   ⏱️  运行时间: {hours}小时 {minutes}分钟 {seconds}秒")
        self.logger.info(
            f"   📩 处理消息: {self.health_stats.get('message_count', 0)} 条"
        )
        self.logger.info(
            f"   📤 发送响应: {self.health_stats.get('response_count', 0)} 条"
        )
        self.logger.info(
            f"   ❌ 错误次数: {self.health_stats.get('error_count', 0)} 次"
        )

        # 计算响应率
        msg_count = self.health_stats.get("message_count", 0)
        resp_count = self.health_stats.get("response_count", 0)
        if msg_count > 0:
            response_rate = (resp_count / msg_count) * 100
            self.logger.info(f"   📊 响应率: {response_rate:.1f}%")

        # 显示内存使用
        memory = self.health_stats.get("memory_usage", 0)
        if memory > 0:
            self.logger.info(f"   🧠 内存使用: {memory:.1f} MB")

    # === 健康检查接口 ===

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "status": "healthy" if self.is_healthy() else "unhealthy",
            "uptime": self.health_stats.get("uptime", 0),
            "connection_status": self.health_stats.get("connection_status", "unknown"),
            "platform_status": self.health_stats.get("platform_status", "unknown"),
            "message_count": self.health_stats.get("message_count", 0),
            "response_count": self.health_stats.get("response_count", 0),
            "error_count": self.health_stats.get("error_count", 0),
            "memory_usage": self.health_stats.get("memory_usage", 0),
            "last_message_time": self.health_stats.get("last_message_time"),
            "last_error_time": self.health_stats.get("last_error_time"),
        }

    def is_healthy(self) -> bool:
        """检查是否健康"""
        return (
            self.agent.is_running()
            and self.health_stats.get("connection_status") == "connected"
            and self.health_stats.get("platform_status") == "available"
        )

    def get_stats_summary(self) -> str:
        """获取统计摘要"""
        stats = self.get_health_status()
        status_emoji = "✅" if stats["status"] == "healthy" else "❌"

        return (
            f"{status_emoji} 状态: {stats['status']} | "
            f"⏱️ 运行: {stats['uptime']}s | "
            f"📩 消息: {stats['message_count']} | "
            f"📤 响应: {stats['response_count']} | "
            f"❌ 错误: {stats['error_count']}"
        )

    def __repr__(self) -> str:
        """字符串表示"""
        status = "健康" if self.is_healthy() else "异常"
        uptime = self.health_stats.get("uptime", 0)
        return f"LifecycleManager({status}, 运行{uptime}秒)"
