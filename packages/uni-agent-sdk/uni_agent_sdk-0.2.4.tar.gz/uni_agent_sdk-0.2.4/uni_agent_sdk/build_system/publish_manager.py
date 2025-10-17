"""
发布管理器模块

统筹完整的发布流程：获取配置、构建镜像、推送到 registry、通知 Node Server
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .build_manager import BuildManager, BuildManagerError
from .cloud_function_client import CloudFunctionClient, CloudFunctionError
from .config_provider import ConfigProvider
from .docker_client import DockerClient, DockerError


class PublishManagerError(Exception):
    """发布管理器异常"""

    pass


class PublishManager:
    """发布管理器

    统筹整个镜像发布流程：
    1. 从云函数获取部署配置（registry、node server）
    2. 调用 BuildManager 构建镜像（如果需要）
    3. 登录 registry 并推送镜像
    4. 通知 Node Server 开始部署
    5. 验证发布结果
    """

    def __init__(
        self,
        config_provider: ConfigProvider,
        cloud_client: CloudFunctionClient,
        build_manager: BuildManager,
        docker_client: DockerClient,
    ) -> None:
        """
        初始化发布管理器

        Args:
            config_provider: 配置提供者实例
            cloud_client: 云函数客户端实例
            build_manager: 构建管理器实例
            docker_client: Docker 客户端实例
        """
        self.config = config_provider
        self.cloud_client = cloud_client
        self.build_manager = build_manager
        self.docker_client = docker_client
        self.deploy_config: Optional[Dict[str, Any]] = None

    def load_environment_variables(self, env_file: Optional[str] = None) -> Dict[str, str]:
        """从指定文件加载生产环境变量

        Args:
            env_file: 环境变量文件路径，默认为 .env

        Returns:
            环境变量字典
        """
        # 确定环境变量文件路径
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = Path.cwd() / ".env"

        env_vars = {}
        if not env_path.exists():
            print(f"⚠️  环境变量文件不存在: {env_path}")
            return env_vars

        # 读取并解析文件
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 忽略注释行和空行
                    if not line or line.startswith("#"):
                        continue
                    # 忽略没有等号的行
                    if "=" not in line:
                        continue

                    # 分割键值对（仅在第一个等号处分割）
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # 移除引号（支持双引号和单引号）
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]

                    env_vars[key] = value

            if env_vars:
                print(f"✅ 从 {env_path} 加载环境变量:")
                for key, value in env_vars.items():
                    # 显示时隐藏敏感值
                    display_value = (
                        "****" if any(
                            keyword in key.upper()
                            for keyword in ["KEY", "PASSWORD", "TOKEN", "SECRET"]
                        )
                        else value
                    )
                    print(f"   {key}={display_value}")

            return env_vars
        except Exception as e:
            print(f"⚠️  读取环境变量文件失败: {e}")
            return {}

    async def publish(self, skip_build: bool = False, env_file: Optional[str] = None) -> Dict[str, Any]:
        """
        完整发布流程

        Args:
            skip_build: 是否跳过构建，使用现有镜像
            env_file: 环境变量文件路径（默认: .env）

        Returns:
            发布结果字典：
            {
                "success": True,
                "image_url": "registry.example.com:5000/robots/oss-agent:1.0.0",
                "image_latest_url": "registry.example.com:5000/robots/oss-agent:latest",
                "robot_id": "robot-12345",
                "deployment_status": "deploying",
                "task_id": "deploy-abc123"
            }

        Raises:
            PublishManagerError: 发布流程失败时抛出
        """
        start_time = datetime.now()

        try:
            # 步骤 1: 准备发布操作
            print("\n" + "=" * 60)
            print("🚀 开始发布流程")
            print("=" * 60 + "\n")

            await self.prepare_publish()

            # 步骤 1.5: 加载环境变量
            print("📋 加载环境变量...")
            environment = self.load_environment_variables(env_file)
            print()

            # 步骤 2: 构建镜像（如果需要）
            if skip_build:
                print("⏩ 跳过构建，使用现有镜像\n")
                local_tag = f"robot-{self.build_manager.project_config['name']}:{self.build_manager.project_config['version']}"
            else:
                print("🏗️  正在构建镜像...\n")
                local_tag = self.build_manager.build_image()

            # 步骤 3: 推送镜像到 OSS
            print("\n📤 正在推送镜像到 registry...\n")
            image_urls = await self.push_to_oss(local_tag)

            # 步骤 4: 更新机器人信息到云函数
            print("\n🔔 正在通知 Node Server...\n")
            deployment_info = await self.update_robot_info(
                image_urls["versioned"],
                image_urls["latest"],
                environment=environment,
            )

            # 步骤 5: 验证发布
            print("\n✅ 正在验证发布...\n")
            await self.verify_publish(deployment_info)

            # 计算耗时
            elapsed = datetime.now() - start_time
            elapsed_seconds = elapsed.total_seconds()

            # 显示成功信息
            print("\n" + "=" * 60)
            print("✅ 发布成功！")
            print(f"🏷️  镜像地址: {image_urls['versioned']}")
            print(f"🏷️  Latest 标签: {image_urls['latest']}")
            print(f"🤖 Robot ID: {self.deploy_config['robot_id']}")
            print(f"📦 部署任务: {deployment_info.get('task_id', 'N/A')}")
            print(f"📊 部署状态: {deployment_info.get('status', 'N/A')}")
            print(f"⏱️  总耗时: {elapsed_seconds:.1f} 秒")
            print("=" * 60)

            print("\n💡 下一步操作：")
            print(
                f"   • 查看部署状态: curl -H 'Authorization: Bearer <token>' {self.deploy_config['node_server']['url']}/api/deployment/{deployment_info.get('task_id', '')}/status"
            )
            print(
                f"   • 查看机器人日志: curl -H 'Authorization: Bearer <token>' {self.deploy_config['node_server']['url']}/api/robots/{self.deploy_config['robot_id']}/logs"
            )
            print()

            return {
                "success": True,
                "image_url": image_urls["versioned"],
                "image_latest_url": image_urls["latest"],
                "robot_id": self.deploy_config["robot_id"],
                "deployment_status": deployment_info.get("status", "unknown"),
                "task_id": deployment_info.get("task_id", ""),
            }

        except (BuildManagerError, DockerError, CloudFunctionError) as e:
            raise PublishManagerError(f"发布失败: {e}") from e
        except Exception as e:
            raise PublishManagerError(f"发布过程中发生未知错误: {e}") from e

    async def prepare_publish(self) -> None:
        """
        准备发布操作

        主要工作：
        1. 如果需要，从云函数获取配置
        2. 更新 ConfigProvider
        3. 验证必需配置

        支持两种模式：
        - 云函数模式：从云函数获取 registry 和 node server 配置
        - 本地配置模式：直接使用 .env 或环境变量中的配置

        Raises:
            PublishManagerError: 准备失败时抛出
        """
        print("🔗 正在准备部署配置...\n")

        try:
            # 获取 appkey
            appkey = self.config.get_robot_appkey()

            # 检查是否需要从云函数获取配置
            if self.cloud_client and hasattr(self, 'cloud_client'):
                try:
                    print("🌐 从云函数获取部署配置...")
                    self.deploy_config = await self.cloud_client.get_deploy_config(appkey)

                    # 更新 ConfigProvider（云函数配置优先级最低）
                    self.config.update_from_cloud(self.deploy_config)
                    print("✅ 云函数配置获取成功\n")
                except (CloudFunctionError, Exception) as e:
                    # 如果云函数获取失败，检查本地配置是否完整
                    print(f"⚠️  云函数配置获取失败: {e}")
                    print("📋 尝试使用本地配置...\n")

                    if not self.config._is_local_config_complete():
                        raise PublishManagerError(
                            f"本地配置不完整，无法继续。请配置 REGISTRY_URL、"
                            "REGISTRY_USERNAME 和 REGISTRY_PASSWORD。"
                        ) from e

                    # 使用本地配置，构建最小的 deploy_config
                    self.deploy_config = {
                        "robot_id": appkey,  # Use appkey as robot_id
                        "registry": {
                            "url": self.config.get_registry_url(),
                            "username": self.config.get_registry_username(),
                            "password": self.config.get_registry_password(),
                            "namespace": "robots",
                        },
                        "node_server": {
                            "url": self.config.get_node_server_url(),
                            "token": self.config.get_node_server_token(),
                        },
                    }
            else:
                # 如果没有云函数客户端，直接使用本地配置
                print("📋 使用本地配置模式\n")
                self.deploy_config = {
                    "robot_id": appkey,
                    "registry": {
                        "url": self.config.get_registry_url(),
                        "username": self.config.get_registry_username(),
                        "password": self.config.get_registry_password(),
                        "namespace": "robots",
                    },
                    "node_server": {
                        "url": self.config.get_node_server_url(),
                        "token": self.config.get_node_server_token(),
                    },
                }

            # 验证必需配置
            self.config.validate_publish_config()
            print("✅ 部署配置准备完毕\n")

        except PublishManagerError:
            raise
        except ValueError as e:
            raise PublishManagerError(f"配置验证失败: {e}") from e
        except Exception as e:
            raise PublishManagerError(f"准备发布配置失败: {e}") from e

    async def push_to_oss(self, local_tag: str) -> Dict[str, str]:
        """
        推送镜像到 OSS（阿里云对象存储/私有 registry）

        Args:
            local_tag: 本地镜像标签（如 "robot-oss-agent:1.0.0"）

        Returns:
            镜像 URL 字典：
            {
                "versioned": "registry.example.com:5000/robots/oss-agent:1.0.0",
                "latest": "registry.example.com:5000/robots/oss-agent:latest"
            }

        Raises:
            PublishManagerError: 推送失败时抛出
        """
        try:
            # 获取 registry 配置
            registry_url = self.config.get_registry_url()
            registry_username = self.config.get_registry_username()
            registry_password = self.config.get_registry_password()

            if not all([registry_url, registry_username, registry_password]):
                raise PublishManagerError(
                    "Registry 配置不完整。请检查 REGISTRY_URL、REGISTRY_USERNAME、REGISTRY_PASSWORD。"
                )

            # 提取项目名称和版本
            # local_tag 格式: "robot-project-name:version"
            if ":" not in local_tag:
                raise PublishManagerError(f"无效的镜像标签格式: {local_tag}")

            tag_base, version = local_tag.split(":", 1)
            project_name = tag_base.replace("robot-", "")

            # 获取 namespace（可选）
            namespace = self.deploy_config.get("registry", {}).get(
                "namespace", "robots"
            )

            # 构建 registry 标签
            # 格式: registry_url/namespace/project_name:version
            registry_tag_versioned = (
                f"{registry_url}/{namespace}/{project_name}:{version}"
            )
            registry_tag_latest = f"{registry_url}/{namespace}/{project_name}:latest"

            # 登录 registry
            print(f"🔐 登录 registry: {registry_url}")
            self.docker_client.login(registry_url, registry_username, registry_password)
            print()

            # 打标签（versioned）
            print(f"🏷️  打标签: {local_tag} -> {registry_tag_versioned}")
            self.docker_client.tag_image(local_tag, registry_tag_versioned)

            # 打标签（latest）
            print(f"🏷️  打标签: {local_tag} -> {registry_tag_latest}")
            self.docker_client.tag_image(local_tag, registry_tag_latest)
            print()

            # 推送镜像（versioned）
            print(f"⬆️  推送镜像: {registry_tag_versioned}")
            await self._push_with_retry(registry_tag_versioned)

            # 推送镜像（latest）
            print(f"⬆️  推送镜像: {registry_tag_latest}")
            await self._push_with_retry(registry_tag_latest)

            print("\n✅ 镜像推送成功！")

            return {
                "versioned": registry_tag_versioned,
                "latest": registry_tag_latest,
            }

        except DockerError as e:
            raise PublishManagerError(f"Docker 操作失败: {e}") from e
        except Exception as e:
            raise PublishManagerError(f"推送镜像失败: {e}") from e

    async def update_robot_info(
        self, image_url: str, image_latest_url: str, environment: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        更新机器人信息到云函数（通知 Node Server）

        Args:
            image_url: 镜像 URL（versioned）
            image_latest_url: 镜像 URL（latest）
            environment: 环境变量字典（可选）

        Returns:
            部署任务信息：
            {
                "task_id": "deploy-abc123",
                "robot_id": "robot-12345",
                "status": "deploying",
                "status_url": "/api/deployment/deploy-abc123/status"
            }

        Raises:
            PublishManagerError: 通知失败时抛出
        """
        try:
            if not self.deploy_config:
                raise PublishManagerError(
                    "部署配置未初始化，请先调用 prepare_publish()"
                )

            # 获取 Node Server 配置
            node_server_url = self.config.get_node_server_url()
            node_server_token = self.config.get_node_server_token()

            if not node_server_url:
                raise PublishManagerError("Node Server URL 未配置")

            if not node_server_token:
                raise PublishManagerError("Node Server Token 未配置")

            # 提取版本号（从 image_url）
            version = image_url.split(":")[-1] if ":" in image_url else "latest"

            # 构建部署请求
            robot_id = self.deploy_config.get("robot_id")
            url = f"{node_server_url.rstrip('/')}/api/robots/deploy"

            payload = {
                "robot_id": robot_id,
                "image": image_url,
                "image_latest": image_latest_url,
                "version": version,
                "environment": environment or {},  # 包含加载的环境变量
                "ports": {8080: 8080},  # 默认端口映射
                "registry_auth": {
                    "username": self.config.get_registry_username(),
                    "password": self.config.get_registry_password(),
                },
            }

            headers = {
                "Authorization": f"Bearer {node_server_token}",
                "Content-Type": "application/json",
            }

            # 发送部署请求（带重试）
            print(f"🚀 通知 Node Server 部署: {url}")
            response_data = await self._notify_with_retry(url, payload, headers)

            # 验证响应
            if response_data.get("code") != 0:
                raise PublishManagerError(
                    f"Node Server 返回错误: {response_data.get('message', 'Unknown error')}"
                )

            deployment_info = response_data.get("data", {})

            print(f"✅ 部署请求已发送！")
            print(f"   任务 ID: {deployment_info.get('task_id', 'N/A')}")
            print(f"   状态: {deployment_info.get('status', 'N/A')}")
            if environment:
                print(f"   环境变量: {len(environment)} 个")

            return deployment_info

        except httpx.HTTPError as e:
            raise PublishManagerError(f"HTTP 请求失败: {e}") from e
        except Exception as e:
            raise PublishManagerError(f"通知 Node Server 失败: {e}") from e

    async def verify_publish(self, deployment_info: Dict[str, Any]) -> None:
        """
        发布后验证

        验证步骤：
        1. 检查部署任务状态
        2. 验证镜像在 registry 中可访问（可选）

        Args:
            deployment_info: 部署任务信息

        Raises:
            PublishManagerError: 验证失败时抛出
        """
        try:
            task_id = deployment_info.get("task_id")
            if not task_id:
                print("⚠️  警告: 无法获取部署任务 ID，跳过验证")
                return

            # 获取 Node Server 配置
            node_server_url = self.config.get_node_server_url()
            node_server_token = self.config.get_node_server_token()

            if not node_server_url or not node_server_token:
                print("⚠️  警告: Node Server 配置不完整，跳过验证")
                return

            # 查询部署状态
            url = f"{node_server_url.rstrip('/')}/api/deployment/{task_id}/status"
            headers = {"Authorization": f"Bearer {node_server_token}"}

            print(f"🔍 查询部署状态: {url}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                status_data = response.json()

            # 检查响应
            if status_data.get("code") != 0:
                print(
                    f"⚠️  警告: 查询部署状态失败: {status_data.get('message', 'Unknown error')}"
                )
                return

            data = status_data.get("data", {})
            status = data.get("status", "unknown")

            print(f"✅ 部署状态验证成功")
            print(f"   状态: {status}")
            print(f"   进度: {data.get('progress', 'N/A')}")

        except httpx.HTTPError as e:
            # 验证失败不应该终止发布流程，只是警告
            print(f"⚠️  警告: 验证发布状态失败: {e}")
        except Exception as e:
            print(f"⚠️  警告: 验证过程中发生错误: {e}")

    async def rollback_publish(
        self, robot_id: str, previous_version: str
    ) -> Dict[str, Any]:
        """
        回滚发布操作

        将机器人回滚到之前的版本

        Args:
            robot_id: 机器人 ID
            previous_version: 之前的版本号

        Returns:
            回滚结果

        Raises:
            PublishManagerError: 回滚失败时抛出
        """
        try:
            print(f"\n🔄 正在回滚到版本: {previous_version}\n")

            # 获取 Node Server 配置
            node_server_url = self.config.get_node_server_url()
            node_server_token = self.config.get_node_server_token()

            if not node_server_url or not node_server_token:
                raise PublishManagerError("Node Server 配置不完整，无法执行回滚")

            # 构建回滚镜像 URL
            registry_url = self.config.get_registry_url()
            namespace = (
                self.deploy_config.get("registry", {}).get("namespace", "robots")
                if self.deploy_config
                else "robots"
            )
            project_name = self.build_manager.project_config["name"]

            previous_image_url = (
                f"{registry_url}/{namespace}/{project_name}:{previous_version}"
            )

            # 发送部署请求（使用旧版本镜像）
            url = f"{node_server_url.rstrip('/')}/api/robots/deploy"

            payload = {
                "robot_id": robot_id,
                "image": previous_image_url,
                "image_latest": f"{registry_url}/{namespace}/{project_name}:latest",
                "version": previous_version,
                "environment": {},
                "ports": {8080: 8080},
                "registry_auth": {
                    "username": self.config.get_registry_username(),
                    "password": self.config.get_registry_password(),
                },
            }

            headers = {
                "Authorization": f"Bearer {node_server_token}",
                "Content-Type": "application/json",
            }

            response_data = await self._notify_with_retry(url, payload, headers)

            if response_data.get("code") != 0:
                raise PublishManagerError(
                    f"回滚失败: {response_data.get('message', 'Unknown error')}"
                )

            print(f"✅ 回滚成功！")
            print(f"   版本: {previous_version}")
            print(f"   任务 ID: {response_data.get('data', {}).get('task_id', 'N/A')}")

            return response_data.get("data", {})

        except Exception as e:
            raise PublishManagerError(f"回滚失败: {e}") from e

    async def _push_with_retry(
        self, tag: str, max_retries: int = 3, backoff_factor: float = 2.0
    ) -> None:
        """
        带重试的推送镜像

        Args:
            tag: 镜像标签
            max_retries: 最大重试次数
            backoff_factor: 退避因子

        Raises:
            DockerError: 所有重试都失败时抛出
        """
        for attempt in range(max_retries):
            try:
                # 使用 asyncio.to_thread 在线程池中执行同步操作
                await asyncio.to_thread(self.docker_client.push, tag)
                return
            except DockerError as e:
                if attempt < max_retries - 1:
                    delay = backoff_factor**attempt
                    print(
                        f"⚠️  推送失败，{delay:.0f} 秒后重试... (尝试 {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

    async def _notify_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> Dict[str, Any]:
        """
        带重试的通知 Node Server

        Args:
            url: Node Server URL
            payload: 请求体
            headers: 请求头
            max_retries: 最大重试次数
            backoff_factor: 退避因子

        Returns:
            响应数据

        Raises:
            httpx.HTTPError: 所有重试都失败时抛出
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt < max_retries - 1:
                    delay = backoff_factor**attempt
                    print(
                        f"⚠️  网络错误，{delay:.0f} 秒后重试... (尝试 {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise
            except httpx.HTTPStatusError as e:
                # HTTP 状态错误（4xx, 5xx）不重试
                raise
