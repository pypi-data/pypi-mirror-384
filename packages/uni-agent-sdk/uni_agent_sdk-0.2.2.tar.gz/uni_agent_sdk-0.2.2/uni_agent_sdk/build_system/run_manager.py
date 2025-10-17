"""本地容器运行管理器"""

import asyncio
import signal
import socket
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from .build_manager import BuildManager
from .docker_client import DockerClient, DockerError


class RunManagerError(Exception):
    """运行管理器异常"""

    pass


class RunManager:
    """本地容器运行管理器

    功能：
    1. 获取最后构建的镜像信息
    2. 启动容器
    3. 实时流式输出日志
    4. 优雅处理容器关闭
    """

    def __init__(
        self,
        project_dir: Path,
        docker_client: DockerClient,
    ) -> None:
        """初始化运行管理器

        Args:
            project_dir: 项目根目录
            docker_client: Docker 客户端实例
        """
        self.project_dir = project_dir
        self.docker_client = docker_client
        self.build_manager = BuildManager(project_dir, docker_client)
        self.container_id: Optional[str] = None

    def load_env_file(self, env_file: Optional[Path] = None) -> Dict[str, str]:
        """从 .env 文件加载环境变量

        Args:
            env_file: .env 文件路径，默认为项目根目录的 .env

        Returns:
            环境变量字典 {"KEY": "VALUE"}
        """
        env_file = env_file or self.project_dir / ".env"

        env_vars = {}
        if not env_file.exists():
            print(f"⚠️  .env 文件不存在: {env_file}")
            return env_vars

        # 读取并解析 .env 文件
        try:
            with open(env_file, encoding="utf-8") as f:
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
                print(f"✅ 从 {env_file} 加载环境变量:")
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
            print(f"⚠️  读取 .env 文件失败: {e}")
            return {}

    def get_image_info(self) -> Dict[str, str]:
        """获取最后构建的镜像信息

        Returns:
            包含镜像信息的字典：
            {
                "name": "robot-my-agent",
                "version": "0.1.0",
                "image_tag": "robot-my-agent:0.1.0"
            }

        Raises:
            RunManagerError: 获取失败时抛出
        """
        try:
            # 从 pyproject.toml 读取项目信息
            config = self.build_manager.project_config

            name = config.get("name")
            version = config.get("version")

            if not name or not version:
                raise RunManagerError(
                    "无法从 pyproject.toml 读取项目名称或版本"
                )

            image_tag = f"robot-{name}:{version}"

            return {
                "name": name,
                "version": version,
                "image_tag": image_tag,
            }
        except RunManagerError:
            raise
        except Exception as e:
            raise RunManagerError(f"获取镜像信息失败: {e}")

    def validate_image_exists(self, image_tag: str) -> bool:
        """验证镜像是否存在

        Args:
            image_tag: 镜像标签

        Returns:
            镜像是否存在
        """
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image_tag],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️  验证镜像存在性失败: {e}")
            return False

    def cleanup_container(self, container_name: str) -> None:
        """清理已存在的同名容器

        Args:
            container_name: 容器名称
        """
        try:
            # 检查容器是否存在
            result = subprocess.run(
                ["docker", "inspect", container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # 容器存在，先停止再删除
                print(f"⚠️  检测到已存在的容器: {container_name}")
                print(f"   正在停止容器...")

                subprocess.run(
                    ["docker", "stop", container_name],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

                print(f"   正在删除容器...")
                subprocess.run(
                    ["docker", "rm", container_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                print(f"✅ 旧容器已清理")

        except Exception as e:
            print(f"⚠️  清理容器失败: {e}")

    def is_port_available(self, port: int) -> bool:
        """检查端口是否可用

        Args:
            port: 端口号

        Returns:
            端口是否可用
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result != 0
        except Exception:
            return False

    def find_available_port(self, preferred_port: int = 8080, max_attempts: int = 10) -> int:
        """找到可用的端口

        Args:
            preferred_port: 首选端口
            max_attempts: 最多尝试次数

        Returns:
            可用的端口号
        """
        for attempt in range(max_attempts):
            test_port = preferred_port + attempt * 100
            if self.is_port_available(test_port):
                return test_port

        # 如果找不到可用端口，使用系统分配的端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def cleanup_running_containers(self, image_tag: str, port: int = 8080) -> None:
        """清理所有占用指定端口的容器

        Args:
            image_tag: 镜像标签（用于日志信息）
            port: 端口号
        """
        try:
            # 先清理所有停止的容器和孤立资源
            subprocess.run(
                ["docker", "system", "prune", "-f"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # 列出所有运行中的容器及其端口映射
            result = subprocess.run(
                ["docker", "ps", "-q"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                container_ids = result.stdout.strip().split("\n")
                containers_to_stop = []

                for container_id in container_ids:
                    if not container_id:
                        continue

                    # 检查每个容器的端口映射
                    inspect_result = subprocess.run(
                        ["docker", "inspect", container_id, "--format",
                         "{{.HostConfig.PortBindings}}"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    if inspect_result.returncode == 0:
                        port_bindings = inspect_result.stdout.strip()
                        # 查找是否使用了指定端口
                        if f":{port}" in port_bindings or str(port) in port_bindings:
                            containers_to_stop.append(container_id)

                if containers_to_stop:
                    print(f"⚠️  检测到 {len(containers_to_stop)} 个容器占用端口 {port}")
                    for container_id in containers_to_stop:
                        print(f"   正在停止容器: {container_id[:12]}")
                        subprocess.run(
                            ["docker", "stop", container_id],
                            capture_output=True,
                            text=True,
                            timeout=15,
                        )

                    print(f"✅ 已停止所有占用端口的容器")

        except Exception as e:
            print(f"⚠️  清理运行中的容器失败: {e}")

    def run_container(
        self,
        image_tag: str,
        port: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> str:
        """启动容器

        Args:
            image_tag: 镜像标签
            port: 主机端口（可选，None 表示不绑定端口）
            env: 环境变量字典
            name: 容器名称

        Returns:
            容器 ID

        Raises:
            RunManagerError: 启动失败时抛出
        """
        try:
            # 检查端口是否可用，如果不可用则自动选择其他端口
            if port is not None:
                if not self.is_port_available(port):
                    print(f"⚠️  端口 {port} 被占用，尝试寻找可用端口...")
                    new_port = self.find_available_port(port)
                    if new_port != port:
                        print(f"✅ 将使用端口 {new_port} 替代")
                    port = new_port

                # 先清理所有占用指定端口的容器（解决端口冲突）
                self.cleanup_running_containers(image_tag, port)

            # 再清理已存在的同名容器
            if name:
                self.cleanup_container(name)

            # 构建 docker run 命令
            cmd = [
                "docker",
                "run",
                "-d",  # detach
            ]

            # 添加 DNS 配置以确保容器可以解析外部域名
            cmd.extend(["--dns", "8.8.8.8", "--dns", "1.1.1.1"])

            # 添加端口映射（可选）
            if port is not None:
                cmd.extend(["-p", f"{port}:8080"])

            # 添加环境变量（确保特殊字符被正确处理）
            if env:
                for key, value in env.items():
                    # 不需要额外引用，subprocess.run 会自动处理特殊字符
                    cmd.extend(["-e", f"{key}={value}"])

            # 添加容器名称
            if name:
                cmd.extend(["--name", name])

            # 添加镜像标签
            cmd.append(image_tag)

            # 调试模式：显示完整的 docker 命令
            if self.docker_client.verbose:
                print(f"\n🔧 Docker 命令: {' '.join(cmd)}\n")

            # 执行 docker run 命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                raise RunManagerError(f"启动容器失败: {error_msg}")

            # 提取容器 ID
            container_id = result.stdout.strip()
            self.container_id = container_id
            return container_id

        except RunManagerError:
            raise
        except Exception as e:
            raise RunManagerError(f"启动容器失败: {e}") from e

    async def stream_logs(self, container_id: str) -> None:
        """实时流式输出容器日志

        Args:
            container_id: 容器 ID

        Raises:
            RunManagerError: 流式输出失败时抛出
        """
        try:
            print("\n📋 容器日志输出:")
            print("-" * 60)

            # 使用 docker logs -f 命令流式输出日志
            process = subprocess.Popen(
                ["docker", "logs", "-f", container_id],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # 设置 Ctrl+C 处理
            def signal_handler(sig, frame):
                raise KeyboardInterrupt()

            signal.signal(signal.SIGINT, signal_handler)

            # 流式输出日志
            try:
                if process.stdout:
                    for line in process.stdout:
                        line = line.rstrip()
                        if line:
                            print(line)
            except KeyboardInterrupt:
                print("\n" + "-" * 60)
                print("📋 日志流已中断")
                process.terminate()
            except Exception as e:
                print(f"⚠️  日志流错误: {e}")
                process.terminate()

        except Exception as e:
            raise RunManagerError(f"流式输出日志失败: {e}") from e

    def stop_container(self, container_id: str) -> None:
        """停止容器

        Args:
            container_id: 容器 ID
        """
        try:
            subprocess.run(
                ["docker", "stop", "-t", "10", container_id],
                capture_output=True,
                text=True,
                timeout=15,
            )
            print("✅ 容器已停止")
        except Exception as e:
            print(f"⚠️  停止容器失败: {e}")

    async def run(
        self,
        port: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        """完整的运行流程

        Args:
            port: 主机端口（可选，None 表示不绑定端口）
            env: 环境变量字典

        Raises:
            RunManagerError: 运行失败时抛出
        """
        try:
            # 步骤 1: 获取镜像信息
            print("\n" + "=" * 60)
            print("🚀 启动智能体容器")
            print("=" * 60 + "\n")

            print("📦 获取镜像信息...")
            image_info = self.get_image_info()
            image_tag = image_info["image_tag"]

            print(f"✅ 镜像标签: {image_tag}")
            print(f"   项目: {image_info['name']}")
            print(f"   版本: {image_info['version']}")

            # 步骤 2: 加载环境变量
            print("\n📋 加载环境变量...")
            if not env:
                env = self.load_env_file()
            else:
                print("✅ 使用提供的环境变量")

            # 步骤 3: 验证镜像是否存在
            print("\n🔍 验证镜像是否存在...")
            if not self.validate_image_exists(image_tag):
                raise RunManagerError(
                    f"镜像不存在: {image_tag}\n"
                    "请先运行 'uni-agent build' 构建镜像"
                )
            print("✅ 镜像存在")

            # 步骤 4: 启动容器
            print("\n🐳 启动容器...")
            container_name = f"robot-{image_info['name']}-{image_info['version']}"
            container_id = self.run_container(
                image_tag,
                port=port,
                env=env,
                name=container_name,
            )
            print(f"✅ 容器已启动")
            print(f"   容器 ID: {container_id[:12]}")
            print(f"   容器名称: {container_name}")
            if port is not None:
                print(f"   访问地址: http://localhost:{port}")
            else:
                print(f"   （无端口绑定）")

            # 步骤 5: 实时输出日志
            print("\n📋 连接日志流...")
            try:
                await self.stream_logs(container_id)
            finally:
                # 优雅关闭：停止容器
                print("\n🛑 正在停止容器...")
                self.stop_container(container_id)

                # 显示后续步骤
                print("\n💡 容器已关闭")
                print(f"   查看日志: docker logs {container_id[:12]}")
                print(f"   重新启动: docker start {container_id[:12]}")
                print(f"   删除容器: docker rm {container_id[:12]}")

        except RunManagerError:
            raise
        except KeyboardInterrupt:
            print("\n⏸️  用户中断")
            if self.container_id:
                self.stop_container(self.container_id)
            raise RunManagerError("运行已被用户中断")
        except Exception as e:
            raise RunManagerError(f"运行过程中发生错误: {e}") from e


__all__ = ["RunManager", "RunManagerError"]
