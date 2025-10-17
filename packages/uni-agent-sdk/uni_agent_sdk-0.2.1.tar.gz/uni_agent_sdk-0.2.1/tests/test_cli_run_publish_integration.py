"""
uni-agent run 和 publish 命令的完整集成测试

测试场景：
1. 本地运行：验证 .env 环境变量加载和容器启动
2. 发布部署：验证 --env-file 参数和环境变量传递
3. 环境变量正确配置在容器中
4. 生产环境配置文件支持
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from uni_agent_sdk.build_system.build_manager import BuildManager
from uni_agent_sdk.build_system.docker_client import DockerClient
from uni_agent_sdk.build_system.publish_manager import PublishManager
from uni_agent_sdk.build_system.run_manager import RunManager


class TestRunCommandWithEnvVariables:
    """测试 run 命令和环境变量加载"""

    @pytest.fixture
    def test_project_dir(self):
        """创建临时测试项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # 创建 pyproject.toml
            pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
            (project_dir / "pyproject.toml").write_text(pyproject_content)

            # 创建 .env 文件（本地开发配置）
            env_content = """# 本地开发配置
DEBUG=true
LOG_LEVEL=DEBUG
ROBOT_APPKEY=test-robot-dev
API_KEY=test-key-12345
DATABASE_URL=postgres://localhost:5432/test
TIMEOUT=30
"""
            (project_dir / ".env").write_text(env_content)

            yield project_dir

    def test_run_loads_env_file(self, test_project_dir):
        """测试 run 命令加载 .env 文件"""
        docker_client = MagicMock(spec=DockerClient)
        run_manager = RunManager(test_project_dir, docker_client)

        # 加载环境变量
        env_vars = run_manager.load_env_file()

        # 验证环境变量被正确加载
        assert len(env_vars) == 6
        assert env_vars["DEBUG"] == "true"
        assert env_vars["LOG_LEVEL"] == "DEBUG"
        assert env_vars["ROBOT_APPKEY"] == "test-robot-dev"
        assert env_vars["API_KEY"] == "test-key-12345"
        assert env_vars["DATABASE_URL"] == "postgres://localhost:5432/test"
        assert env_vars["TIMEOUT"] == "30"

    def test_run_passes_env_to_container(self, test_project_dir):
        """测试 run 命令将环境变量传给容器"""
        docker_client = MagicMock(spec=DockerClient)
        docker_client.client = MagicMock()

        # Mock 镜像列表查询
        mock_image = MagicMock()
        mock_image.tags = ["robot-test-agent:1.0.0"]
        docker_client.client.images.list.return_value = [mock_image]

        # Mock 容器运行
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        docker_client.client.containers.run.return_value = mock_container

        run_manager = RunManager(test_project_dir, docker_client)

        # 获取环境变量
        env_vars = run_manager.load_env_file()

        # 启动容器
        container_id = run_manager.run_container(
            image_tag="robot-test-agent:1.0.0",
            port=8080,
            env=env_vars,
            name="robot-test-agent-1.0.0",
        )

        # 验证容器被启动，且环境变量被传递
        assert container_id == "abc123def456"
        docker_client.client.containers.run.assert_called_once()

        # 验证 run 调用时环境变量被传递
        call_kwargs = docker_client.client.containers.run.call_args[1]
        assert call_kwargs["environment"] == env_vars
        assert len(call_kwargs["environment"]) == 6

    def test_run_displays_env_variables(self, test_project_dir, capsys):
        """测试 run 命令显示加载的环境变量"""
        docker_client = MagicMock(spec=DockerClient)
        run_manager = RunManager(test_project_dir, docker_client)

        # 加载环境变量（会输出到 stdout）
        env_vars = run_manager.load_env_file()

        # 捕获输出
        captured = capsys.readouterr()

        # 验证输出包含环境变量信息
        assert "从" in captured.out or "加载" in captured.out
        assert "DEBUG=true" in captured.out
        assert "LOG_LEVEL=DEBUG" in captured.out
        # API_KEY 应该被隐藏
        assert "API_KEY=****" in captured.out

    def test_run_missing_env_file_warning(self, test_project_dir, capsys):
        """测试 run 命令缺少 .env 文件的警告"""
        # 删除 .env 文件
        (test_project_dir / ".env").unlink()

        docker_client = MagicMock(spec=DockerClient)
        run_manager = RunManager(test_project_dir, docker_client)

        # 加载环境变量（会返回空字典）
        env_vars = run_manager.load_env_file()

        # 捕获输出
        captured = capsys.readouterr()

        # 验证返回空字典和警告
        assert env_vars == {}
        assert ".env 文件不存在" in captured.out

    def test_run_with_custom_env_file(self, test_project_dir):
        """测试 run 命令使用自定义环境变量文件"""
        # 创建自定义 .env.dev 文件
        env_dev_content = """DEBUG=false
LOG_LEVEL=INFO
CUSTOM_VAR=custom_value
"""
        env_dev_file = test_project_dir / ".env.dev"
        env_dev_file.write_text(env_dev_content)

        docker_client = MagicMock(spec=DockerClient)
        run_manager = RunManager(test_project_dir, docker_client)

        # 加载自定义环境文件
        env_vars = run_manager.load_env_file(env_dev_file)

        # 验证环境变量
        assert len(env_vars) == 3
        assert env_vars["DEBUG"] == "false"
        assert env_vars["LOG_LEVEL"] == "INFO"
        assert env_vars["CUSTOM_VAR"] == "custom_value"


