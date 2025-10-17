"""配置管理"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class Config:
    """配置管理类

    支持环境变量、配置文件和构造参数的配置方式，
    按优先级：构造参数 > 环境变量 > 默认值
    """

    def __init__(self, **kwargs):
        """初始化配置

        Args:
            **kwargs: 配置参数
        """
        # 自动加载 .env 文件
        self._load_dotenv()
        self._config = kwargs

    def _load_dotenv(self):
        """加载 .env 文件"""
        if not DOTENV_AVAILABLE:
            return

        # 查找 .env 文件的位置
        # 1. 当前工作目录
        # 2. 脚本所在目录
        # 3. 项目根目录（查找包含 setup.py 的目录）

        search_paths = [
            Path.cwd(),  # 当前工作目录
            Path(__file__).parent.parent.parent,  # uni-agent-sdk 根目录
        ]

        # 添加项目根目录（查找包含 setup.py 的目录）
        current = Path.cwd()
        while current != current.parent:
            if (current / "setup.py").exists():
                search_paths.insert(0, current)
                break
            current = current.parent

        # 尝试加载 .env 文件
        for path in search_paths:
            env_file = path / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                break

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        # 优先级：构造参数 > 环境变量 > 默认值
        if key in self._config:
            return self._config[key]

        env_key = key.upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置值"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置值"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置值"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # 平台配置
    @property
    def platform_base_url(self) -> str:
        """平台API基础URL"""
        return self.get(
            "platform_base_url",
            "https://fc-mp-8234fa2c-3eb4-4a22-8a8c-9a0ee3e97513.next.bspapp.com",
        )

    @property
    def connectcode(self) -> str:
        """平台连接代码 - S2S认证必需"""
        return self.get("connectcode", "")

    # RabbitMQ配置
    @property
    def rabbitmq_host(self) -> str:
        """RabbitMQ主机"""
        return self.get("rabbitmq_host", "115.190.75.7")

    @property
    def rabbitmq_port(self) -> int:
        """RabbitMQ端口"""
        return self.get_int("rabbitmq_port", 5673)

    @property
    def rabbitmq_vhost(self) -> str:
        """RabbitMQ虚拟主机"""
        return self.get("rabbitmq_vhost", "/dev")

    @property
    def rabbitmq_user(self) -> str:
        """RabbitMQ用户名"""
        return self.get("rabbitmq_username", "guest")

    @property
    def rabbitmq_password(self) -> str:
        """RabbitMQ密码"""
        return self.get("rabbitmq_password", "guest")

    # LLM配置
    @property
    def openrouter_api_key(self) -> Optional[str]:
        """OpenRouter API密钥"""
        return self.get("openrouter_api_key")

    @property
    def openrouter_base_url(self) -> str:
        """OpenRouter API基础URL"""
        return self.get("openrouter_base_url", "https://openrouter.ai/api/v1")

    @property
    def kimi_api_key(self) -> Optional[str]:
        """Kimi API密钥"""
        return self.get("kimi_api_key")

    @property
    def kimi_base_url(self) -> str:
        """Kimi API基础URL"""
        return self.get("kimi_base_url", "https://api.moonshot.cn/v1")

    @property
    def default_model(self) -> str:
        """默认LLM模型"""
        return self.get("default_model", "kimi-k2-turbo-preview")

    @property
    def default_temperature(self) -> float:
        """默认温度参数"""
        return self.get_float("default_temperature", 0.7)

    @property
    def default_max_tokens(self) -> int:
        """默认最大token数"""
        return self.get_int("default_max_tokens", 1000)

    # HTTP配置
    @property
    def http_timeout(self) -> int:
        """HTTP超时时间（秒）"""
        return self.get_int("http_timeout", 30)

    @property
    def http_connect_timeout(self) -> int:
        """HTTP连接超时时间（秒）"""
        return self.get_int("http_connect_timeout", 10)

    @property
    def http_retry_times(self) -> int:
        """HTTP重试次数"""
        return self.get_int("http_retry_times", 3)

    # 日志配置
    @property
    def log_level(self) -> str:
        """日志级别"""
        level = self.get("log_level", "INFO").upper()
        return getattr(logging, level, logging.INFO)

    @property
    def log_format(self) -> str:
        """日志格式"""
        return self.get(
            "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # 文件服务配置
    @property
    def upload_base_url(self) -> str:
        """文件上传基础URL"""
        return self.get("upload_base_url", "https://upload.example.com")

    @property
    def download_dir(self) -> str:
        """下载目录"""
        return self.get("download_dir", "./downloads")

    @property
    def max_file_size(self) -> int:
        """最大文件大小（字节）"""
        return self.get_int("max_file_size", 100 * 1024 * 1024)  # 100MB

    # 性能配置
    @property
    def max_workers(self) -> int:
        """最大工作线程数"""
        return self.get_int("max_workers", 4)

    @property
    def message_queue_size(self) -> int:
        """消息队列大小"""
        return self.get_int("message_queue_size", 100)

    @property
    def prefetch_count(self) -> int:
        """RabbitMQ预取消息数"""
        return self.get_int("prefetch_count", 1)

    # 安全配置
    @property
    def enable_signature_verify(self) -> bool:
        """是否启用签名验证"""
        return self.get_bool("enable_signature_verify", True)

    # 文件服务配置
    @property
    def file_upload_retry_times(self) -> int:
        """文件上传重试次数"""
        return self.get_int("file_upload_retry_times", 3)

    @property
    def file_upload_timeout(self) -> int:
        """文件上传超时时间（秒）"""
        return self.get_int("file_upload_timeout", 60)

    # 消息服务配置
    @property
    def message_retry_times(self) -> int:
        """消息发送重试次数"""
        return self.get_int("message_retry_times", 3)

    @property
    def message_max_retries(self) -> int:
        """消息处理最大重试次数（用于消息处理失败时的重试）"""
        return self.get_int("message_max_retries", 3)

    @property
    def message_retry_delays(self) -> list:
        """消息重试延迟（秒）- 指数退避策略

        默认为 [1, 2, 4] 表示 1秒、2秒、4秒的延迟
        """
        delays_str = self.get("message_retry_delays", "1,2,4")
        try:
            return [int(d.strip()) for d in delays_str.split(",")]
        except (ValueError, AttributeError):
            return [1, 2, 4]

    @property
    def enable_dead_letter_queue(self) -> bool:
        """是否启用死信队列（重试失败后发送）"""
        return self.get_bool("enable_dead_letter_queue", True)

    @property
    def enable_markdown_processing(self) -> bool:
        """是否启用Markdown处理"""
        return self.get_bool("enable_markdown_processing", True)

    @property
    def enable_html_reports(self) -> bool:
        """是否启用HTML报告功能"""
        return self.get_bool("enable_html_reports", True)

    @property
    def signature_expire_time(self) -> int:
        """签名过期时间（秒）"""
        return self.get_int("signature_expire_time", 300)

    def validate(self) -> Dict[str, str]:
        """验证配置

        Returns:
            验证错误信息字典，空字典表示验证通过
        """
        errors = {}

        # 验证必需配置 - 至少需要一个 AI API 密钥
        if not self.openrouter_api_key and not self.kimi_api_key:
            errors["ai_api_key"] = (
                "需要设置 OpenRouter API 密钥或 Kimi API 密钥其中之一"
            )

        if not self.rabbitmq_host:
            errors["rabbitmq_host"] = "RabbitMQ主机未设置"

        if not self.platform_base_url:
            errors["platform_base_url"] = "平台API基础URL未设置"

        # 验证CONNECTCODE必需配置（S2S认证必需）
        if not self.connectcode:
            errors["connectcode"] = (
                "CONNECTCODE是S2S认证的必需配置，无法与uni-im云函数通信"
            )

        # 验证数值范围
        if self.http_timeout <= 0:
            errors["http_timeout"] = "HTTP超时时间必须大于0"

        if self.default_temperature < 0 or self.default_temperature > 2:
            errors["default_temperature"] = "温度参数必须在0-2之间"

        if self.default_max_tokens <= 0:
            errors["default_max_tokens"] = "最大token数必须大于0"

        # 验证文件配置
        if self.max_file_size <= 0:
            errors["max_file_size"] = "最大文件大小必须大于0"

        if self.file_upload_retry_times < 0:
            errors["file_upload_retry_times"] = "文件上传重试次数不能小于0"

        if self.message_retry_times < 0:
            errors["message_retry_times"] = "消息重试次数不能小于0"

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "platform_base_url": self.platform_base_url,
            "rabbitmq_host": self.rabbitmq_host,
            "rabbitmq_port": self.rabbitmq_port,
            "rabbitmq_vhost": self.rabbitmq_vhost,
            "rabbitmq_user": self.rabbitmq_user,
            "openrouter_base_url": self.openrouter_base_url,
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "http_timeout": self.http_timeout,
            "log_level": logging.getLevelName(self.log_level),
            "max_workers": self.max_workers,
            "enable_signature_verify": self.enable_signature_verify,
            "max_file_size": self.max_file_size,
            "file_upload_retry_times": self.file_upload_retry_times,
            "file_upload_timeout": self.file_upload_timeout,
            "message_retry_times": self.message_retry_times,
            "enable_markdown_processing": self.enable_markdown_processing,
            "enable_html_reports": self.enable_html_reports,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        config_dict = self.to_dict()
        # 隐藏敏感信息
        if "openrouter_api_key" in config_dict:
            config_dict["openrouter_api_key"] = "***"
        if "rabbitmq_password" in config_dict:
            config_dict["rabbitmq_password"] = "***"
        return f"Config({config_dict})"
