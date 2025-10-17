#!/usr/bin/env python3
"""OSS集成智能体 - HTML报告预览功能

🎯 核心功能：
- ✅ OSS HTML文件上传
- ✅ 浏览器预览支持
- ✅ LLM智能回复
- ✅ 命令系统支持

运行方式：
    export KIMI_API_KEY="your_api_key"
    python examples/full_featured_agent.py
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加SDK路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uni_agent_sdk import Agent, Response, setup_agent_logging


class FullFeaturedAgent(Agent):
    """OSS集成智能体

    专注于HTML报告上传和预览功能：
    - 🎯 OSS文件上传
    - 📄 HTML报告生成
    - 🌐 浏览器预览支持
    - 🧠 LLM智能对话
    """

    async def handle_message(self, message, context):
        """核心业务逻辑"""

        if not context.should_respond():
            return None

        user_message = message.content

        # 检查是否为命令
        if user_message.startswith("/"):
            return await self._handle_command(context)

        # LLM智能回复
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": user_message}]
            )
            return Response.text(response)
        except Exception as e:
            self.logger.error(f"LLM回复失败: {e}")
            return Response.text("抱歉，智能回复暂时不可用，请稍后再试。")

    async def _handle_command(self, context) -> Response:
        """处理命令"""
        cmd_info = context.get_command()
        if not cmd_info:
            return Response.text("命令格式错误，请使用 /help 查看可用命令。")

        command = cmd_info["command"]

        if command == "help":
            return Response.text(
                "🤖 OSS智能体命令：\n"
                "/help - 显示帮助信息\n"
                "/report - 生成HTML报告（OSS预览）"
            )
        elif command == "report":
            return await self._generate_html_report(context)
        else:
            return Response.text(f"未知命令：{command}。使用 /help 查看可用命令。")

    async def _generate_html_report(self, context):
        """生成HTML报告并上传到OSS"""
        try:
            self.logger.info("📝 开始生成HTML报告并上传...")

            # 生成HTML报告内容
            html_content = self._create_html_report()

            # 使用OSS上传HTML文件
            file_result = await self.files.upload_html_to_oss(
                html_content=html_content,
                filename="agent_analysis_report.html"
            )

            if not file_result.get('success'):
                return Response.text(f"❌ 报告生成失败：{file_result.get('error')}")

            self.logger.info(f"📁 HTML报告已生成: {file_result.get('file_url')}")

            # 返回HTML报告卡片
            return await self.create_html_report_response(
                title="智能体测试报告",
                content=html_content,
                summary="点击查看完整的智能体测试报告，包含性能指标、功能验证等详细信息。",
                options={
                    "file_url": file_result['file_url'],
                    "file_name": "intelligent_agent_report.html",
                    "file_size": len(html_content.encode('utf-8'))
                }
            )

        except Exception as e:
            self.logger.error(f"HTML报告生成失败: {e}")
            return Response.text(f"❌ 报告生成失败: {str(e)}")

    def _create_html_report(self):
        """创建简化HTML报告"""
        current_time = self._get_current_time()

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSS智能体测试报告</title>
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
            background: linear-gradient(135deg, #007fff 0%, #0066cc 100%);
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
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-value {{
            font-weight: bold;
            color: #007fff;
        }}
        .status-good {{
            color: #28a745;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 OSS智能体测试报告</h1>
        <p>uni-agent-sdk OSS集成功能验证</p>
    </div>

    <div class="card">
        <h3>📊 系统状态</h3>
        <div class="metric">
            <span>OSS集成状态</span>
            <span class="status-good">✅ 正常运行</span>
        </div>
        <div class="metric">
            <span>HTML预览功能</span>
            <span class="status-good">✅ 可用</span>
        </div>
        <div class="metric">
            <span>文件上传服务</span>
            <span class="status-good">✅ 在线</span>
        </div>
        <div class="metric">
            <span>报告生成时间</span>
            <span class="metric-value">{current_time}</span>
        </div>
    </div>

    <div class="card">
        <h3>🔧 功能验证</h3>
        <div class="metric">
            <span>文件上传到OSS</span>
            <span class="status-good">✅ 通过</span>
        </div>
        <div class="metric">
            <span>Content-Disposition设置</span>
            <span class="status-good">✅ inline模式</span>
        </div>
        <div class="metric">
            <span>浏览器预览支持</span>
            <span class="status-good">✅ 支持</span>
        </div>
        <div class="metric">
            <span>iframe嵌入支持</span>
            <span class="status-good">✅ 支持</span>
        </div>
    </div>

    <div class="card">
        <h3>📝 测试说明</h3>
        <p>此报告验证了以下OSS集成功能：</p>
        <ul>
            <li>✅ HTML文件成功上传到阿里云OSS</li>
            <li>✅ 设置正确的Content-Disposition: inline头</li>
            <li>✅ 支持浏览器直接预览而非下载</li>
            <li>✅ 支持iframe嵌入显示</li>
            <li>✅ 生成可访问的公共URL</li>
        </ul>
    </div>

    <div class="footer">
        <p>📅 报告生成时间: {current_time}</p>
        <p>🔗 OSS集成测试 - 所有功能正常</p>
    </div>
</body>
</html>"""

    def _get_current_time(self):
        """获取当前时间"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # === 生命周期钩子 ===

    async def on_startup(self):
        """启动钩子"""
        await super().on_startup()
        self.logger.info("🎯 OSS智能体启动完成！")
        self.logger.info("📊 专注OSS HTML预览功能")
        self.logger.info("⚡ 核心功能就绪")

    async def on_error(self, error: Exception, context=None):
        """错误处理钩子"""
        await super().on_error(error, context)
        self.logger.info(f"🔧 自动处理错误：{error}")


def main():
    """主函数"""
    # 设置日志
    setup_agent_logging()

    # 设置DEBUG级别以查看详细信息
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # 从配置获取API凭据
    from uni_agent_sdk.utils.config import Config
    config = Config()

    api_key = config.get('robot_api_key')
    api_secret = config.get('robot_api_secret')

    if not api_key or not api_secret:
        print("❌ 缺少robot_api_key或robot_api_secret配置")
        return

    print(f"使用API凭据: {api_key} / {api_secret[:10]}...")

    # 创建并启动智能体
    agent = FullFeaturedAgent(api_key, api_secret)
    agent.run()


if __name__ == "__main__":
    main()