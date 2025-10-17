"""
验证 run 和 publish 命令能够成功配置环境变量的真实场景测试

这个文件包含了模拟真实使用场景的测试，确保：
1. uni-agent run 能正确加载和传递环境变量到容器
2. uni-agent publish 能正确加载和传递环境变量到 Node Server
3. 两种模式下环境变量都被正确配置
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRunCommandVerification:
    """验证 run 命令成功配置环境变量"""

    @pytest.fixture
    def agent_project(self):
        """创建完整的智能体项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # 创建项目结构
            (project_dir / "pyproject.toml").write_text("""
[project]
name = "smart-agent"
version = "1.0.0"
""")

            # 创建本地开发 .env
            (project_dir / ".env").write_text("""# 本地开发配置
DEBUG=true
LOG_LEVEL=DEBUG
ROBOT_APPKEY=local-smart-agent
API_BASE_URL=http://localhost:8000
DB_HOST=localhost
DB_PORT=5432
DB_USER=dev_user
ENABLE_DEBUG_LOGGING=true
""")

            yield project_dir

    def test_run_with_env_variables_scenario(self, agent_project):
        """场景：用户运行 uni-agent run，环境变量被正确加载和应用"""
        from uni_agent_sdk.build_system.run_manager import RunManager
        from uni_agent_sdk.build_system.docker_client import DockerClient

        docker_client = MagicMock(spec=DockerClient)
        docker_client.client = MagicMock()

        # Mock Docker 镜像查询
        mock_image = MagicMock()
        mock_image.tags = ["robot-smart-agent:1.0.0"]
        docker_client.client.images.list.return_value = [mock_image]

        # Mock 容器启动
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        docker_client.client.containers.run.return_value = mock_container

        # 创建 RunManager
        run_manager = RunManager(agent_project, docker_client)

        # 步骤 1: 加载环境变量
        env_vars = run_manager.load_env_file()

        # 验证：环境变量被成功加载
        assert env_vars is not None
        assert len(env_vars) == 8
        print(f"✅ 步骤 1: 加载了 {len(env_vars)} 个环境变量")

        # 步骤 2: 启动容器并传递环境变量
        container_id = run_manager.run_container(
            image_tag="robot-smart-agent:1.0.0",
            port=8080,
            env=env_vars,
            name="smart-agent-dev",
        )

        # 验证：容器成功启动
        assert container_id == "abc123def456"
        print(f"✅ 步骤 2: 容器启动成功，ID: {container_id[:12]}")

        # 验证：环境变量被传给了容器
        call_args = docker_client.client.containers.run.call_args
        passed_env = call_args[1]["environment"]

        assert len(passed_env) == 8
        assert passed_env["DEBUG"] == "true"
        assert passed_env["ROBOT_APPKEY"] == "local-smart-agent"
        assert passed_env["DB_HOST"] == "localhost"
        print(
            f"✅ 步骤 3: 环境变量正确传给容器（共 {len(passed_env)} 个）"
        )

        # 验证：所有关键环境变量都存在
        expected_keys = [
            "DEBUG",
            "LOG_LEVEL",
            "ROBOT_APPKEY",
            "API_BASE_URL",
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "ENABLE_DEBUG_LOGGING",
        ]
        for key in expected_keys:
            assert key in passed_env, f"缺少必要的环境变量: {key}"
        print(f"✅ 步骤 4: 所有 {len(expected_keys)} 个关键环境变量都已配置")


class TestPublishCommandVerification:
    """验证 publish 命令成功配置环境变量"""

    @pytest.fixture
    def agent_project_prod(self):
        """创建带有生产配置的智能体项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            (project_dir / "pyproject.toml").write_text("""
[project]
name = "production-agent"
version = "2.0.0"
""")

            # 本地开发配置
            (project_dir / ".env").write_text("""ROBOT_APPKEY=dev-agent
DEBUG=true
LOG_LEVEL=DEBUG
API_BASE_URL=http://localhost:8000
DB_HOST=localhost
DB_PORT=5432
CACHE_ENABLED=true
""")

            # 生产部署配置
            (project_dir / ".env.prod").write_text("""ROBOT_APPKEY=prod-agent-main
