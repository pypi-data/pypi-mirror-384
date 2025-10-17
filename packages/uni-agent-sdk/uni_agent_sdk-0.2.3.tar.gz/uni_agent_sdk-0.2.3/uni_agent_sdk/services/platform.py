"""平台API通信服务"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import aiohttp

from ..models.message import Response
from ..utils.config import Config
from ..utils.crypto import sign_data


class PlatformAPI:
    """平台API通信服务类

    处理与uni-im平台的所有HTTP通信，包括：
    - 智能体信息获取
    - 会话上下文获取
    - 响应消息发送
    """

    def __init__(self, api_key: str, api_secret: str, config: Config):
        """初始化平台API服务

        Args:
            api_key: 智能体API密钥
            api_secret: 智能体API秘钥
            config: 配置对象
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config
        self.base_url = config.platform_base_url

        self.logger = logging.getLogger(f"PlatformAPI-{api_key[:8]}")

        # 认证信息（通过set_auth_info设置）
        self._developer_userid: Optional[str] = None
        self._jwt_token: Optional[str] = None

        # HTTP会话配置
        self._session: Optional[aiohttp.ClientSession] = None

    def set_auth_info(self, developer_userid: str, jwt_token: str):
        """设置认证信息

        Args:
            developer_userid: 开发者用户ID
            jwt_token: JWT访问令牌
        """
        self._developer_userid = developer_userid
        self._jwt_token = jwt_token
        self.logger.info(
            f"🔄 设置认证信息: developer_userid={developer_userid}, token={jwt_token[:20]}..."
        )

        # 强制重置会话，确保下次使用时创建新会话
        if self._session:
            try:
                if not self._session.closed:
                    # 异步关闭现有会话
                    asyncio.create_task(self._session.close())
                    self.logger.info("🗑️ 已关闭旧HTTP会话")
            except Exception as e:
                self.logger.warning(f"关闭旧会话时出错: {e}")

        # 无论如何都重置会话引用
        self._session = None
        self.logger.info("✅ 认证信息已设置，HTTP会话已重置")

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话（懒加载）"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                total=self.config.http_timeout, connect=self.config.http_connect_timeout
            )

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "uni-agent-sdk/1.0",
            }

            # 添加 CONNECTCODE 头部用于 S2S 认证
            if self.config.connectcode:
                headers["Unicloud-S2s-Authorization"] = (
                    f"CONNECTCODE {self.config.connectcode}"
                )

            # 添加机器人用户身份信息（如果已获取认证信息）
            if self._jwt_token and self._developer_userid:
                headers["uni-id-token"] = self._jwt_token
                headers["uni-id-uid"] = self._developer_userid
                self.logger.info(
                    f"✅ 使用JWT认证: uid={self._developer_userid}, token={self._jwt_token[:20]}..."
                )
            else:
                # 未认证状态，仅用于注册
                headers["uni-id-token"] = ""
                headers["uni-id-uid"] = ""
                # self.logger.warning("⚠️ 使用S2S认证（注册模式）- 可能导致API调用失败")

            self.logger.debug(f"HTTP Headers: {headers}")

            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def close(self):
        """关闭HTTP会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def register_robot(self) -> Dict[str, Any]:
        """注册机器人并获取完整认证信息

        这是认证流程的第一步，使用api_key/api_secret进行机器人注册，
        平台会返回：developer_userid, JWT令牌, RabbitMQ配置, 文件服务配置等完整认证信息

        Returns:
            包含完整认证信息的字典，格式：
            {
                "errCode": 0,
                "data": {
                    "robot_id": "智能体ID",
                    "developer_userid": "开发者用户ID",
                    "token": "JWT访问令牌",
                    "expires_at": JWT令牌过期时间戳,
                    "rabbitmq_config": {
                        "host": "RabbitMQ主机",
                        "port": 端口,
                        "vhost": "虚拟主机",
                        "username": "用户名",
                        "auth_mechanism": "JWT",
                        "queue_name": "RabbitMQ队列名"
                    },
                    "file_service_config": {
                        "access_key_id": "OSS访问密钥ID",
                        "access_key_secret": "OSS访问密钥",
                        "bucket_name": "OSS桶名称",
                        "endpoint": "OSS端点",
                        "region": "服务区域",
                        "base_path": "基础路径",
                        "expires_at": OSS密钥过期时间戳
                    }
                }
            }
        """
        data = {"api_key": self.api_key, "api_secret": self.api_secret}

        try:
            session = await self._get_session()
            url = f"{self.base_url}/uni-im-co/registerRobot"  # 注册端点

            self.logger.debug(f"注册机器人: {url}")
            self.logger.debug(f"请求数据: {data}")

            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP请求失败: {resp.status}")

                result = await resp.json()
                self.logger.debug(f"机器人注册响应: {result}")

                if result.get("errCode") != 0:
                    raise Exception(
                        f"机器人注册失败: {result.get('errMsg', '未知错误')}"
                    )

                return result

        except Exception as e:
            self.logger.error(f"机器人注册失败: {e}")
            raise

    async def get_file_service_config(self) -> Dict[str, Any]:
        """获取文件服务配置（包含密钥）

        Returns:
            包含文件服务配置的字典，格式：
            {
                "errCode": 0,
                "data": {
                    "access_key_id": "文件服务访问密钥ID",
                    "access_key_secret": "文件服务访问密钥",
                    "bucket_name": "文件桶名称",
                    "endpoint": "文件服务端点",
                    "region": "服务区域",
                    "expires_at": 密钥过期时间戳
                }
            }
        """
        data = {"api_key": self.api_key, "api_secret": self.api_secret}

        try:
            session = await self._get_session()
            url = f"{self.base_url}/uni-im-co/getFileServiceConfig"

            self.logger.debug(f"获取文件服务配置: {url}")

            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP请求失败: {resp.status}")

                result = await resp.json()
                self.logger.debug(f"文件服务配置响应: {result}")

                if result.get("errCode") != 0:
                    raise Exception(
                        f"获取文件服务配置失败: {result.get('errMsg', '未知错误')}"
                    )

                return result

        except Exception as e:
            self.logger.error(f"获取文件服务配置失败: {e}")
            raise

    async def get_robot_info(self) -> Dict[str, Any]:
        """获取智能体信息（包含RabbitMQ访问令牌）

        Returns:
            包含智能体信息和RabbitMQ配置的字典，格式：
            {
                "errCode": 0,
                "data": {
                    "robot_id": "智能体ID",
                    "name": "智能体名称",
                    "queue_name": "RabbitMQ队列名",
                    "rabbitmq_token": "JWT访问令牌",
                    "token_expires_at": 令牌过期时间戳,
                    "rabbitmq_config": {
                        "host": "RabbitMQ主机",
                        "port": 端口,
                        "vhost": "虚拟主机",
                        "username": "用户名",
                        "password": "密码"
                    }
                }
            }
        """
        data = {"api_key": self.api_key, "api_secret": self.api_secret}

        try:
            session = await self._get_session()
            url = f"{self.base_url}/uni-im-co/getRobotInfoByApiKey"

            self.logger.debug(f"获取智能体信息: {url}")

            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP请求失败: {resp.status}")

                result = await resp.json()
                self.logger.debug(f"智能体信息响应: {result}")
                return result

        except Exception as e:
            self.logger.error(f"获取智能体信息失败: {e}")
            raise

    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """获取会话上下文

        Args:
            conversation_id: 会话ID

        Returns:
            会话上下文信息
        """
        # 准备请求数据
        data = {"conversation_id": conversation_id}
        signature = sign_data(conversation_id, self.api_secret)

        request_data = {**data, "api_key": self.api_key, "signature": signature}

        try:
            session = await self._get_session()
            url = f"{self.base_url}/uni-im-co/getConversationContext"

            self.logger.debug(f"获取会话上下文: {conversation_id}")

            async with session.post(url, json=request_data) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP请求失败: {resp.status}")

                result = await resp.json()

                if result.get("errCode") != 0:
                    raise Exception(
                        f"获取会话上下文失败: {result.get('errMsg', '未知错误')}"
                    )

                return result.get("data", {})

        except Exception as e:
            self.logger.error(f"获取会话上下文失败: {e}")
            raise

    async def send_response(
        self, conversation_id: str, response: Response, to_uid: str
    ):
        """发送响应消息到平台

        Args:
            conversation_id: 会话ID
            response: 响应对象
            to_uid: 目标用户ID
        """
        # 准备响应数据
        response_data = {
            "conversation_id": conversation_id,
            "response": {**response.to_platform_format(), "to_uid": to_uid},
        }

        # 生成签名
        payload = json.dumps(response_data, ensure_ascii=False, separators=(",", ":"))
        signature = sign_data(payload, self.api_secret)

        request_data = {
            **response_data,
            "api_key": self.api_key,
            "signature": signature,
        }

        try:
            session = await self._get_session()
            url = f"{self.base_url}/uni-im-co/receiveSDKResponse"

            self.logger.debug(f"发送响应: {conversation_id} -> {to_uid}")

            async with session.post(url, json=request_data) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP请求失败: {resp.status}")

                result = await resp.json()

                if result.get("errCode") != 0:
                    raise Exception(f"发送响应失败: {result.get('errMsg', '未知错误')}")

                self.logger.debug("响应发送成功")

        except Exception as e:
            self.logger.error(f"发送响应失败: {e}")
            raise

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
