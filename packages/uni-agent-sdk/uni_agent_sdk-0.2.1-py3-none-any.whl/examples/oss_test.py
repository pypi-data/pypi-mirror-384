#!/usr/bin/env python3
"""OSS功能独立测试脚本

专门测试HTML文件上传到OSS的功能，不依赖平台认证。
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加SDK路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uni_agent_sdk.services.file import FileService
from uni_agent_sdk.utils.config import Config
from uni_agent_sdk import setup_agent_logging

async def test_oss_functionality():
    """测试OSS核心功能"""

    print("🧪 开始OSS功能独立测试...")

    # 初始化配置
    config = Config()

    # 创建文件服务
    file_service = FileService(config)

    try:
        # 创建测试HTML内容
        html_content = create_test_html()
        print(f"📝 生成测试HTML内容 ({len(html_content)} 字符)")

        # 测试HTML上传到OSS
        print("🔄 开始上传HTML到OSS...")
        result = await file_service.upload_html_to_oss(
            html_content=html_content,
            filename="oss_test_report.html"
        )

        if result.get('success'):
            print(f"✅ OSS上传成功！")
            print(f"📄 文件URL: {result.get('file_url')}")
            print(f"📊 文件大小: {result.get('size')} 字节")
            print(f"🕒 上传时间: {result.get('upload_time')}")

            # 验证文件是否可访问
            print("🔍 验证文件可访问性...")
            file_info = await file_service.get_file_info(result['file_url'])
            print(f"✅ 文件验证成功: {file_info.get('content_type')}")

        else:
            print(f"❌ OSS上传失败: {result.get('error')}")

    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
    finally:
        # 清理资源
        await file_service.close()

def create_test_html():
    """创建测试HTML内容"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSS功能测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .success {{
            color: #28a745;
            font-weight: bold;
        }}
        .info {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .info:last-child {{
            border-bottom: none;
        }}
        .value {{
            font-weight: bold;
            color: #007fff;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 OSS功能测试报告</h1>
        <p>uni-agent-sdk OSS集成测试结果</p>
    </div>

    <div class="card">
        <h3>📊 测试结果</h3>
        <div class="info">
            <span>OSS上传功能</span>
            <span class="success">✅ 正常</span>
        </div>
        <div class="info">
            <span>HTML预览功能</span>
            <span class="success">✅ 可用</span>
        </div>
        <div class="info">
            <span>Content-Disposition</span>
            <span class="success">✅ inline模式</span>
        </div>
        <div class="info">
            <span>测试时间</span>
            <span class="value">{current_time}</span>
        </div>
    </div>

    <div class="card">
        <h3>🔧 技术验证</h3>
        <ul>
            <li>✅ 阿里云OSS集成正常</li>
            <li>✅ HTML文件上传成功</li>
            <li>✅ 浏览器预览支持</li>
            <li>✅ 文件URL生成正确</li>
            <li>✅ Content-Type设置正确</li>
        </ul>
    </div>

    <div class="card">
        <h3>📝 总结</h3>
        <p>OSS集成功能测试全部通过，系统工作正常。此HTML文件成功上传到阿里云OSS，
        并可通过浏览器直接预览而非下载，验证了核心功能的完整性。</p>
    </div>

    <div style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
        <p>🎉 测试完成时间: {current_time}</p>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    # 设置日志
    setup_agent_logging()

    print("🚀 启动OSS功能独立测试")
    asyncio.run(test_oss_functionality())
    print("🏁 测试完成")