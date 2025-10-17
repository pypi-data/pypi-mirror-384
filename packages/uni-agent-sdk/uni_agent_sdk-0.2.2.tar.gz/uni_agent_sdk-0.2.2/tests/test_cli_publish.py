"""
CLI publish 命令测试

测试 CLI publish 命令的各种场景，包括：
- 基础发布命令
- 跳过构建参数
- 指定版本参数
- 指定配置文件
- 验证开关
- 错误处理
- 帮助信息显示
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from uni_agent_sdk.build_system.build_manager import BuildManagerError
from uni_agent_sdk.build_system.cloud_function_client import CloudFunctionError
from uni_agent_sdk.build_system.config_provider import ConfigProvider
from uni_agent_sdk.build_system.docker_client import DockerError
from uni_agent_sdk.build_system.publish_manager import PublishManagerError
from uni_agent_sdk.cli.publish import publish_command


class TestPublishCommand:
    """测试 publish_command 函数"""

    def test_publish_command_basic(self, tmp_path: Path, monkeypatch):
        """测试基础发布命令"""
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

        # 创建 .env 文件
        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
REGISTRY_URL=registry.example.com:5000
REGISTRY_USERNAME=admin
REGISTRY_PASSWORD=password123
NODE_SERVER_URL=http://localhost:8000
NODE_SERVER_TOKEN=test-token
"""
        (project_dir / ".env").write_text(env_content)

        # 切换到项目目录
        monkeypatch.chdir(project_dir)

        # Mock 所有依赖
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            # 配置 ConfigProvider mock
            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            # 配置 DockerClient mock
            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            # 配置 BuildManager mock
            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 配置 CloudFunctionClient mock
            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            # 配置 PublishManager mock
            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 配置 asyncio.run 返回成功结果
            mock_asyncio_run.return_value = {
                "success": True,
                "image_url": "registry.example.com:5000/robots/test-agent:1.0.0",
                "robot_id": "robot-12345",
                "deployment_status": "deploying",
                "task_id": "deploy-abc123",
            }

            # 执行命令
            result = publish_command()

            # 验证
            assert result is True
            mock_docker.is_docker_available.assert_called_once()
            mock_asyncio_run.assert_called_once()

    def test_publish_command_skip_build(self, tmp_path: Path, monkeypatch):
        """测试跳过构建参数"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            mock_asyncio_run.return_value = {
                "success": True,
                "image_url": "registry.example.com:5000/robots/test-agent:1.0.0",
                "robot_id": "robot-12345",
                "deployment_status": "deploying",
                "task_id": "deploy-abc123",
            }

            # 执行命令，跳过构建
            result = publish_command(skip_build=True)

            # 验证
            assert result is True
            # 验证 publish 方法被调用时传入了 skip_build=True
            mock_publish_mgr.publish = AsyncMock(
                return_value={
                    "success": True,
                    "image_url": "registry.example.com:5000/robots/test-agent:1.0.0",
                    "robot_id": "robot-12345",
                    "deployment_status": "deploying",
                    "task_id": "deploy-abc123",
                }
            )

    def test_publish_command_with_version(self, tmp_path: Path, monkeypatch):
        """测试指定版本参数"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            mock_asyncio_run.return_value = {
                "success": True,
                "image_url": "registry.example.com:5000/robots/test-agent:2.0.0",
                "robot_id": "robot-12345",
                "deployment_status": "deploying",
                "task_id": "deploy-abc123",
            }

            # 执行命令，指定版本
            result = publish_command(version="2.0.0")

            # 验证
            assert result is True
            # 验证版本被更新
            assert mock_build_mgr.project_config["version"] == "2.0.0"

    def test_publish_command_with_config_file(self, tmp_path: Path, monkeypatch):
        """测试指定配置文件"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        # 创建自定义配置文件
        custom_config_path = project_dir / "custom.env"
        custom_config_content = """
