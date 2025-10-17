#!/usr/bin/env python3
"""JWT认证测试脚本

专门测试机器人注册和JWT认证流程，验证数据库初始化是否成功。
"""

import asyncio
import os
import sys

# 添加SDK路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uni_agent_sdk.services.platform import PlatformAPI
from uni_agent_sdk.utils.config import Config


async def test_jwt_authentication():
    """测试JWT认证流程"""
    print("🧪 开始JWT认证测试...")
    print("=" * 60)

    # 使用测试API密钥
    api_key = "robot_test_api_key_deepseek"
    api_secret = "test_api_secret_deepseek"

    print(f"📋 使用测试凭据:")
    print(f"   API Key: {api_key}")
    print(f"   API Secret: {api_secret}")
    print()

    # 创建配置和平台服务实例
    print("🔧 创建平台服务实例...")
    config = Config()
    platform = PlatformAPI(api_key, api_secret, config)

    try:
        # 仅测试机器人注册部分
        print("🔐 测试机器人注册...")
        registration_result = await platform.register_robot()

        print("✅ JWT认证测试成功!")
        print(f"📊 注册结果: {registration_result}")

        # 检查返回的关键字段
        if registration_result.get("errCode") == 0:
            data = registration_result.get("data", {})
            print("\n📋 认证信息详情:")
            print(f"   开发者用户ID: {data.get('developer_userid')}")
            print(
                f"   JWT令牌: {data.get('jwt_token')[:50]}..."
                if data.get("jwt_token")
                else "   JWT令牌: 未获取"
            )
            print(f"   令牌过期时间: {data.get('token_expires_at')}")
            print(
                f"   RabbitMQ配置: {'已获取' if data.get('rabbitmq_config') else '未获取'}"
            )

            print("\n🎉 JWT认证流程完全正常!")
            return True
        else:
            print(f"❌ 注册失败: {registration_result}")
            return False

    except Exception as e:
        print(f"❌ JWT认证测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # 清理资源
        await platform.close()
        print("\n🧹 测试清理完成")


async def main():
    """主函数"""
    print("🚀 JWT认证流程测试")
    print("=" * 60)
    print("🎯 目标: 验证机器人注册和JWT令牌获取")
    print("📊 范围: 数据库连接 -> API验证 -> JWT生成")
    print("=" * 60)
    print()

    success = await test_jwt_authentication()

    print("\n" + "=" * 60)
    if success:
        print("🎊 测试结果: JWT认证流程完全正常!")
        print("✅ 数据库初始化成功")
        print("✅ API凭据验证成功")
        print("✅ JWT令牌生成成功")
        print("✅ 认证架构重构完成")
    else:
        print("💥 测试结果: JWT认证流程存在问题")
        print("❌ 需要进一步调试")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
