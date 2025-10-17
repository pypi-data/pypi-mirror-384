#!/usr/bin/env python3
"""Kimi API测试脚本

测试Kimi API配置是否正确工作
"""

import asyncio
import os

from openai import AsyncOpenAI


async def test_kimi_api():
    """测试Kimi API"""
    print("🧪 测试Kimi API配置...")
    print("=" * 50)

    # Kimi API配置
    api_key = "sk-WBOFCIXf0D3k2Bj9JjT41S99F4hMcd4G4zCMtqbyPkkZqT1R"
    base_url = "https://api.moonshot.cn/v1"
    model = "kimi-k2-turbo-preview"

    print(f"📋 API配置:")
    print(f"   模型: {model}")
    print(f"   API Base: {base_url}")
    print(f"   API Key: {api_key[:20]}...")
    print()

    try:
        # 创建客户端
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        print("🔤 发送测试消息...")

        # 测试消息
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
                },
                {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"},
            ],
            temperature=0.6,
        )

        response_content = completion.choices[0].message.content

        print("✅ Kimi API测试成功!")
        print("📤 AI回复:")
        print(f"   {response_content}")
        print()
        print("🎉 Kimi API配置正确，可以正常使用!")

        return True

    except Exception as e:
        print(f"❌ Kimi API测试失败: {e}")
        return False

    finally:
        await client.close()


async def main():
    """主函数"""
    print("🚀 Kimi API配置测试")
    print("=" * 50)

    success = await test_kimi_api()

    print("=" * 50)
    if success:
        print("🎊 测试结果: Kimi API配置成功!")
        print("✅ 现在可以使用Kimi进行智能对话")
    else:
        print("💥 测试结果: Kimi API配置失败")
        print("❌ 请检查API密钥和网络连接")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
