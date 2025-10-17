"""
Docker 客户端封装模块

封装 docker 命令行调用，提供构建、推送、登录等功能
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


class DockerError(Exception):
    """Docker 操作异常"""

    pass


class DockerClient:
    """Docker 命令行客户端封装"""

    def __init__(self, verbose: bool = True) -> None:
        """
        初始化 Docker 客户端

        Args:
            verbose: 是否显示详细输出
        """
        self.verbose = verbose

    def is_docker_available(self) -> bool:
        """
        检查 Docker daemon 是否运行

        Returns:
            True 如果 Docker 可用，False 否则
        """
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def build(
        self, dockerfile_path: Path, tag: str, context_dir: Path, no_cache: bool = False
    ) -> str:
        """
        构建 Docker 镜像

        Args:
            dockerfile_path: Dockerfile 路径
            tag: 镜像标签
            context_dir: 构建上下文目录
            no_cache: 是否禁用缓存

        Returns:
            镜像 ID

        Raises:
            DockerError: 构建失败时抛出
        """
        if not self.is_docker_available():
            raise DockerError(
                "Docker daemon 未运行。请启动 Docker Desktop 或检查 Docker 服务状态。"
            )

        cmd = [
            "docker",
            "build",
            "-f",
            str(dockerfile_path),
            "-t",
            tag,
        ]

        if no_cache:
            cmd.append("--no-cache")

        cmd.append(str(context_dir))

        if self.verbose:
            print(f"🔨 正在构建镜像: {tag}")
            print(f"📁 构建上下文: {context_dir}")
            print(f"📝 Dockerfile: {dockerfile_path}")
            print()

        try:
            # 实时输出构建日志
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            output_lines = []
            if process.stdout:
                for line in process.stdout:
                    line = line.rstrip()
                    output_lines.append(line)
                    if self.verbose:
                        print(line)

            process.wait()

            if process.returncode != 0:
                raise DockerError(
                    f"镜像构建失败（退出码: {process.returncode}）\n"
                    f"请检查 Dockerfile 和构建上下文。"
                )

            # 提取镜像 ID
            image_id = self._extract_image_id("\n".join(output_lines))

            if self.verbose:
                print()
                print(f"✅ 镜像构建成功！")
                print(f"🏷️  标签: {tag}")
                print(f"🆔 镜像 ID: {image_id}")

            return image_id

        except subprocess.TimeoutExpired:
            raise DockerError("构建超时。请检查网络连接或构建配置。")
        except FileNotFoundError:
            raise DockerError(
                "未找到 docker 命令。请确保 Docker 已正确安装并添加到 PATH。"
            )

    def push(self, tag: str) -> bool:
        """
        推送镜像到 registry

        Args:
            tag: 镜像标签（包含 registry 地址）

        Returns:
            True 如果推送成功

        Raises:
            DockerError: 推送失败时抛出
        """
        if not self.is_docker_available():
            raise DockerError("Docker daemon 未运行。请启动 Docker。")

        cmd = ["docker", "push", tag]

        if self.verbose:
            print(f"⬆️  正在推送镜像: {tag}")
            print()

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if process.stdout:
                for line in process.stdout:
                    line = line.rstrip()
                    if self.verbose:
                        print(line)

            process.wait()

            if process.returncode != 0:
                raise DockerError(
                    f"镜像推送失败（退出码: {process.returncode}）\n"
                    f"请检查 registry 认证和网络连接。"
                )

            if self.verbose:
                print()
                print(f"✅ 镜像推送成功！")

            return True

        except FileNotFoundError:
            raise DockerError("未找到 docker 命令。请确保 Docker 已正确安装。")

    def login(self, registry_url: str, username: str, password: str) -> bool:
        """
        登录到 registry

        Args:
            registry_url: Registry 地址
            username: 用户名
            password: 密码

        Returns:
            True 如果登录成功

        Raises:
            DockerError: 登录失败时抛出
        """
        if not self.is_docker_available():
            raise DockerError("Docker daemon 未运行。请启动 Docker。")

        cmd = [
            "docker",
            "login",
            registry_url,
            "-u",
            username,
            "--password-stdin",
        ]

        if self.verbose:
            print(f"🔐 正在登录 registry: {registry_url}")

        try:
            result = subprocess.run(
                cmd,
                input=password,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                raise DockerError(f"Registry 登录失败: {error_msg}")

            if self.verbose:
                print(f"✅ 登录成功！")

            return True

        except subprocess.TimeoutExpired:
            raise DockerError("登录超时。请检查网络连接。")
        except FileNotFoundError:
            raise DockerError("未找到 docker 命令。请确保 Docker 已正确安装。")

    def inspect_image(self, tag: str) -> Dict[str, str]:
        """
        获取镜像详细信息

        Args:
            tag: 镜像标签

        Returns:
            包含镜像信息的字典，包括:
            - id: 镜像 ID
            - size: 镜像大小（字节）
            - size_mb: 镜像大小（MB）
            - created: 创建时间

        Raises:
            DockerError: 获取信息失败时抛出
        """
        if not self.is_docker_available():
            raise DockerError("Docker daemon 未运行。请启动 Docker。")

        cmd = [
            "docker",
            "inspect",
            tag,
            "--format",
            "{{json .}}",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                if "No such image" in error_msg or "No such object" in error_msg:
                    raise DockerError(f"镜像不存在: {tag}")
                raise DockerError(f"获取镜像信息失败: {error_msg}")

            # 解析 JSON 输出
            image_info = json.loads(result.stdout.strip())

            # 提取关键信息
            size_bytes = image_info.get("Size", 0)
            size_mb = round(size_bytes / (1024 * 1024), 2)

            return {
                "id": image_info.get("Id", "").replace("sha256:", "")[:12],
                "size": str(size_bytes),
                "size_mb": str(size_mb),
                "created": image_info.get("Created", ""),
            }

        except json.JSONDecodeError as e:
            raise DockerError(f"解析镜像信息失败: {e}")
        except subprocess.TimeoutExpired:
            raise DockerError("获取镜像信息超时。")
        except FileNotFoundError:
            raise DockerError("未找到 docker 命令。请确保 Docker 已正确安装。")

    def tag_image(self, source_tag: str, target_tag: str) -> bool:
        """
        给镜像打标签

        Args:
            source_tag: 源镜像标签
            target_tag: 目标镜像标签

        Returns:
            True 如果打标签成功

        Raises:
            DockerError: 打标签失败时抛出
        """
        if not self.is_docker_available():
            raise DockerError("Docker daemon 未运行。请启动 Docker。")

        cmd = ["docker", "tag", source_tag, target_tag]

        if self.verbose:
            print(f"🏷️  正在打标签: {source_tag} -> {target_tag}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                if "No such image" in error_msg:
                    raise DockerError(f"源镜像不存在: {source_tag}")
                raise DockerError(f"打标签失败: {error_msg}")

            if self.verbose:
                print(f"✅ 标签创建成功！")

            return True

        except subprocess.TimeoutExpired:
            raise DockerError("打标签超时。")
        except FileNotFoundError:
            raise DockerError("未找到 docker 命令。请确保 Docker 已正确安装。")

    def _extract_image_id(self, output: str) -> str:
        """
        从构建输出中提取镜像 ID

        Args:
            output: docker build 的输出

        Returns:
            镜像 ID（12位短格式）

        Raises:
            DockerError: 无法提取镜像 ID 时抛出
        """
        # 尝试匹配 "Successfully built <image_id>"
        match = re.search(r"Successfully built ([a-f0-9]{12})", output)
        if match:
            return match.group(1)

        # 尝试匹配 "writing image sha256:<full_id>"
        match = re.search(r"writing image sha256:([a-f0-9]{64})", output)
        if match:
            return match.group(1)[:12]

        # 如果都没匹配到，尝试用 inspect 命令获取
        # 这种情况通常不会发生，但作为兜底方案
        raise DockerError("无法从构建输出中提取镜像 ID")
