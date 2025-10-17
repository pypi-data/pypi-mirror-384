"""
CLI build 命令测试

测试 CLI build 命令的各种场景，包括：
- 基础构建命令
- 指定版本参数
- 强制重建参数
- 禁用缓存参数
- 错误处理
- 帮助信息显示
"""

import subprocess
import sys
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from uni_agent_sdk.build_system.build_manager import BuildManagerError
from uni_agent_sdk.build_system.docker_client import DockerError
from uni_agent_sdk.cli.build import build_command


class TestBuildCommand:
    """测试 build_command 函数"""

    def test_build_command_basic(self, tmp_path: Path, monkeypatch):
        """测试基础构建命令"""
        # 创建测试项目结构
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        # 创建 pyproject.toml
        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        # 切换到项目目录
        monkeypatch.chdir(project_dir)

        # Mock Docker 客户端和构建管理器
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            # 配置 mock
            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-test-agent:1.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令
            result = build_command()

            # 验证
            assert result is True
            mock_docker.is_docker_available.assert_called_once()
            mock_build_mgr.build_image.assert_called_once_with(
                version=None,
                rebuild=False,
            )

    def test_build_command_with_version(self, tmp_path: Path, monkeypatch):
        """测试指定版本参数"""
        # 创建测试项目
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-test-agent:2.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令，指定版本
            result = build_command(version="2.0.0")

            # 验证
            assert result is True
            mock_build_mgr.build_image.assert_called_once_with(
                version="2.0.0",
                rebuild=False,
            )

    def test_build_command_with_rebuild(self, tmp_path: Path, monkeypatch):
        """测试强制重建参数"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-test-agent:1.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令，启用 rebuild
            result = build_command(rebuild=True)

            # 验证
            assert result is True
            mock_build_mgr.build_image.assert_called_once_with(
                version=None,
                rebuild=True,
            )

    def test_build_command_with_no_cache(self, tmp_path: Path, monkeypatch):
        """测试禁用缓存参数"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-test-agent:1.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令，启用 no_cache
            result = build_command(no_cache=True)

            # 验证
            assert result is True
            mock_build_mgr.build_image.assert_called_once_with(
                version=None,
                rebuild=True,  # no_cache 应该转换为 rebuild=True
            )

    def test_build_command_no_pyproject(self, tmp_path: Path, monkeypatch):
        """测试缺少 pyproject.toml 的情况"""
        # 创建空目录（没有 pyproject.toml）
        project_dir = tmp_path / "empty-project"
        project_dir.mkdir()

        monkeypatch.chdir(project_dir)

        # 执行命令
        result = build_command()

        # 验证失败
        assert result is False

    def test_build_command_docker_not_available(self, tmp_path: Path, monkeypatch):
        """测试 Docker 不可用的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock Docker 不可用
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls:
            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = False
            mock_docker_cls.return_value = mock_docker

            # 执行命令
            result = build_command()

            # 验证失败
            assert result is False

    def test_build_command_build_manager_error(self, tmp_path: Path, monkeypatch):
        """测试 BuildManager 抛出异常的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.side_effect = BuildManagerError("构建失败")
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令
            result = build_command()

            # 验证失败
            assert result is False

    def test_build_command_docker_error(self, tmp_path: Path, monkeypatch):
        """测试 Docker 操作失败的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.side_effect = DockerError("Docker 构建失败")
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令
            result = build_command()

            # 验证失败
            assert result is False

    def test_build_command_keyboard_interrupt(self, tmp_path: Path, monkeypatch):
        """测试用户中断的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.side_effect = KeyboardInterrupt()
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令
            result = build_command()

            # 验证失败
            assert result is False


class TestBuildCommandCLI:
    """测试 CLI 集成"""

    def test_cli_help(self):
        """测试帮助信息显示"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "build", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证帮助信息包含关键内容
        assert result.returncode == 0
        assert "构建智能体 Docker 镜像" in result.stdout
        assert "--version" in result.stdout
        assert "--rebuild" in result.stdout
        assert "--no-cache" in result.stdout

    def test_cli_version_option(self):
        """测试版本选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "build", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --version 选项存在
        assert "--version" in result.stdout or "-v" in result.stdout

    def test_cli_rebuild_option(self):
        """测试 rebuild 选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "build", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --rebuild 选项存在
        assert "--rebuild" in result.stdout

    def test_cli_no_cache_option(self):
        """测试 no-cache 选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "build", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --no-cache 选项存在
        assert "--no-cache" in result.stdout


class TestBuildCommandEdgeCases:
    """测试边缘情况"""

    def test_build_with_both_rebuild_and_no_cache(self, tmp_path: Path, monkeypatch):
        """测试同时指定 rebuild 和 no_cache 的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-test-agent:1.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令，同时启用两个参数
            result = build_command(rebuild=True, no_cache=True)

            # 验证
            assert result is True
            mock_build_mgr.build_image.assert_called_once_with(
                version=None,
                rebuild=True,  # 应该使用 True
            )

    def test_build_with_all_options(self, tmp_path: Path, monkeypatch):
        """测试指定所有选项的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-test-agent:3.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令，指定所有选项
            result = build_command(
                version="3.0.0",
                rebuild=True,
                config="custom.toml",
                tag="custom-tag",
                no_cache=True,
            )

            # 验证
            assert result is True
            mock_build_mgr.build_image.assert_called_once_with(
                version="3.0.0",
                rebuild=True,
            )

    def test_build_with_generic_exception(self, tmp_path: Path, monkeypatch):
        """测试未知异常的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.side_effect = RuntimeError("未知错误")
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令
            result = build_command()

            # 验证失败
            assert result is False
