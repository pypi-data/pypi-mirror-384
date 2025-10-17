"""
uni-agent-sdk: 智能体开发SDK

极简的uni-im平台智能体开发框架，让开发者只需3行代码就能创建智能体。

使用示例：
    from uni_agent_sdk import Agent, Response

    class MyAgent(Agent):
        async def handle_message(self, message, context):
            return Response.text("你好！")

    MyAgent().run()
"""

__version__ = "0.1.0"
__author__ = "uni-im"

# 主要导出
from .agent import Agent
from .models.message import Message, Response
from .services.file import FileService
from .services.llm import LLMService
from .services.platform import PlatformAPI
from .utils.config import Config
from .utils.logger import get_logger, setup_agent_logging

__all__ = [
    "Agent",
    "Message",
    "Response",
    "LLMService",
    "PlatformAPI",
    "FileService",
    "Config",
    "get_logger",
    "setup_agent_logging",
]
