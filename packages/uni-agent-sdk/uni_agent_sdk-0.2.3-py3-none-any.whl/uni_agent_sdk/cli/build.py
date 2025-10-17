"""
CLI build 命令实现

提供用户友好的构建命令接口，支持：
- 构建 Docker 镜像
- 指定版本号
- 强制重建（禁用缓存）
- 清晰的进度和错误提示
"""

import sys
from pathlib import Path
from typing import Optional

from ..build_system.build_manager import BuildManager, BuildManagerError
from ..build_system.docker_client import DockerClient, DockerError


def build_command(
    version: Optional[str] = None,
    rebuild: bool = False,
    config: Optional[str] = None,
    tag: Optional[str] = None,
    no_cache: bool = False,
) -> bool:
    """
    执行构建命令

    Args:
        version: 指定版本号（可选）
        rebuild: 强制重新构建（--rebuild）
        config: 配置文件路径（可选，暂未实现）
        tag: 自定义镜像标签（可选，暂未实现）
        no_cache: 禁用 Docker 缓存（--no-cache）

    Returns:
        True 如果构建成功，False 否则
    """
    print("🏗️  开始构建智能体镜像...\n")

    # 获取项目目录（当前工作目录）
    project_dir = Path.cwd()

    # 验证项目目录
    if not (project_dir / "pyproject.toml").exists():
        print("❌ 错误: 当前目录不包含 pyproject.toml 文件")
        print("   请确保在项目根目录运行构建命令。")
        print()
        print("💡 提示:")
        print("   cd your-agent-project")
        print("   uni-agent build")
        return False

    try:
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

        # 执行构建
        # rebuild 和 no_cache 是等价的，优先使用 no_cache
        use_no_cache = rebuild or no_cache

        image_tag = build_manager.build_image(
            version=version,
            rebuild=use_no_cache,
        )

        print(f"✅ 构建完成！镜像标签: {image_tag}")
        return True

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
        print("\n⏸️  构建已取消")
        return False

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        print("   请检查日志或联系支持团队。")
        return False


def add_build_command(subparsers):
    """
    添加 build 命令到 argparse 子解析器

    Args:
        subparsers: argparse 子解析器对象
    """
    build_parser = subparsers.add_parser(
        "build",
        help="构建智能体 Docker 镜像",
        description="构建智能体 Docker 镜像，自动读取 pyproject.toml 配置",
    )

    build_parser.add_argument(
        "--version",
        "-v",
        type=str,
        default=None,
        help="指定镜像版本号（如 1.0.0）。如果不指定，将使用 pyproject.toml 中的版本。",
    )

    build_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="强制重新构建，不使用缓存（等同于 --no-cache）",
    )

    build_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="禁用 Docker 缓存，强制重新构建所有层",
    )

    build_parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="指定配置文件路径（暂未实现）",
    )

    build_parser.add_argument(
        "--tag",
        "-t",
        type=str,
        default=None,
        help="自定义镜像标签（暂未实现）",
    )

    build_parser.set_defaults(
        func=lambda args: build_command(
            version=args.version,
            rebuild=args.rebuild,
            config=args.config,
            tag=args.tag,
            no_cache=args.no_cache,
        )
    )


__all__ = ["build_command", "add_build_command"]
