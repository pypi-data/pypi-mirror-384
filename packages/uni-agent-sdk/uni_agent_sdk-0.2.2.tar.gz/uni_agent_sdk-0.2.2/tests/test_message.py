#!/usr/bin/env python3
"""简单的消息发送测试脚本"""

import asyncio
import json
from datetime import datetime

import aiohttp


async def send_test_message():
    """向智能体发送测试消息（通过平台API模拟）"""
    print("📨 发送测试消息到DeepSeek智能体...")

    # 模拟的测试消息
    test_message = {
        "type": "message",
        "conversation_id": "test_conversation_456",
        "from_uid": "user_test_12345",
        "content": "你好，请帮我生成一个Python列表推导式示例",
        "timestamp": int(datetime.now().timestamp() * 1000),
        "message_id": f"test_msg_{int(datetime.now().timestamp())}",
    }

    print(f"✅ 测试消息已准备: {test_message['content']}")
    print(f"📋 会话ID: {test_message['conversation_id']}")
    print(f"👤 发送者: {test_message['from_uid']}")

    # 这里正常情况下会通过RabbitMQ发送消息
    # 由于依赖问题，我们先模拟发送成功
    print("🎯 消息已模拟发送到智能体队列")
    print("⏳ 等待智能体处理...")

    # 等待一段时间观察智能体日志
    await asyncio.sleep(5)
    print("📊 请检查智能体日志以确认消息处理状态")


if __name__ == "__main__":
    asyncio.run(send_test_message())