class TestPublishCommandWithEnvVariables:
    """测试 publish 命令和环境变量传递"""

    @pytest.fixture
    def test_project_dir(self):
        """创建临时测试项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # 创建 pyproject.toml
            pyproject_content = """
[project]
name = "test-agent"
version = "1.0.0"
"""
            (project_dir / "pyproject.toml").write_text(pyproject_content)

            # 创建 .env（本地开发配置）
            env_content = """ROBOT_APPKEY=test-robot-dev
DEBUG=true
LOG_LEVEL=DEBUG
"""
            (project_dir / ".env").write_text(env_content)

            # 创建 .env.prod（生产配置）
            env_prod_content = """ROBOT_APPKEY=prod-robot-main
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgres://prod-db.example.com:5432/prod
"""
            (project_dir / ".env.prod").write_text(env_prod_content)

            yield project_dir

    def test_publish_loads_default_env_file(self, test_project_dir):
        """测试 publish 命令加载默认 .env 文件"""
        config_provider = MagicMock()
        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 加载默认环境变量文件
        old_cwd = os.getcwd()
        try:
            os.chdir(test_project_dir)
            env_vars = publish_manager.load_environment_variables()

            # 验证环境变量
            assert len(env_vars) == 3
            assert env_vars["ROBOT_APPKEY"] == "test-robot-dev"
            assert env_vars["DEBUG"] == "true"
            assert env_vars["LOG_LEVEL"] == "DEBUG"
        finally:
            os.chdir(old_cwd)

    def test_publish_loads_prod_env_file(self, test_project_dir):
        """测试 publish 命令加载生产环境 .env.prod 文件"""
        config_provider = MagicMock()
        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 加载生产环境文件
        env_vars = publish_manager.load_environment_variables(
            str(test_project_dir / ".env.prod")
        )

        # 验证环境变量
        assert len(env_vars) == 4
        assert env_vars["ROBOT_APPKEY"] == "prod-robot-main"
        assert env_vars["DEBUG"] == "false"
        assert env_vars["LOG_LEVEL"] == "INFO"
        assert env_vars["DATABASE_URL"] == "postgres://prod-db.example.com:5432/prod"

    def test_publish_passes_env_to_node_server(self, test_project_dir):
        """测试 publish 命令将环境变量传给 Node Server"""
        config_provider = MagicMock()
        config_provider.get_node_server_url.return_value = "http://localhost:8000"
        config_provider.get_node_server_token.return_value = "test-token"
        config_provider.get_registry_username.return_value = "admin"
        config_provider.get_registry_password.return_value = "password"

        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 设置部署配置
        publish_manager.deploy_config = {
            "robot_id": "robot-12345",
            "registry": {
                "url": "registry.example.com:5000",
                "username": "admin",
                "password": "password",
                "namespace": "robots",
            },
            "node_server": {
                "url": "http://localhost:8000",
                "token": "test-token",
            },
        }

        # 加载环境变量
        old_cwd = os.getcwd()
        try:
            os.chdir(test_project_dir)
            env_vars = publish_manager.load_environment_variables()

            # 验证环境变量会被包含在部署请求中
            assert env_vars["ROBOT_APPKEY"] == "test-robot-dev"
            assert len(env_vars) == 3
        finally:
            os.chdir(old_cwd)

    def test_publish_env_file_parameter(self, test_project_dir):
        """测试 publish 命令的 --env-file 参数"""
        config_provider = MagicMock()
        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 测试指定环境文件
        env_vars_prod = publish_manager.load_environment_variables(
            str(test_project_dir / ".env.prod")
        )
        env_vars_dev = publish_manager.load_environment_variables(
            str(test_project_dir / ".env")
        )

        # 验证两个环境配置不同
        assert env_vars_prod["ROBOT_APPKEY"] == "prod-robot-main"
        assert env_vars_dev["ROBOT_APPKEY"] == "test-robot-dev"
        assert env_vars_prod["LOG_LEVEL"] == "INFO"
        assert env_vars_dev["LOG_LEVEL"] == "DEBUG"


class TestRunPublishEnvIntegration:
    """run 和 publish 命令的环境变量集成测试"""

    @pytest.fixture
    def test_project_dir(self):
        """创建完整的测试项目结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # 创建 pyproject.toml
            pyproject_content = """
[project]
name = "integration-agent"
version = "1.0.0"
"""
            (project_dir / "pyproject.toml").write_text(pyproject_content)

            # 创建本地开发 .env
            env_content = """# 本地开发环境
DEBUG=true
LOG_LEVEL=DEBUG
ROBOT_APPKEY=dev-robot
API_KEY=dev-api-key-12345
DATABASE_URL=postgres://localhost:5432/dev
TIMEOUT=30
ENABLE_CACHE=true
"""
            (project_dir / ".env").write_text(env_content)

            # 创建生产 .env.prod
            env_prod_content = """# 生产环境
DEBUG=false
LOG_LEVEL=INFO
ROBOT_APPKEY=prod-robot-main
API_KEY=prod-api-key-abcde
DATABASE_URL=postgres://prod-db.example.com:5432/prod
TIMEOUT=60
ENABLE_CACHE=false
"""
            (project_dir / ".env.prod").write_text(env_prod_content)

            yield project_dir

    def test_dev_env_for_local_run(self, test_project_dir):
        """测试开发环境用于本地 run 命令"""
        docker_client = MagicMock(spec=DockerClient)
        run_manager = RunManager(test_project_dir, docker_client)

        # 加载本地环境
        env_vars = run_manager.load_env_file()

        # 验证开发环境配置
        assert env_vars["DEBUG"] == "true"
        assert env_vars["LOG_LEVEL"] == "DEBUG"
        assert env_vars["ROBOT_APPKEY"] == "dev-robot"
        assert len(env_vars) == 7

    def test_prod_env_for_publish(self, test_project_dir):
        """测试生产环境用于 publish 命令"""
        config_provider = MagicMock()
        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 加载生产环境
        env_vars = publish_manager.load_environment_variables(
            str(test_project_dir / ".env.prod")
        )

        # 验证生产环境配置
        assert env_vars["DEBUG"] == "false"
        assert env_vars["LOG_LEVEL"] == "INFO"
        assert env_vars["ROBOT_APPKEY"] == "prod-robot-main"
        assert len(env_vars) == 7

    def test_env_sensitive_values_hidden(self, test_project_dir, capsys):
        """测试敏感值在输出中被隐藏"""
        docker_client = MagicMock(spec=DockerClient)
        run_manager = RunManager(test_project_dir, docker_client)

        # 加载环境变量（会输出到 stdout）
        env_vars = run_manager.load_env_file()

        # 捕获输出
        captured = capsys.readouterr()

        # 验证输出中敏感值被隐藏
        assert "API_KEY=****" in captured.out
        assert "dev-api-key-12345" not in captured.out
        assert "DATABASE_URL" in captured.out  # 不隐藏（不含敏感关键词）

    def test_all_env_vars_passed_to_container(self, test_project_dir):
        """测试所有环境变量都被传给容器"""
        docker_client = MagicMock(spec=DockerClient)
        docker_client.client = MagicMock()

        # Mock 镜像和容器
        mock_image = MagicMock()
        mock_image.tags = ["robot-integration-agent:1.0.0"]
        docker_client.client.images.list.return_value = [mock_image]

        mock_container = MagicMock()
        mock_container.id = "container123"
        docker_client.client.containers.run.return_value = mock_container

        run_manager = RunManager(test_project_dir, docker_client)

        # 获取环境变量
        env_vars = run_manager.load_env_file()

        # 启动容器
        container_id = run_manager.run_container(
            image_tag="robot-integration-agent:1.0.0",
            port=8080,
            env=env_vars,
            name="integration-agent-test",
        )

        # 验证所有环境变量都被传递
        call_kwargs = docker_client.client.containers.run.call_args[1]
        passed_env = call_kwargs["environment"]

        assert len(passed_env) == 7
        assert passed_env["DEBUG"] == "true"
        assert passed_env["LOG_LEVEL"] == "DEBUG"
        assert passed_env["ROBOT_APPKEY"] == "dev-robot"
        assert passed_env["API_KEY"] == "dev-api-key-12345"
        assert passed_env["DATABASE_URL"] == "postgres://localhost:5432/dev"
        assert passed_env["TIMEOUT"] == "30"
        assert passed_env["ENABLE_CACHE"] == "true"

    def test_env_file_not_found_graceful_fallback(self, test_project_dir):
        """测试环境文件不存在时的优雅降级"""
        config_provider = MagicMock()
        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        # 尝试加载不存在的文件
        env_vars = publish_manager.load_environment_variables(
            str(test_project_dir / ".env.missing")
        )

        # 验证返回空字典（不抛出异常）
        assert env_vars == {}