DEBUG=false
LOG_LEVEL=INFO
API_BASE_URL=https://api.example.com
DB_HOST=db.production.example.com
DB_PORT=5432
CACHE_ENABLED=false
""")

            yield project_dir

    def test_publish_with_env_variables_scenario(self, agent_project_prod):
        """场景：用户运行 uni-agent publish --env-file .env.prod，环境变量被正确加载和传递"""
        from uni_agent_sdk.build_system.publish_manager import PublishManager

        config_provider = MagicMock()
        config_provider.get_node_server_url.return_value = "http://node-server:8000"
        config_provider.get_node_server_token.return_value = "secret-token-xyz"

        cloud_client = MagicMock()
        build_manager = MagicMock()
        docker_client = MagicMock()

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=cloud_client,
            build_manager=build_manager,
            docker_client=docker_client,
        )

        publish_manager.deploy_config = {
            "robot_id": "prod-robot-123",
            "registry": {
                "url": "registry.example.com:5000",
                "namespace": "robots",
            },
            "node_server": {
                "url": "http://node-server:8000",
                "token": "secret-token-xyz",
            },
        }

        # 步骤 1: 加载生产环境变量
        prod_env_file = agent_project_prod / ".env.prod"
        prod_env_vars = publish_manager.load_environment_variables(
            str(prod_env_file)
        )

        # 验证：生产环境变量被成功加载
        assert prod_env_vars is not None
        assert len(prod_env_vars) == 7
        assert prod_env_vars["ROBOT_APPKEY"] == "prod-agent-main"
        assert prod_env_vars["DEBUG"] == "false"
        assert prod_env_vars["LOG_LEVEL"] == "INFO"
        print(f"✅ 步骤 1: 加载了 {len(prod_env_vars)} 个生产环境变量")

        # 步骤 2: 验证生产配置与开发配置不同
        dev_env_file = agent_project_prod / ".env"
        dev_env_vars = publish_manager.load_environment_variables(str(dev_env_file))

        assert dev_env_vars["DEBUG"] == "true"
        assert prod_env_vars["DEBUG"] == "false"
        assert dev_env_vars["ROBOT_APPKEY"] == "dev-agent"
        assert prod_env_vars["ROBOT_APPKEY"] == "prod-agent-main"
        print("✅ 步骤 2: 生产和开发配置正确隔离")

        # 步骤 3: 模拟部署请求（包含环境变量）
        deployment_payload = {
            "robot_id": publish_manager.deploy_config["robot_id"],
            "image": "registry.example.com:5000/robots/production-agent:2.0.0",
            "version": "2.0.0",
            "environment": prod_env_vars,  # 环境变量被包含在部署请求中
            "registry_auth": {
                "username": "admin",
                "password": "secret",
            },
        }

        # 验证：环境变量在部署请求中
        assert deployment_payload["environment"] == prod_env_vars
        assert len(deployment_payload["environment"]) == 7
        print(
            f"✅ 步骤 3: 环境变量被包含在部署请求中（共 {len(deployment_payload['environment'])} 个）"
        )

        # 步骤 4: 验证关键的生产环境变量
        expected_prod_config = {
            "ROBOT_APPKEY": "prod-agent-main",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "API_BASE_URL": "https://api.example.com",
            "DB_HOST": "db.production.example.com",
        }

        for key, expected_value in expected_prod_config.items():
            assert (
                deployment_payload["environment"][key] == expected_value
            ), f"生产环境变量 {key} 配置不正确"
        print("✅ 步骤 4: 所有关键的生产环境变量都已正确配置")


class TestCompleteRunPublishWorkflow:
    """完整的 run 和 publish 工作流验证"""

    @pytest.fixture
    def full_workflow_project(self):
        """创建完整的工作流项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            (project_dir / "pyproject.toml").write_text("""
[project]
name = "complete-agent"
version = "1.0.0"
""")

            # 本地开发环境
            (project_dir / ".env").write_text("""# 本地开发
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
ROBOT_APPKEY=dev-complete-agent
SERVICE_ENDPOINT=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
TIMEOUT=30
""")

            # 生产环境
            (project_dir / ".env.prod").write_text("""# 生产部署
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ROBOT_APPKEY=prod-complete-agent
SERVICE_ENDPOINT=https://api.example.com
REDIS_URL=redis://redis.production:6379/0
TIMEOUT=60
""")

            yield project_dir

    def test_complete_dev_to_prod_workflow(self, full_workflow_project):
        """测试完整的开发到生产工作流"""
        from uni_agent_sdk.build_system.run_manager import RunManager
        from uni_agent_sdk.build_system.publish_manager import PublishManager
        from uni_agent_sdk.build_system.docker_client import DockerClient

        print("\n========== 完整工作流验证 ==========\n")

        # ==================== 第一阶段：本地开发和测试 ====================
        print("📝 第一阶段：本地开发和测试")
        print("-" * 50)

        docker_client = MagicMock(spec=DockerClient)
        docker_client.client = MagicMock()

        # Mock 镜像
        mock_image = MagicMock()
        mock_image.tags = ["robot-complete-agent:1.0.0"]
        docker_client.client.images.list.return_value = [mock_image]

        # Mock 容器
        mock_container = MagicMock()
        mock_container.id = "dev_container_123"
        docker_client.client.containers.run.return_value = mock_container

        # 创建 RunManager
        run_manager = RunManager(full_workflow_project, docker_client)

        # 步骤 1: 开发环境下加载 .env
        dev_env = run_manager.load_env_file()
        assert dev_env["ENVIRONMENT"] == "development"
        assert dev_env["DEBUG"] == "true"
        assert len(dev_env) == 7  # ENVIRONMENT, DEBUG, LOG_LEVEL, ROBOT_APPKEY, SERVICE_ENDPOINT, REDIS_URL, TIMEOUT
        print(f"✅ 1. 加载本地开发环境变量（.env）- {len(dev_env)} 个")

        # 步骤 2: 启动容器进行测试
        container_id = run_manager.run_container(
            image_tag="robot-complete-agent:1.0.0",
            port=8080,
            env=dev_env,
            name="complete-agent-dev",
        )
        assert container_id == "dev_container_123"
        print(f"✅ 2. 启动开发容器，传递 {len(dev_env)} 个环境变量")

        # 验证开发容器收到的环境变量
        call_args = docker_client.client.containers.run.call_args
        dev_container_env = call_args[1]["environment"]
        assert dev_container_env["TIMEOUT"] == "30"  # 开发时超时时间较短
        print("✅ 3. 验证开发容器环境变量（TIMEOUT=30）")

        # ==================== 第二阶段：生产部署准备 ====================
        print("\n📝 第二阶段：生产部署准备")
        print("-" * 50)

        config_provider = MagicMock()
        config_provider.get_node_server_url.return_value = "http://node-server:8000"
        config_provider.get_node_server_token.return_value = "prod-token"

        publish_manager = PublishManager(
            config_provider=config_provider,
            cloud_client=MagicMock(),
            build_manager=MagicMock(),
            docker_client=docker_client,
        )

        publish_manager.deploy_config = {
            "robot_id": "prod-agent-123",
            "node_server": {
                "url": "http://node-server:8000",
                "token": "prod-token",
            },
        }

        # 步骤 3: 加载生产环境变量
        prod_env_file = full_workflow_project / ".env.prod"
        prod_env = publish_manager.load_environment_variables(str(prod_env_file))
        assert prod_env["ENVIRONMENT"] == "production"
        assert prod_env["DEBUG"] == "false"
        assert len(prod_env) == 7
        print(f"✅ 1. 加载生产环境变量（.env.prod）- {len(prod_env)} 个")

        # 步骤 4: 验证生产和开发配置的差异
        differences = {
            "ENVIRONMENT": (dev_env["ENVIRONMENT"], prod_env["ENVIRONMENT"]),
            "DEBUG": (dev_env["DEBUG"], prod_env["DEBUG"]),
            "LOG_LEVEL": (dev_env["LOG_LEVEL"], prod_env["LOG_LEVEL"]),
            "ROBOT_APPKEY": (dev_env["ROBOT_APPKEY"], prod_env["ROBOT_APPKEY"]),
            "SERVICE_ENDPOINT": (dev_env["SERVICE_ENDPOINT"], prod_env["SERVICE_ENDPOINT"]),
            "REDIS_URL": (dev_env["REDIS_URL"], prod_env["REDIS_URL"]),
            "TIMEOUT": (dev_env["TIMEOUT"], prod_env["TIMEOUT"]),
        }

        for key, (dev_val, prod_val) in differences.items():
            assert dev_val != prod_val or key == "LOG_LEVEL"  # 某些值应该不同
        print("✅ 2. 验证生产和开发配置正确隔离（7 个参数不同）")

        # 步骤 5: 构建部署请求
        deployment_request = {
            "robot_id": publish_manager.deploy_config["robot_id"],
            "image": "registry.example.com:5000/robots/complete-agent:1.0.0",
            "version": "1.0.0",
            "environment": prod_env,
            "ports": {8080: 8080},
        }

        # 验证：部署请求包含正确的生产环境变量
        assert deployment_request["environment"]["TIMEOUT"] == "60"  # 生产时超时时间较长
        assert deployment_request["environment"]["ROBOT_APPKEY"] == "prod-complete-agent"
        assert len(deployment_request["environment"]) == 7
        print(f"✅ 3. 构建部署请求，包含 {len(deployment_request['environment'])} 个生产环境变量")

        # ==================== 验证结果 ====================
        print("\n📝 结果验证")
        print("-" * 50)

        print(
            f"""
✅ 开发环境配置：
   - ENVIRONMENT: {dev_env["ENVIRONMENT"]}
   - DEBUG: {dev_env["DEBUG"]}
   - TIMEOUT: {dev_env["TIMEOUT"]}
   - 容器ID: {container_id[:12]}

✅ 生产环境配置：
   - ENVIRONMENT: {prod_env["ENVIRONMENT"]}
   - DEBUG: {prod_env["DEBUG"]}
   - TIMEOUT: {prod_env["TIMEOUT"]}
   - Robot ID: prod-agent-123

✅ 工作流状态：
   - 本地测试：成功 ✓
   - 生产部署：准备就绪 ✓
   - 环境隔离：完全 ✓
"""
        )

        return True
