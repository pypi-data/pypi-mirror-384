"""
CLI publish 命令实现

提供用户友好的发布命令接口，支持：
- 发布 Docker 镜像到 registry
- 通知 Node Server 部署
- 验证发布状态
- 清晰的进度和错误提示
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from ..build_system.build_manager import BuildManager, BuildManagerError
from ..build_system.cloud_function_client import CloudFunctionClient, CloudFunctionError
from ..build_system.config_provider import ConfigProvider
from ..build_system.docker_client import DockerClient, DockerError
from ..build_system.publish_manager import PublishManager, PublishManagerError


def publish_command(
    skip_build: bool = False,
    config: Optional[str] = None,
    version: Optional[str] = None,
    namespace: Optional[str] = None,
    verify: bool = True,
    env_file: Optional[str] = None,
) -> bool:
    """
    执行发布命令

    Args:
        skip_build: 跳过构建，使用现有镜像
        config: 配置文件路径（可选）
        version: 指定版本号（可选）
        namespace: 镜像命名空间（可选）
        verify: 发布后验证部署状态（默认开启）
        env_file: 环境变量文件路径（默认: .env）

    Returns:
        True 如果发布成功，False 否则
    """
    print("🚀 开始发布智能体镜像...\n")

    # 获取项目目录（当前工作目录）
    project_dir = Path.cwd()

    # 验证项目目录
    if not (project_dir / "pyproject.toml").exists():
        print("❌ 错误: 当前目录不包含 pyproject.toml 文件")
        print("   请确保在项目根目录运行发布命令。")
        print()
        print("💡 提示:")
        print("   cd your-agent-project")
        print("   uni-agent publish")
        return False

    try:
        # 初始化配置提供者
        config_provider = ConfigProvider()

        # 如果指定了配置文件，加载配置
        if config:
            config_path = Path(config)
            if not config_path.exists():
                print(f"❌ 配置文件不存在: {config}")
                return False
            config_provider.load_from_file(config_path)

        # 初始化 Docker 客户端
        docker_client = DockerClient(verbose=True)

        # 检查 Docker 是否可用
        if not docker_client.is_docker_available():
            print("❌ Docker daemon 不可用")
            print()
            print("💡 解决方案:")
            print("   • macOS: 启动 Docker Desktop")
            print("   • Linux: sudo systemctl start docker")
            print("   • Windows: 启动 Docker Desktop")
            print("   • 检查 Docker 权限: sudo usermod -aG docker $USER")
            return False

        # 初始化构建管理器
        build_manager = BuildManager(
            project_dir=project_dir,
            docker_client=docker_client,
        )

        # 如果指定了版本，更新构建管理器的版本
        if version:
            build_manager.project_config["version"] = version

        # 初始化云函数客户端（如果需要）
        cloud_function_url = config_provider.get_cloud_function_url()
        if cloud_function_url:
            cloud_client = CloudFunctionClient(base_url=cloud_function_url)
        else:
            # 本地配置完整，不需要云函数
            cloud_client = CloudFunctionClient(base_url="http://localhost")  # Dummy URL

        # 初始化发布管理器
        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 执行发布流程（异步）
        result = asyncio.run(publish_manager.publish(skip_build=skip_build, env_file=env_file))

        if result["success"]:
            print("\n✅ 发布成功！")
            return True
        else:
            print("\n❌ 发布失败")
            return False

    except PublishManagerError as e:
        print(f"❌ 发布失败: {e}")
        print()
        print("💡 常见问题:")
        print("   • 检查 ROBOT_APPKEY 是否正确配置")
        print("   • 确保网络可访问云函数和 registry")
        print("   • 验证 Node Server 是否运行")
        return False

    except CloudFunctionError as e:
        print(f"❌ 云函数错误: {e}")
        print()
        print("💡 排查建议:")
        print("   • 检查 CLOUD_FUNCTION_URL 配置")
        print("   • 验证 ROBOT_APPKEY 是否有效")
        print("   • 确保网络连接正常")
        return False

    except BuildManagerError as e:
        print(f"❌ 构建失败: {e}")
        print()
        print("💡 常见问题:")
        print("   • 检查 pyproject.toml 格式是否正确")
        print("   • 确保项目名称和版本已定义")
        print("   • 检查 Dockerfile 语法（如果自定义）")
        return False

    except DockerError as e:
        print(f"❌ Docker 错误: {e}")
        print()
        print("💡 排查建议:")
        print("   • 检查 Docker daemon 是否运行")
        print("   • 检查磁盘空间是否充足")
        print("   • 尝试清理旧镜像: docker system prune")
        return False

    except KeyboardInterrupt:
        print("\n⏸️  发布已取消")
        return False

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        print("   请检查日志或联系支持团队。")
        return False


def add_publish_command(subparsers):
    """
    添加 publish 命令到 argparse 子解析器

    Args:
        subparsers: argparse 子解析器对象
    """
    publish_parser = subparsers.add_parser(
        "publish",
        help="发布智能体镜像到云端",
        description="发布智能体 Docker 镜像到 registry，并通知 Node Server 部署",
    )

    publish_parser.add_argument(
        "--skip-build",
        action="store_true",
        help="跳过构建，直接使用现有镜像发布",
    )

    publish_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="指定配置文件路径（如 .env 文件）",
    )

    publish_parser.add_argument(
        "--version",
        "-v",
        type=str,
        default=None,
        help="指定镜像版本号（如 1.0.0）。如果不指定，将使用 pyproject.toml 中的版本。",
    )

    publish_parser.add_argument(
        "--namespace",
        "-n",
        type=str,
        default=None,
        help="指定镜像命名空间（如 robots）。如果不指定，使用云函数返回的默认值。",
    )

    publish_parser.add_argument(
        "--verify",
        action="store_true",
        default=True,
        help="发布后验证部署状态（默认开启）",
    )

    publish_parser.add_argument(
        "--no-verify",
        dest="verify",
        action="store_false",
        help="跳过发布后验证",
    )

    publish_parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="环境变量文件路径（默认: .env，生产环境可使用 .env.prod）",
    )

    publish_parser.set_defaults(
        func=lambda args: publish_command(
            skip_build=args.skip_build,
            config=args.config,
            version=args.version,
            namespace=args.namespace,
            verify=args.verify,
            env_file=args.env_file,
        )
    )


__all__ = ["publish_command", "add_publish_command"]
