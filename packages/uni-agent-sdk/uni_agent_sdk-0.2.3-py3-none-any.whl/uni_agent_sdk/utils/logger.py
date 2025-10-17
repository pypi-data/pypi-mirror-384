"""
智能体SDK日志模块

提供统一的日志格式和配置，包含时间、日志等级、文件名:行号、内容
支持控制台输出和文件输出，以及不同的日志等级控制

使用示例：
    from uni_agent_sdk.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("这是一条信息日志")
    logger.error("这是一条错误日志")
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Union


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        # 获取颜色
        color = self.COLORS.get(record.levelname, "")

        # 格式化消息
        formatted = super().format(record)

        # 只在支持颜色的终端中添加颜色
        if color and hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            # 给日志级别添加颜色
            formatted = formatted.replace(
                record.levelname, f"{color}{record.levelname}{self.RESET}"
            )

        return formatted


class AgentLogger:
    """智能体日志管理器"""

    _instances = {}
    _default_config = {
        "level": logging.INFO,
        "format": "[%(asctime)s] [%(levelname)8s] [%(name)s] %(filename)s:%(lineno)d - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "console_output": True,
        "file_output": False,
        "file_path": None,
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5,
        "encoding": "utf-8",
    }

    def __init__(self, name: str, **config):
        self.name = name
        self.config = {**self._default_config, **config}
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        self.logger.setLevel(self.config["level"])

        # 清除现有的处理器，避免重复输出
        self.logger.handlers.clear()

        # 控制台输出
        if self.config["console_output"]:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = ColoredFormatter(
                fmt=self.config["format"], datefmt=self.config["date_format"]
            )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(self.config["level"])
            self.logger.addHandler(console_handler)

        # 文件输出
        if self.config["file_output"] and self.config["file_path"]:
            self._setup_file_handler()

    def _setup_file_handler(self):
        """设置文件输出处理器"""
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(self.config["file_path"])
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # 使用RotatingFileHandler支持日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.config["file_path"],
                maxBytes=self.config["max_file_size"],
                backupCount=self.config["backup_count"],
                encoding=self.config["encoding"],
            )

            # 文件输出不使用颜色
            file_formatter = logging.Formatter(
                fmt=self.config["format"], datefmt=self.config["date_format"]
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(self.config["level"])
            self.logger.addHandler(file_handler)

        except Exception as e:
            # 如果文件处理器设置失败，至少保证控制台输出正常
            print(f"Warning: Failed to setup file handler: {e}", file=sys.stderr)

    def set_level(self, level: Union[str, int]):
        """设置日志级别"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(message, *args, **kwargs)

    def warn(self, message: str, *args, **kwargs):
        """警告日志（别名）"""
        self.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """异常日志（自动包含异常堆栈）"""
        self.logger.exception(message, *args, **kwargs)


# 全局配置
_global_config = {}


def configure_logging(**config):
    """
    全局配置日志设置

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: 日志格式
        date_format: 时间格式
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        file_path: 日志文件路径
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的日志文件备份数量
        encoding: 文件编码
    """
    global _global_config
    _global_config.update(config)


def get_logger(name: Optional[str] = None, **config) -> AgentLogger:
    """
    获取日志器实例

    Args:
        name: 日志器名称，通常传入 __name__
        **config: 日志配置参数，会覆盖全局配置

    Returns:
        AgentLogger: 日志器实例
    """
    if name is None:
        name = "uni_agent_sdk"

    # 合并配置：全局配置 + 传入配置
    merged_config = {**_global_config, **config}

    # 使用单例模式，相同名称和配置的日志器只创建一次
    config_key = (name, tuple(sorted(merged_config.items())))

    if config_key not in AgentLogger._instances:
        AgentLogger._instances[config_key] = AgentLogger(name, **merged_config)

    return AgentLogger._instances[config_key]


def setup_agent_logging(
    level: Union[str, int] = logging.INFO,
    log_dir: Optional[str] = None,
    console: bool = True,
    file_logging: bool = False,
):
    """
    快速设置智能体日志配置

    Args:
        level: 日志级别
        log_dir: 日志目录，如果指定则启用文件日志
        console: 是否输出到控制台
        file_logging: 是否强制启用文件日志
    """
    config = {
        "level": level,
        "console_output": console,
    }

    if log_dir or file_logging:
        if not log_dir:
            log_dir = "./logs"

        # 生成日志文件名，包含时间戳
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"agent_{timestamp}.log")

        config.update({"file_output": True, "file_path": log_file})

    configure_logging(**config)


# 为了方便使用，提供默认的日志器
default_logger = None


def get_default_logger() -> AgentLogger:
    """获取默认日志器"""
    global default_logger
    if default_logger is None:
        default_logger = get_logger("uni_agent_sdk.default")
    return default_logger


# 便捷函数，直接使用默认日志器
def debug(message: str, *args, **kwargs):
    """调试日志"""
    get_default_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """信息日志"""
    get_default_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """警告日志"""
    get_default_logger().warning(message, *args, **kwargs)


def warn(message: str, *args, **kwargs):
    """警告日志（别名）"""
    get_default_logger().warn(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """错误日志"""
    get_default_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """严重错误日志"""
    get_default_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """异常日志（自动包含异常堆栈）"""
    get_default_logger().exception(message, *args, **kwargs)


if __name__ == "__main__":
    # 示例用法
    setup_agent_logging(level="DEBUG", console=True)

    logger = get_logger(__name__)
    logger.debug("这是调试信息")
    logger.info("智能体初始化完成")
    logger.warning("检测到配置项缺失，使用默认值")
    logger.error("连接服务器失败，正在重试...")
    logger.critical("系统内存不足，程序即将退出")

    try:
        1 / 0
    except Exception:
        logger.exception("发生除零错误")