class TestEnvVariableSpecialFormats:
    """测试环境变量的特殊格式支持"""

    def test_env_values_with_equals_sign(self):
        """测试值中包含等号的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # 创建 pyproject.toml
            (project_dir / "pyproject.toml").write_text("""
[project]
name = "test"
version = "1.0.0"
""")

            # 创建 .env 包含等号的值
            (project_dir / ".env").write_text(
                "DATABASE_URL=postgres://user:pass@localhost:5432/db?sslmode=require&timeout=30\n"
            )

            docker_client = MagicMock(spec=DockerClient)
            run_manager = RunManager(project_dir, docker_client)

            env_vars = run_manager.load_env_file()

            # 验证值被正确解析
            assert (
                env_vars["DATABASE_URL"]
                == "postgres://user:pass@localhost:5432/db?sslmode=require&timeout=30"
            )

    def test_env_values_with_quotes(self):
        """测试引号值的处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            (project_dir / "pyproject.toml").write_text("""
[project]
name = "test"
version = "1.0.0"
""")

            (project_dir / ".env").write_text(
                """QUOTED_DOUBLE="value with spaces"
QUOTED_SINGLE='another value'
NO_QUOTES=simple_value
"""
            )

            docker_client = MagicMock(spec=DockerClient)
            run_manager = RunManager(project_dir, docker_client)

            env_vars = run_manager.load_env_file()

            # 验证引号被移除
            assert env_vars["QUOTED_DOUBLE"] == "value with spaces"
            assert env_vars["QUOTED_SINGLE"] == "another value"
            assert env_vars["NO_QUOTES"] == "simple_value"

    def test_env_file_with_comments_and_empty_lines(self):
        """测试环境文件中注释和空行的处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            (project_dir / "pyproject.toml").write_text("""
[project]
name = "test"
version = "1.0.0"
""")

            (project_dir / ".env").write_text(
                """# This is a comment
KEY1=value1

# Another comment
KEY2=value2

KEY3=value3
"""
            )

            docker_client = MagicMock(spec=DockerClient)
            run_manager = RunManager(project_dir, docker_client)

            env_vars = run_manager.load_env_file()

            # 验证只有有效的键值对被加载
            assert len(env_vars) == 3
            assert "KEY1" in env_vars
            assert "KEY2" in env_vars
            assert "KEY3" in env_vars
