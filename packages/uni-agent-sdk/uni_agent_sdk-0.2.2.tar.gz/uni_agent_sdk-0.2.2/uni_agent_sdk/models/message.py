"""消息和响应数据模型"""

from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


class Message(BaseModel):
    """接收消息模型"""

    id: str = Field(..., description="消息ID")
    from_uid: str = Field(..., description="发送者用户ID")
    to_uid: str = Field(..., description="接收者用户ID（智能体ID）")
    conversation_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="消息内容")
    message_type: str = Field(default="text", description="消息类型")
    create_time: int = Field(..., description="创建时间戳")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建消息对象"""
        return cls(
            id=data.get("messageId", ""),
            from_uid=data.get("fromUserId", ""),
            to_uid=data.get("toUserId", ""),
            conversation_id=data.get("conversationId", ""),
            content=data.get("content", ""),
            message_type=data.get("messageType", "text"),
            create_time=data.get("createTime", 0),
        )


class Response(BaseModel):
    """响应消息模型"""

    content: str = Field(..., description="响应内容")
    response_type: str = Field(default="text", description="响应类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    @classmethod
    def text(cls, content: str, **kwargs) -> "Response":
        """创建文本响应"""
        return cls(content=content, response_type="text", metadata=kwargs)

    @classmethod
    def image(cls, image_url: str, caption: str = "", **kwargs) -> "Response":
        """创建图片响应"""
        return cls(
            content=caption,
            response_type="image",
            metadata={"image_url": image_url, **kwargs},
        )

    @classmethod
    def file(cls, file_url: str, filename: str, **kwargs) -> "Response":
        """创建文件响应"""
        return cls(
            content=filename,
            response_type="file",
            metadata={"file_url": file_url, "filename": filename, **kwargs},
        )

    def to_platform_format(self) -> Dict[str, Any]:
        """转换为平台API格式"""
        # 对 htmlReport 类型特殊处理
        if self.response_type == "htmlReport":
            return {
                "type": self.response_type,
                "content": self.content,
                "body": self.metadata,  # html_report 需要 body 是结构化对象
                **self.metadata,
            }
        else:
            return {
                "type": self.response_type,
                "content": self.content,
                "body": self.content,
                **self.metadata,
            }
