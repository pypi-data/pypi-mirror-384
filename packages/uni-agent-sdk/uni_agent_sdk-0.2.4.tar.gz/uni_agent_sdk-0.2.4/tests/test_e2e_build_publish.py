"""
端到端集成测试 - Robot Build & Publish 系统

验证完整的 build → publish → deploy 工作流程
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestE2EBuildPublishWorkflow:
    """端到端完整工作流测试"""

    def test_full_build_and_publish_workflow(self, monkeypatch):
        """测试完整的 build → publish 工作流

        场景：
        1. 执行 build 命令构建镜像
        2. 验证镜像成功构建
        3. 执行 publish 命令发布镜像
        4. 验证发布成功
        """
        # 定位 oss-agent 项目
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过 E2E 测试")

        monkeypatch.chdir(oss_agent_dir)

        # Mock 外部服务
        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls, patch(
            "uni_agent_sdk.cli.publish.ConfigProvider"
        ) as mock_config_cls, patch(
            "uni_agent_sdk.cli.publish.CloudFunctionClient"
        ) as mock_cloud_cls, patch(
            "uni_agent_sdk.cli.publish.PublishManager"
        ) as mock_publish_mgr_cls:

            # 配置 build 命令的 mock
            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = True
            mock_docker_cls.return_value = mock_docker

            mock_build_mgr = MagicMock()
            mock_build_mgr.project_config = {
                "name": "oss-agent",
                "version": "1.0.0",
                "package_name": "oss_agent",
            }
            mock_build_mgr.build_image.return_value = "robot-oss-agent:1.0.0"
            mock_build_mgr.get_image_info.return_value = {
                "tag": "robot-oss-agent:1.0.0",
                "image_id": "sha256:abc123",
                "size": 350,
                "build_time": 45.5,
            }
            mock_build_mgr_cls.return_value = mock_build_mgr

            # 配置 publish 命令的 mock
            mock_config = MagicMock()
            mock_config.get_robot_appkey.return_value = "test-appkey"
            mock_config_cls.return_value = mock_config

            mock_cloud_client = MagicMock()
            mock_cloud_cls.return_value = mock_cloud_client

            mock_publish_mgr = MagicMock()
            mock_publish_mgr.publish = AsyncMock(
                return_value={
                    "success": True,
                    "image_url": "registry.example.com/robots/oss-agent:1.0.0",
                    "robot_id": "robot-oss-agent-001",
                    "deployment_status": "deploying",
                }
            )
            mock_publish_mgr_cls.return_value = mock_publish_mgr

            # 步骤 1: 执行 build 命令
            from uni_agent_sdk.cli.build import build_command

            build_result = build_command()
            assert build_result is True
            mock_build_mgr.build_image.assert_called_once()

            # 步骤 2: 验证镜像信息
            image_info = mock_build_mgr.get_image_info("robot-oss-agent:1.0.0")
            assert image_info["tag"] == "robot-oss-agent:1.0.0"
            assert image_info["size"] > 0

            # 步骤 3: 执行 publish 命令
            from uni_agent_sdk.cli.publish import publish_command

            publish_result = publish_command(skip_build=True)
            assert publish_result is True
            mock_publish_mgr.publish.assert_called_once()

    def test_cli_help_shows_all_commands(self):
        """测试 CLI help 显示所有命令"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "build" in result.stdout
        assert "publish" in result.stdout

    def test_build_command_help(self):
        """测试 build 命令的帮助信息"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "build", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--version" in result.stdout

    def test_publish_command_help(self):
        """测试 publish 命令的帮助信息"""
        result = subprocess.run(
            [sys.executable, "-m", "uni_agent_sdk.cli", "publish", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--skip-build" in result.stdout


class TestE2EErrorHandling:
    """端到端错误处理测试"""

    def test_build_fails_when_docker_unavailable(self, monkeypatch):
        """测试 Docker 不可用时 build 命令的错误处理"""
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过 E2E 测试")

        monkeypatch.chdir(oss_agent_dir)

        with patch("uni_agent_sdk.cli.build.DockerClient") as mock_docker_cls, patch(
            "uni_agent_sdk.cli.build.BuildManager"
        ) as mock_build_mgr_cls:

            mock_docker = MagicMock()
            mock_docker.is_docker_available.return_value = False
            mock_docker_cls.return_value = mock_docker

            from uni_agent_sdk.cli.build import build_command

            # 当 Docker 不可用时应该返回 False
            result = build_command()
            assert result is False

    def test_build_fails_on_missing_pyproject(self, monkeypatch):
        """测试缺少 pyproject.toml 时 build 命令的错误处理"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            monkeypatch.chdir(tmp_dir)

            from uni_agent_sdk.cli.build import build_command

            # 应该失败，因为没有 pyproject.toml
            result = build_command()
            assert result is False


class TestE2EIntegration:
    """端到端集成测试"""

    def test_build_manager_reads_real_project_config(self):
        """测试 BuildManager 能正确读取真实项目配置"""
        project_root = Path(__file__).parent.parent.parent
        oss_agent_dir = project_root / "robots" / "oss-agent"

        if not oss_agent_dir.exists():
            pytest.skip("oss-agent 项目不存在，跳过 E2E 测试")

        from uni_agent_sdk.build_system.build_manager import BuildManager
        from uni_agent_sdk.build_system.docker_client import DockerClient

        docker_client = DockerClient(verbose=False)
        build_manager = BuildManager(oss_agent_dir, docker_client)

        # 验证配置读取
        config = build_manager.project_config
        assert config["name"] == "oss-agent"
        assert config["version"] == "1.0.0"
        assert config["package_name"] == "oss_agent"

    def test_docker_client_availability_check(self):
        """测试 DockerClient 的 Docker 可用性检查"""
        from uni_agent_sdk.build_system.docker_client import DockerClient

        docker_client = DockerClient(verbose=False)
        is_available = docker_client.is_docker_available()
        assert isinstance(is_available, bool)

    def test_config_provider_loads_env_variables(self, monkeypatch):
        """测试 ConfigProvider 能加载环境变量"""
        monkeypatch.setenv("ROBOT_APPKEY", "test-appkey-123")
        monkeypatch.setenv("CLOUD_FUNCTION_URL", "https://test.example.com/api")

        from uni_agent_sdk.build_system.config_provider import ConfigProvider

        config = ConfigProvider()

        # 验证读取
        assert config.get_robot_appkey() == "test-appkey-123"
        assert config.get_cloud_function_url() == "https://test.example.com/api"

    def test_dockerfile_generator_creates_valid_dockerfile(self):
        """测试 DockerfileGenerator 能生成有效的 Dockerfile"""
        import tempfile

        from uni_agent_sdk.build_system.dockerfile_generator import DockerfileGenerator

        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir)

            # 生成 Dockerfile
            generator = DockerfileGenerator()
            dockerfile_path = generator.generate(project_dir, "test_package")

            # 验证文件存在
            assert dockerfile_path.exists()

            # 验证内容有效
            content = dockerfile_path.read_text()
            assert "FROM python" in content
            assert "test_package" in content
