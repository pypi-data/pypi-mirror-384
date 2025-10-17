"""
CLI build 命令集成测试

测试 build 命令在真实项目结构上的工作情况
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestBuildCommandIntegration:
    """测试 build 命令在真实项目上的集成"""

    def test_build_command_on_oss_agent(self, monkeypatch):
        """测试在 oss-agent 项目上运行 build 命令"""
        # 查找 oss-agent 项目
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过集成测试")

        # 切换到 oss-agent 目录
        monkeypatch.chdir(oss_agent_dir)

        # Mock Docker 操作（避免真实构建）
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            # 配置 mock
            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            # Mock BuildManager 来读取真实的 pyproject.toml
            from uni_agent_sdk.build_system.build_manager import BuildManager
            from uni_agent_sdk.build_system.docker_client import DockerClient

            # 创建真实的 BuildManager 来读取配置
            real_docker = DockerClient(verbose=False)
            real_build_mgr = BuildManager(oss_agent_dir, real_docker)

            # 验证项目配置被正确读取
            assert real_build_mgr.project_config["name"] == "oss-agent"
            assert real_build_mgr.project_config["version"] == "1.0.0"
            assert real_build_mgr.project_config["package_name"] == "oss_agent"

            # Mock build_image 方法
            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = real_build_mgr.project_config
            mock_build_mgr.build_image.return_value = "robot-oss-agent:1.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行 build 命令
            from uni_agent_sdk.cli.build import build_command

            result = build_command()

            # 验证成功
            assert result is True
            mock_build_mgr.build_image.assert_called_once()

    def test_build_command_with_custom_version(self, monkeypatch):
        """测试在 oss-agent 上指定自定义版本"""
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过集成测试")

        monkeypatch.chdir(oss_agent_dir)

        # Mock
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.build_image.return_value = "robot-oss-agent:2.0.0"
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 执行命令，指定版本
            from uni_agent_sdk.cli.build import build_command

            result = build_command(version="2.0.0")

            # 验证
            assert result is True
            mock_build_mgr.build_image.assert_called_once_with(
                version="2.0.0", rebuild=False
            )


class TestBuildCommandRealProjectValidation:
    """验证真实项目配置读取"""

    def test_read_oss_agent_config(self):
        """测试读取 oss-agent 的 pyproject.toml"""
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过测试")

        from uni_agent_sdk.build_system.build_manager import BuildManager
        from uni_agent_sdk.build_system.docker_client import DockerClient

        # 创建 BuildManager（不执行构建）
        docker_client = DockerClient(verbose=False)
        build_manager = BuildManager(oss_agent_dir, docker_client)

        # 验证配置
        config = build_manager.project_config
        assert config["name"] == "oss-agent"
        assert config["version"] == "1.0.0"
        assert config["package_name"] == "oss_agent"

    def test_version_determination_logic(self):
        """测试版本确定逻辑"""
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过测试")

        from uni_agent_sdk.build_system.build_manager import BuildManager
        from uni_agent_sdk.build_system.docker_client import DockerClient

        docker_client = DockerClient(verbose=False)
        build_manager = BuildManager(oss_agent_dir, docker_client)

        # 测试版本确定逻辑
        # 1. 指定版本
        version = build_manager._determine_version("2.0.0")
        assert version == "2.0.0"

        # 2. 使用 pyproject.toml 版本
        version = build_manager._determine_version(None)
        assert version == "1.0.0"  # 从 pyproject.toml


class TestBuildCommandCLIIntegration:
    """测试 CLI 完整流程"""

    def test_cli_build_help_integration(self):
        """测试 CLI help 显示正确的 build 命令信息"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "build", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "构建智能体 Docker 镜像" in result.stdout
        assert "--version" in result.stdout
        assert "--rebuild" in result.stdout
        assert "--no-cache" in result.stdout
        assert "--config" in result.stdout

    def test_cli_main_help_shows_build(self):
        """测试主 CLI help 显示 build 命令"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "build" in result.stdout
        assert (
            "构建智能体 Docker 镜像" in result.stdout
            or "构建智能体镜像" in result.stdout
        )
