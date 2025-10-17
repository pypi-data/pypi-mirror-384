#!/usr/bin/env python3
"""智能体注册测试脚本

直接测试智能体注册API，获取详细的错误信息。
"""

import sys
import os
import asyncio
import aiohttp
import json

# 添加SDK路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uni_agent_sdk.utils.config import Config
from uni_agent_sdk import setup_agent_logging

async def test_robot_registration():
    """测试智能体注册功能"""

    print("🧪 开始智能体注册测试...")

    # 初始化配置
    config = Config()

    # 从环境变量获取API凭据
    api_key = config.get('robot_api_key', 'robot_test_api_key_deepseek')
    api_secret = config.get('robot_api_secret', 'test_api_secret_deepseek')
    platform_url = config.platform_base_url
    connectcode = config.connectcode

    print(f"📋 配置信息:")
    print(f"   API Key: {api_key}")
    print(f"   API Secret: {api_secret[:10]}...")
    print(f"   平台URL: {platform_url}")
    print(f"   Connect Code: {connectcode[:10] if connectcode else 'None'}...")

    # 准备注册数据
    data = {
        "api_key": api_key,
        "api_secret": api_secret
    }

    # 准备HTTP头
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'uni-agent-sdk/1.0'
    }

    # 添加 CONNECTCODE 头部用于 S2S 认证
    if connectcode:
        headers['Unicloud-S2s-Authorization'] = f'CONNECTCODE {connectcode}'
        print(f"✅ 已添加S2S认证头")
    else:
        print(f"⚠️ 缺少CONNECTCODE，可能导致认证失败")

    try:
        url = f"{platform_url}/uni-im-co/registerRobot"

        print(f"\n🔗 请求URL: {url}")
        print(f"📦 请求数据: {json.dumps(data, indent=2)}")
        print(f"📤 请求头: {json.dumps(headers, indent=2)}")

        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"\n🚀 发送注册请求...")

            async with session.post(url, json=data, headers=headers) as resp:
                print(f"📈 HTTP状态码: {resp.status}")
                print(f"📋 响应头: {dict(resp.headers)}")

                try:
                    result = await resp.json()
                    print(f"📄 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")

                    if result.get('errCode') == 0:
                        print(f"✅ 注册成功！")
                        data = result.get('data', {})
                        if 'robot_info' in data:
                            robot_info = data['robot_info']
                            print(f"🤖 智能体信息:")
                            print(f"   ID: {robot_info.get('robot_id')}")
                            print(f"   名称: {robot_info.get('name')}")
                            print(f"   队列: {robot_info.get('queue_name')}")
                        if 'rabbitmq_config' in data:
                            rabbitmq = data['rabbitmq_config']
                            print(f"🐰 RabbitMQ配置:")
                            print(f"   主机: {rabbitmq.get('host')}")
                            print(f"   端口: {rabbitmq.get('port')}")
                            print(f"   虚拟主机: {rabbitmq.get('vhost')}")
                    else:
                        error_msg = result.get('errMsg', '未知错误')
                        print(f"❌ 注册失败: {error_msg}")

                        # 分析常见错误
                        if 'API凭据无效' in error_msg or 'invalid' in error_msg.lower():
                            print(f"🔍 可能的解决方案:")
                            print(f"   1. 检查.env文件中的ROBOT_API_KEY和ROBOT_API_SECRET")
                            print(f"   2. 确认API凭据是否在平台注册")
                            print(f"   3. 验证CONNECTCODE是否正确")

                except json.JSONDecodeError:
                    text = await resp.text()
                    print(f"❌ 无法解析JSON响应: {text}")

                if resp.status != 200:
                    print(f"❌ HTTP请求失败: {resp.status}")
                    return False

    except Exception as e:
        print(f"❌ 请求过程中出错: {e}")
        return False

    return True

async def test_connectivity():
    """测试基础连接性"""
    config = Config()
    platform_url = config.platform_base_url

    print(f"\n🔍 测试平台连接性...")
    print(f"🔗 平台URL: {platform_url}")

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 测试基础连接
            async with session.get(platform_url) as resp:
                print(f"📈 连接状态: {resp.status}")
                if resp.status == 200:
                    print(f"✅ 平台连接正常")
                else:
                    print(f"⚠️ 平台响应异常: {resp.status}")

    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    # 设置日志
    setup_agent_logging()

    print("🚀 启动智能体注册测试")

    async def main():
        await test_connectivity()
        await test_robot_registration()

    asyncio.run(main())
    print("🏁 测试完成")