ROBOT_APPKEY=custom-appkey
CLOUD_FUNCTION_URL=http://custom.example.com
"""
        custom_config_path.write_text(custom_config_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = (
                "http://custom.example.com"
            )
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            mock_asyncio_run.return_value = {
                "success": True,
                "image_url": "registry.example.com:5000/robots/test-agent:1.0.0",
                "robot_id": "robot-12345",
                "deployment_status": "deploying",
                "task_id": "deploy-abc123",
            }

            # 执行命令，指定配置文件
            result = publish_command(config=str(custom_config_path))

            # 验证
            assert result is True
            mock_config.load_from_file.assert_called_once()

    def test_publish_command_no_pyproject(self, tmp_path: Path, monkeypatch):
        """测试缺少 pyproject.toml 的情况"""
        # 创建空目录（没有 pyproject.toml）
        project_dir = tmp_path / "empty-project"
        project_dir.mkdir()

        monkeypatch.chdir(project_dir)

        # 执行命令
        result = publish_command()

        # 验证失败
        assert result is False

    def test_publish_command_config_file_not_found(self, tmp_path: Path, monkeypatch):
        """测试配置文件不存在的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        monkeypatch.chdir(project_dir)

        # 执行命令，指定不存在的配置文件
        result = publish_command(config="nonexistent.env")

        # 验证失败
        assert result is False

    def test_publish_command_docker_not_available(self, tmp_path: Path, monkeypatch):
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

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            # Docker 不可用
            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = False
            mock_docker_cls.return_value = mock_docker

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False

    def test_publish_command_publish_manager_error(self, tmp_path: Path, monkeypatch):
        """测试 PublishManager 抛出异常的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟发布失败
            mock_asyncio_run.side_effect = PublishManagerError("发布失败")

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False

    def test_publish_command_cloud_function_error(self, tmp_path: Path, monkeypatch):
        """测试云函数错误的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟云函数错误
            mock_asyncio_run.side_effect = CloudFunctionError("云函数调用失败")

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False

    def test_publish_command_build_manager_error(self, tmp_path: Path, monkeypatch):
        """测试构建管理器错误的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟构建错误
            mock_asyncio_run.side_effect = BuildManagerError("构建失败")

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False

    def test_publish_command_docker_error(self, tmp_path: Path, monkeypatch):
        """测试 Docker 错误的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟 Docker 错误
            mock_asyncio_run.side_effect = DockerError("Docker 推送失败")

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False

    def test_publish_command_keyboard_interrupt(self, tmp_path: Path, monkeypatch):
        """测试用户中断的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟用户中断
            mock_asyncio_run.side_effect = KeyboardInterrupt()

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False

    def test_publish_command_generic_exception(self, tmp_path: Path, monkeypatch):
        """测试未知异常的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟未知异常
            mock_asyncio_run.side_effect = RuntimeError("未知错误")

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False


class TestPublishCommandCLI:
    """测试 CLI 集成"""

    def test_cli_help(self):
        """测试帮助信息显示"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "publish", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证帮助信息包含关键内容
        assert result.returncode == 0
        assert "发布智能体镜像" in result.stdout or "发布智能体" in result.stdout
        assert "--skip-build" in result.stdout
        assert "--config" in result.stdout
        assert "--version" in result.stdout

    def test_cli_skip_build_option(self):
        """测试 skip-build 选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "publish", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --skip-build 选项存在
        assert "--skip-build" in result.stdout

    def test_cli_config_option(self):
        """测试 config 选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "publish", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --config 选项存在
        assert "--config" in result.stdout or "-c" in result.stdout

    def test_cli_version_option(self):
        """测试 version 选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "publish", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --version 选项存在
        assert "--version" in result.stdout or "-v" in result.stdout

    def test_cli_verify_options(self):
        """测试 verify 选项存在"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "publish", "--help"],
            capture_output=True,
            text=True,
        )

        # 验证 --verify 和 --no-verify 选项存在
        assert "--verify" in result.stdout or "--no-verify" in result.stdout


class TestPublishCommandEdgeCases:
    """测试边缘情况"""

    def test_publish_with_all_options(self, tmp_path: Path, monkeypatch):
        """测试指定所有选项的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        custom_config_path = project_dir / "custom.env"
        custom_config_content = """
ROBOT_APPKEY=custom-appkey
CLOUD_FUNCTION_URL=http://custom.example.com
"""
        custom_config_path.write_text(custom_config_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = (
                "http://custom.example.com"
            )
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            mock_asyncio_run.return_value = {
                "success": True,
                "image_url": "registry.example.com:5000/custom-ns/test-agent:3.0.0",
                "robot_id": "robot-12345",
                "deployment_status": "deploying",
                "task_id": "deploy-abc123",
            }

            # 执行命令，指定所有选项
            result = publish_command(
                skip_build=True,
                config=str(custom_config_path),
                version="3.0.0",
                namespace="custom-ns",
                verify=False,
            )

            # 验证
            assert result is True
            assert mock_build_mgr.project_config["version"] == "3.0.0"

    def test_publish_failed_result(self, tmp_path: Path, monkeypatch):
        """测试发布失败（返回 success=False）的情况"""
        project_dir = tmp_path / "test-agent"
        project_dir.mkdir()

        pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
        (project_dir / "pyproject.toml").write_text(pyproject_content)

        env_content = """
ROBOT_APPKEY=test-appkey
CLOUD_FUNCTION_URL=http://test.example.com
"""
        (project_dir / ".env").write_text(env_content)

        monkeypatch.chdir(project_dir)

        # Mock
        with patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.DockerClient"
        ) as mock_docker_cls, patch(
            "uni_agent_sdk.cli.publish.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.asyncio.run"
        ) as mock_asyncio_run:

            mock_config = MagicMock()
            mock_config.get_cloud_function_url.return_value = "http://test.example.com"
            mock_config_cls.return_value = mock_config

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {"name": "test-agent", "version": "1.0.0"}
            mock_build_mgr_cls.return_value = mock_build_mgr

            mock_cloud = MagicMock()
            mock_cloud_cls.return_value = mock_cloud

            mock_publish_mgr = MagicMock()
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 模拟发布失败（但没有抛异常）
            mock_asyncio_run.return_value = {
                "success": False,
            }

            # 执行命令
            result = publish_command()

            # 验证失败
            assert result is False
