"""CLI command implementations."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from .scaffold import ScaffoldError, create_scaffold


def _check_python_version() -> Tuple[bool, str]:
    """
    检查 Python 版本是否满足要求（>=3.8）

    Returns:
        (是否满足要求, 版本字符串)
    """
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, version_str

    return True, version_str


def _create_virtual_env(project_dir: Path) -> Tuple[bool, str]:
    """
    为项目创建虚拟环境

    Args:
        project_dir: 项目根目录

    Returns:
        (成功或否, 消息)
    """
    venv_dir = project_dir / ".venv"

    print("📦 正在创建虚拟环境...")

    try:
        # 创建虚拟环境
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            capture_output=True,
            check=True,
            timeout=60,
        )
        print(f"✅ 虚拟环境已创建: {venv_dir}")
        return True, "虚拟环境创建成功"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        return False, f"虚拟环境创建失败: {error_msg}"
    except subprocess.TimeoutExpired:
        return False, "虚拟环境创建超时"
    except Exception as e:
        return False, f"虚拟环境创建异常: {e}"


def _install_dependencies(project_dir: Path) -> Tuple[bool, str]:
    """
    在虚拟环境中安装依赖

    Args:
        project_dir: 项目根目录

    Returns:
        (成功或否, 消息)
    """
    venv_dir = project_dir / ".venv"
    requirements_file = project_dir / "requirements.txt"

    if not requirements_file.exists():
        return True, "requirements.txt 不存在，跳过依赖安装"

    print("📚 正在安装依赖...")

    # 确定 pip 的路径
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip"
    else:
        pip_path = venv_dir / "bin" / "pip"

    try:
        # 安装依赖
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            capture_output=True,
            check=True,
            timeout=300,  # 5 分钟超时
        )
        print(f"✅ 依赖已安装")
        return True, "依赖安装成功"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        # 只返回 warning，不中断流程
        print(f"⚠️  依赖安装失败（可稍后手动重试）: {error_msg[:100]}")
        return True, "依赖安装失败但继续"
    except subprocess.TimeoutExpired:
        print("⚠️  依赖安装超时（可稍后手动重试）")
        return True, "依赖安装超时但继续"
    except Exception as e:
        print(f"⚠️  依赖安装异常（可稍后手动重试）: {e}")
        return True, "依赖安装异常但继续"


def init_project(
    name: str, template: str = "basic", skip_venv: bool = False
) -> bool:
    """
    初始化新项目

    功能：
    1. 检测 Python 版本
    2. 生成项目骨架
    3. 创建虚拟环境
    4. 安装依赖

    Args:
        name: 项目名称
        template: 项目模板（default: basic）
        skip_venv: 跳过虚拟环境创建和依赖安装

    Returns:
        是否成功
    """
    print(f"🚀 创建新项目: {name}")
    print(f"📋 使用模板: {template}")

    # 检查 Python 版本
    print(f"🐍 检测 Python 版本...")
    py_ok, py_version = _check_python_version()
    print(f"   Python {py_version}", end="")
    if py_ok:
        print(" ✅")
    else:
        print(" ❌")
        print(f"❌ 错误: 需要 Python 3.8+，当前为 {py_version}")
        return False

    # 创建项目骨架
    try:
        project_dir = create_scaffold(Path.cwd(), name, template)
    except FileExistsError:
        print(f"❌ 错误: 目录 '{name}' 已存在")
        return False
    except ScaffoldError as exc:
        print(f"❌ 模板错误: {exc}")
        return False
    except Exception as exc:
        print(f"❌ 创建项目失败: {exc}")
        return False

    print("✅ 项目骨架已生成")

    # 可选：创建虚拟环境和安装依赖
    if not skip_venv:
        venv_ok, venv_msg = _create_virtual_env(project_dir)
        if not venv_ok:
            print(f"⚠️  {venv_msg}")
            # 继续执行，不中断

        dep_ok, dep_msg = _install_dependencies(project_dir)
        # 依赖安装失败不中断（会返回 True）

    # 显示项目信息和后续步骤
    print("\n✅ 项目创建成功！")
    print("\n📍 项目位置: " + str(project_dir.resolve()))
    print("\n下一步:")

    if skip_venv:
        print(f"  cd {project_dir.name}")
        print("  python -m venv .venv")
        print("  source .venv/bin/activate  # Windows: .venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
    else:
        # 根据操作系统显示激活命令
        activate_cmd = (
            ".venv\\Scripts\\activate"
            if sys.platform == "win32"
            else "source .venv/bin/activate"
        )
        print(f"  cd {project_dir.name}")
        print(f"  {activate_cmd}")

    print("  cp .env.example .env")
    print(
        f"  python -m {project_dir.name.replace('-', '_')}.main"
    )

    print("\n💡 开发提示:")
    print("  • 编辑 {}/agents/{}_agent.py 来实现你的智能体逻辑".format(
        project_dir.name.replace("-", "_"),
        project_dir.name.replace("-", "_"),
    ))
    print("  • 查看 README.md 了解项目结构")
    print("  • 运行 pytest 来测试你的代码")

    return True


def run_agent(
    config_file: Optional[str] = None,
    debug: bool = False,
    port: Optional[int] = None,
    env: Optional[dict] = None,
) -> bool:
    """在本地启动智能体容器并显示日志

    功能：
    1. 获取最后构建的镜像
    2. 启动容器
    3. 实时显示日志
    4. 优雅关闭

    Args:
        config_file: 配置文件路径（可选）
        debug: 是否启用调试模式
        port: 主机端口（可选，None 表示不绑定端口）
        env: 环境变量字典（可选）

    Returns:
        是否成功
    """
    import asyncio

    from ..build_system.docker_client import DockerClient
    from ..build_system.run_manager import RunManager, RunManagerError

    if debug:
        print("🐛 调试模式已启用")

    if config_file and not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        return False

    try:
        # 初始化运行管理器
        docker_client = DockerClient(verbose=debug)

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

        run_manager = RunManager(
            project_dir=Path.cwd(),
            docker_client=docker_client,
        )

        # 运行容器并显示日志
        asyncio.run(run_manager.run(port=port, env=env))
        return True

    except RunManagerError as e:
        print(f"❌ 运行失败: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏸️  运行已被中断")
        return True
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def run_tests(verbose: bool = False) -> bool:
    """Run pytest in the current working directory."""
    print("🧪 运行测试...")

    cmd = ["python", "-m", "pytest"]
    if verbose:
        cmd.append("-v")
    if os.path.exists("tests"):
        cmd.append("tests")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("❌ pytest 未安装，请先安装: pip install pytest")
        return False
    except Exception as exc:
        print(f"❌ 运行测试失败: {exc}")
        return False

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


__all__ = ["init_project", "run_agent", "run_tests"]
