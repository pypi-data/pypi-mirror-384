"""消息上下文 - 智能的消息上下文管理

提供丰富的上下文信息，让智能体能够智能判断是否响应、
如何响应，以及获取用户、会话相关的详细信息。

核心功能：
- 自动判断消息类型（群聊/私聊、命令/普通消息）
- 提供用户信息（昵称、权限等）
- 智能响应决策（是否被@、关键词匹配等）
- 便捷的上下文访问方法
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..models.message import Message
    from ..services.platform import PlatformAPI
    from ..utils.config import Config


class MessageContext:
    """消息上下文 - 智能的上下文信息管理

    为智能体提供丰富的上下文信息，包括：
    - 用户信息（昵称、ID、权限等）
    - 会话信息（类型、历史等）
    - 智能判断方法（是否应该响应、命令解析等）
    """

    def __init__(
        self,
        message: "Message",
        user_info: Dict[str, Any],
        conversation_info: Dict[str, Any],
        config: "Config",
    ):
        """初始化上下文

        Args:
            message: 消息对象
            user_info: 用户信息
            conversation_info: 会话信息
            config: 配置对象
        """
        self.message = message
        self.user_info = user_info
        self.conversation_info = conversation_info
        self.config = config

        # 缓存解析结果
        self._parsed_command: Optional[Dict[str, Any]] = None
        self._is_group_chat: Optional[bool] = None
        self._mentioned_robot: Optional[bool] = None

    @classmethod
    async def create(
        cls, message: "Message", platform_api: "PlatformAPI", config: "Config"
    ) -> "MessageContext":
        """创建消息上下文（工厂方法）

        Args:
            message: 消息对象
            platform_api: 平台API服务
            config: 配置对象

        Returns:
            MessageContext实例
        """
        # 获取会话上下文（包含用户信息等）
        try:
            context_data = await platform_api.get_conversation_context(
                message.conversation_id
            )

            # 提取用户信息
            user_info = {
                "user_id": message.from_uid,
                "nickname": context_data.get("user_nickname", "未知用户"),
                "avatar": context_data.get("user_avatar", ""),
                "role": context_data.get("user_role", []),
                "permissions": context_data.get("user_permissions", []),
            }

            # 提取会话信息
            conversation_info = {
                "conversation_id": message.conversation_id,
                "type": context_data.get("conversation_type", "single"),
                "group_id": context_data.get("group_id"),
                "group_name": context_data.get("group_name"),
                "member_count": context_data.get("member_count", 0),
                "recent_messages": context_data.get("recent_messages", []),
            }

        except Exception as e:
            # 降级处理：使用基础信息
            user_info = {
                "user_id": message.from_uid,
                "nickname": "未知用户",
                "avatar": "",
                "role": [],
                "permissions": [],
            }

            conversation_info = {
                "conversation_id": message.conversation_id,
                "type": "single",  # 默认私聊
                "group_id": None,
                "group_name": None,
                "member_count": 0,
                "recent_messages": [],
            }

        return cls(message, user_info, conversation_info, config)

    # === 基础信息访问 ===

    @property
    def conversation_id(self) -> str:
        """会话ID"""
        return self.message.conversation_id

    @property
    def user_id(self) -> str:
        """发送者用户ID"""
        return self.message.from_uid

    @property
    def user_nickname(self) -> str:
        """发送者昵称"""
        return self.user_info.get("nickname", "未知用户")

    @property
    def user_avatar(self) -> str:
        """发送者头像URL"""
        return self.user_info.get("avatar", "")

    @property
    def user_role(self) -> List[str]:
        """发送者角色列表"""
        return self.user_info.get("role", [])

    @property
    def user_permissions(self) -> List[str]:
        """发送者权限列表"""
        return self.user_info.get("permissions", [])

    @property
    def message_content(self) -> str:
        """消息内容"""
        return self.message.content

    @property
    def message_type(self) -> str:
        """消息类型"""
        return self.message.message_type

    @property
    def create_time(self) -> datetime:
        """消息创建时间"""
        return datetime.fromtimestamp(self.message.create_time / 1000)

    # === 会话类型判断 ===

    @property
    def is_group_chat(self) -> bool:
        """是否为群聊"""
        if self._is_group_chat is None:
            self._is_group_chat = (
                self.conversation_info.get("type") == "group"
                or self.conversation_info.get("group_id") is not None
                or self.conversation_info.get("member_count", 0) > 2
            )
        return self._is_group_chat

    @property
    def is_private_chat(self) -> bool:
        """是否为私聊"""
        return not self.is_group_chat

    @property
    def group_name(self) -> Optional[str]:
        """群组名称（如果是群聊）"""
        return self.conversation_info.get("group_name")

    @property
    def member_count(self) -> int:
        """群成员数量"""
        return self.conversation_info.get("member_count", 0)

    # === 智能判断方法 ===

    def is_mentioned(self, robot_name: Optional[str] = None) -> bool:
        """检查是否被@或提及

        Args:
            robot_name: 机器人名称，如果不提供则检查通用@符号

        Returns:
            是否被提及
        """
        if self._mentioned_robot is None:
            content = self.message_content.lower()

            # 检查@符号
            mentioned = "@" in content

            # 如果提供了机器人名称，检查是否包含名称
            if robot_name:
                mentioned = mentioned or robot_name.lower() in content

            # 检查常见的呼叫词
            call_words = ["机器人", "ai", "智能体", "助手", "bot"]
            for word in call_words:
                if word in content:
                    mentioned = True
                    break

            self._mentioned_robot = mentioned

        return self._mentioned_robot

    def should_respond(self, robot_name: Optional[str] = None) -> bool:
        """智能判断是否应该响应

        Args:
            robot_name: 机器人名称

        Returns:
            是否应该响应
        """
        # 私聊总是响应
        if self.is_private_chat:
            return True

        # 群聊中被@或提及时响应
        if self.is_group_chat and self.is_mentioned(robot_name):
            return True

        # 检查是否是命令消息
        if self.is_command():
            return True

        # 默认不响应群聊中的普通消息
        return False

    def is_command(self, prefix: str = "/") -> bool:
        """检查是否为命令消息

        Args:
            prefix: 命令前缀，默认为 "/"

        Returns:
            是否为命令
        """
        return self.message_content.strip().startswith(prefix)

    def get_command(self, prefix: str = "/") -> Optional[Dict[str, Any]]:
        """解析命令

        Args:
            prefix: 命令前缀

        Returns:
            命令信息字典：{"command": "命令名", "args": ["参数列表"], "raw": "原始内容"}
        """
        if self._parsed_command is None and self.is_command(prefix):
            content = self.message_content.strip()
            if content.startswith(prefix):
                # 移除前缀
                command_text = content[len(prefix) :]

                # 分割命令和参数
                parts = command_text.split()
                if parts:
                    self._parsed_command = {
                        "command": parts[0].lower(),
                        "args": parts[1:],
                        "raw": command_text,
                    }

        return self._parsed_command

    def has_keyword(self, *keywords: str, case_sensitive: bool = False) -> bool:
        """检查消息是否包含关键词

        Args:
            *keywords: 关键词列表
            case_sensitive: 是否区分大小写

        Returns:
            是否包含任一关键词
        """
        content = self.message_content
        if not case_sensitive:
            content = content.lower()
            keywords = [kw.lower() for kw in keywords]

        return any(keyword in content for keyword in keywords)

    def match_pattern(self, pattern: str) -> Optional[re.Match]:
        """使用正则表达式匹配消息内容

        Args:
            pattern: 正则表达式模式

        Returns:
            匹配结果
        """
        return re.search(pattern, self.message_content)

    # === 权限检查 ===

    def has_role(self, role: str) -> bool:
        """检查用户是否具有指定角色

        Args:
            role: 角色名称

        Returns:
            是否具有角色
        """
        return role in self.user_role

    def has_permission(self, permission: str) -> bool:
        """检查用户是否具有指定权限

        Args:
            permission: 权限名称

        Returns:
            是否具有权限
        """
        return permission in self.user_permissions

    def is_admin(self) -> bool:
        """检查用户是否为管理员"""
        return self.has_role("admin") or self.has_permission("admin")

    def is_staff(self) -> bool:
        """检查用户是否为内部用户"""
        return self.has_role("staff") or self.has_permission("staff")

    # === 便捷方法 ===

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的消息历史

        Args:
            limit: 返回消息数量限制

        Returns:
            最近消息列表
        """
        recent = self.conversation_info.get("recent_messages", [])
        return recent[-limit:] if recent else []

    def format_user_mention(self) -> str:
        """格式化用户提及"""
        return f"@{self.user_nickname}"

    def get_response_context(self) -> Dict[str, Any]:
        """获取响应上下文信息（用于LLM提示）"""
        return {
            "user_name": self.user_nickname,
            "is_group_chat": self.is_group_chat,
            "group_name": self.group_name,
            "member_count": self.member_count,
            "is_mentioned": self.is_mentioned(),
            "is_command": self.is_command(),
            "command_info": self.get_command(),
            "user_roles": self.user_role,
            "message_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "conversation_type": "群聊" if self.is_group_chat else "私聊",
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message": {
                "id": self.message.id,
                "content": self.message.content,
                "type": self.message.message_type,
                "create_time": self.message.create_time,
            },
            "user": self.user_info,
            "conversation": self.conversation_info,
            "analysis": {
                "is_group_chat": self.is_group_chat,
                "is_mentioned": self.is_mentioned(),
                "should_respond": self.should_respond(),
                "is_command": self.is_command(),
                "command": self.get_command(),
            },
        }

    def __repr__(self) -> str:
        """字符串表示"""
        chat_type = "群聊" if self.is_group_chat else "私聊"
        return f"MessageContext({self.user_nickname}, {chat_type}, {self.message_content[:20]}...)"
