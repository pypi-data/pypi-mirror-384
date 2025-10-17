"""
PublishManager 发布管理器测试

测试镜像发布的完整流程：
- 准备发布操作
- 推送镜像到 OSS
- 更新机器人信息到云函数
- 发布后验证
- 完整发布流程
- 回滚发布操作
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from uni_agent_sdk.build_system.build_manager import BuildManager
from uni_agent_sdk.build_system.cloud_function_client import (
    CloudFunctionClient,
    CloudFunctionError,
)
from uni_agent_sdk.build_system.config_provider import ConfigProvider
from uni_agent_sdk.build_system.docker_client import DockerClient, DockerError
from uni_agent_sdk.build_system.publish_manager import (
    PublishManager,
    PublishManagerError,
)


@pytest.fixture
def mock_config_provider() -> ConfigProvider:
    """创建 mock 的 ConfigProvider"""
    config = Mock(spec=ConfigProvider)
    config.get_robot_appkey = Mock(return_value="test-appkey-123")
    config.get_registry_url = Mock(return_value="registry.example.com:5000")
    config.get_registry_username = Mock(return_value="admin")
    config.get_registry_password = Mock(return_value="password123")
    config.get_node_server_url = Mock(return_value="http://localhost:8000")
    config.get_node_server_token = Mock(return_value="test-token")
    config.update_from_cloud = Mock()
    config.validate_publish_config = Mock()
    return config


@pytest.fixture
def mock_cloud_client() -> CloudFunctionClient:
    """创建 mock 的 CloudFunctionClient"""
    client = Mock(spec=CloudFunctionClient)
    client.get_deploy_config = AsyncMock(
        return_value={
            "robot_id": "robot-test-123",
            "registry": {
                "url": "registry.example.com:5000",
                "username": "admin",
                "password": "password123",
                "namespace": "robots",
            },
            "node_server": {
                "url": "http://localhost:8000",
                "token": "test-token",
            },
            "config": {
                "max_retries": 3,
                "retry_delay_seconds": 5,
            },
        }
    )
    return client


@pytest.fixture
def mock_build_manager(tmp_path: Path) -> BuildManager:
    """创建 mock 的 BuildManager"""
    manager = Mock(spec=BuildManager)
    manager.project_config = {
        "name": "test-agent",
        "version": "1.0.0",
        "package_name": "test_agent",
    }
    manager.project_dir = tmp_path / "test-project"
    manager.project_dir.mkdir(exist_ok=True)
    manager.build_image = Mock(return_value="robot-test-agent:1.0.0")
    return manager


@pytest.fixture
def mock_docker_client() -> DockerClient:
    """创建 mock 的 DockerClient"""
    client = Mock(spec=DockerClient)
    client.login = Mock(return_value=True)
    client.tag_image = Mock(return_value=True)
    client.push = Mock(return_value=True)
    return client


@pytest.fixture
def publish_manager(
    mock_config_provider: ConfigProvider,
    mock_cloud_client: CloudFunctionClient,
    mock_build_manager: BuildManager,
    mock_docker_client: DockerClient,
) -> PublishManager:
    """创建 PublishManager 实例"""
    return PublishManager(
        mock_config_provider,
        mock_cloud_client,
        mock_build_manager,
        mock_docker_client,
    )


# ============ 测试准备发布操作 ============


@pytest.mark.asyncio
async def test_prepare_publish_success(
    publish_manager: PublishManager,
    mock_config_provider: ConfigProvider,
    mock_cloud_client: CloudFunctionClient,
) -> None:
    """测试成功准备发布操作"""
    await publish_manager.prepare_publish()

    # 验证调用了云函数客户端
    mock_cloud_client.get_deploy_config.assert_called_once_with("test-appkey-123")

    # 验证更新了配置
    mock_config_provider.update_from_cloud.assert_called_once()

    # 验证验证了配置
    mock_config_provider.validate_publish_config.assert_called_once()

    # 验证保存了配置
    assert publish_manager.deploy_config is not None
    assert publish_manager.deploy_config["robot_id"] == "robot-test-123"


@pytest.mark.asyncio
async def test_prepare_publish_cloud_error(
    publish_manager: PublishManager,
    mock_cloud_client: CloudFunctionClient,
) -> None:
    """测试云函数调用失败时抛出异常"""
    mock_cloud_client.get_deploy_config.side_effect = CloudFunctionError("网络错误")

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.prepare_publish()

    assert "获取部署配置失败" in str(exc_info.value)


@pytest.mark.asyncio
async def test_prepare_publish_validation_error(
    publish_manager: PublishManager,
    mock_config_provider: ConfigProvider,
) -> None:
    """测试配置验证失败时抛出异常"""
    mock_config_provider.validate_publish_config.side_effect = ValueError("缺少配置")

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.prepare_publish()

    assert "配置验证失败" in str(exc_info.value)


# ============ 测试推送镜像到 OSS ============


@pytest.mark.asyncio
async def test_push_to_oss_success(
    publish_manager: PublishManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试成功推送镜像到 OSS"""
    # 设置部署配置
    publish_manager.deploy_config = {
        "robot_id": "robot-test-123",
        "registry": {
            "namespace": "robots",
        },
    }

    result = await publish_manager.push_to_oss("robot-test-agent:1.0.0")

    # 验证返回值
    assert result["versioned"] == "registry.example.com:5000/robots/test-agent:1.0.0"
    assert result["latest"] == "registry.example.com:5000/robots/test-agent:latest"

    # 验证调用了 docker login
    mock_docker_client.login.assert_called_once_with(
        "registry.example.com:5000", "admin", "password123"
    )

    # 验证打标签（2次：versioned 和 latest）
    assert mock_docker_client.tag_image.call_count == 2
    mock_docker_client.tag_image.assert_any_call(
        "robot-test-agent:1.0.0",
        "registry.example.com:5000/robots/test-agent:1.0.0",
    )
    mock_docker_client.tag_image.assert_any_call(
        "robot-test-agent:1.0.0",
        "registry.example.com:5000/robots/test-agent:latest",
    )

    # 验证推送镜像（2次：versioned 和 latest）
    assert mock_docker_client.push.call_count == 2


@pytest.mark.asyncio
async def test_push_to_oss_invalid_tag(publish_manager: PublishManager) -> None:
    """测试无效的镜像标签格式"""
    publish_manager.deploy_config = {"registry": {"namespace": "robots"}}

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.push_to_oss("invalid-tag-without-version")

    assert "无效的镜像标签格式" in str(exc_info.value)


@pytest.mark.asyncio
async def test_push_to_oss_missing_config(
    publish_manager: PublishManager,
    mock_config_provider: ConfigProvider,
) -> None:
    """测试 registry 配置不完整时抛出异常"""
    mock_config_provider.get_registry_url.return_value = None

    publish_manager.deploy_config = {"registry": {"namespace": "robots"}}

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.push_to_oss("robot-test-agent:1.0.0")

    assert "Registry 配置不完整" in str(exc_info.value)


@pytest.mark.asyncio
async def test_push_to_oss_docker_login_error(
    publish_manager: PublishManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试 Docker 登录失败时抛出异常"""
    publish_manager.deploy_config = {"registry": {"namespace": "robots"}}

    mock_docker_client.login.side_effect = DockerError("登录失败")

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.push_to_oss("robot-test-agent:1.0.0")

    assert "Docker 操作失败" in str(exc_info.value)


@pytest.mark.asyncio
async def test_push_to_oss_default_namespace(
    publish_manager: PublishManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试使用默认 namespace"""
    # 不设置 namespace
    publish_manager.deploy_config = {"registry": {}}

    result = await publish_manager.push_to_oss("robot-test-agent:1.0.0")

    # 应该使用默认的 "robots" namespace
    assert "robots" in result["versioned"]


# ============ 测试更新机器人信息 ============


@pytest.mark.asyncio
async def test_update_robot_info_success(
    publish_manager: PublishManager,
) -> None:
    """测试成功更新机器人信息"""
    publish_manager.deploy_config = {
        "robot_id": "robot-test-123",
        "registry": {"namespace": "robots"},
    }

    # Mock httpx response
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 0,
        "message": "success",
        "data": {
            "task_id": "deploy-abc123",
            "robot_id": "robot-test-123",
            "status": "deploying",
            "status_url": "/api/deployment/deploy-abc123/status",
        },
    }
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await publish_manager.update_robot_info(
            "registry.example.com:5000/robots/test-agent:1.0.0",
            "registry.example.com:5000/robots/test-agent:latest",
        )

        # 验证返回值
        assert result["task_id"] == "deploy-abc123"
        assert result["robot_id"] == "robot-test-123"
        assert result["status"] == "deploying"

        # 验证调用了正确的 URL
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:8000/api/robots/deploy"

        # 验证请求体
        payload = call_args[1]["json"]
        assert payload["robot_id"] == "robot-test-123"
        assert payload["image"] == "registry.example.com:5000/robots/test-agent:1.0.0"
        assert payload["version"] == "1.0.0"

        # 验证请求头
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-token"


@pytest.mark.asyncio
async def test_update_robot_info_no_deploy_config(
    publish_manager: PublishManager,
) -> None:
    """测试未初始化部署配置时抛出异常"""
    publish_manager.deploy_config = None

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.update_robot_info("image:1.0.0", "image:latest")

    assert "部署配置未初始化" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_robot_info_missing_url(
    publish_manager: PublishManager,
    mock_config_provider: ConfigProvider,
) -> None:
    """测试 Node Server URL 未配置时抛出异常"""
    publish_manager.deploy_config = {"robot_id": "robot-test-123"}

    mock_config_provider.get_node_server_url.return_value = None

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.update_robot_info("image:1.0.0", "image:latest")

    assert "Node Server URL 未配置" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_robot_info_server_error(
    publish_manager: PublishManager,
) -> None:
    """测试 Node Server 返回错误时抛出异常"""
    publish_manager.deploy_config = {
        "robot_id": "robot-test-123",
        "registry": {"namespace": "robots"},
    }

    # Mock 错误响应
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 400,
        "message": "Invalid request",
    }
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(PublishManagerError) as exc_info:
            await publish_manager.update_robot_info("image:1.0.0", "image:latest")

        assert "Node Server 返回错误" in str(exc_info.value)


# ============ 测试发布后验证 ============


@pytest.mark.asyncio
async def test_verify_publish_success(publish_manager: PublishManager) -> None:
    """测试成功验证发布"""
    deployment_info = {
        "task_id": "deploy-abc123",
        "status": "deploying",
    }

    # Mock httpx response
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "task_id": "deploy-abc123",
            "status": "deploying",
            "progress": 50,
        },
    }
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        # 应该不抛出异常
        await publish_manager.verify_publish(deployment_info)

        # 验证调用了正确的 URL
        call_args = mock_client.get.call_args
        assert "deploy-abc123" in call_args[0][0]


@pytest.mark.asyncio
async def test_verify_publish_no_task_id(
    publish_manager: PublishManager,
    capsys: pytest.CaptureFixture,
) -> None:
    """测试没有 task_id 时跳过验证"""
    deployment_info = {}

    await publish_manager.verify_publish(deployment_info)

    captured = capsys.readouterr()
    assert "跳过验证" in captured.out


@pytest.mark.asyncio
async def test_verify_publish_network_error(
    publish_manager: PublishManager,
    capsys: pytest.CaptureFixture,
) -> None:
    """测试网络错误时只警告不抛出异常"""
    deployment_info = {"task_id": "deploy-abc123"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.side_effect = httpx.ConnectError("连接失败")
        mock_client_class.return_value = mock_client

        # 应该不抛出异常
        await publish_manager.verify_publish(deployment_info)

        captured = capsys.readouterr()
        assert "警告" in captured.out


# ============ 测试完整发布流程 ============


@pytest.mark.asyncio
async def test_publish_full_workflow(
    publish_manager: PublishManager,
    mock_build_manager: BuildManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试完整的发布工作流"""
    # Mock httpx responses
    mock_post_response = Mock()
    mock_post_response.json.return_value = {
        "code": 0,
        "data": {
            "task_id": "deploy-abc123",
            "robot_id": "robot-test-123",
            "status": "deploying",
        },
    }
    mock_post_response.raise_for_status = Mock()

    mock_get_response = Mock()
    mock_get_response.json.return_value = {
        "code": 0,
        "data": {
            "task_id": "deploy-abc123",
            "status": "deploying",
            "progress": 50,
        },
    }
    mock_get_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_post_response
        mock_client.get.return_value = mock_get_response
        mock_client_class.return_value = mock_client

        result = await publish_manager.publish()

        # 验证返回值
        assert result["success"] is True
        assert "image_url" in result
        assert "robot_id" in result
        assert result["robot_id"] == "robot-test-123"

        # 验证调用了构建
        mock_build_manager.build_image.assert_called_once()

        # 验证调用了 docker 操作
        mock_docker_client.login.assert_called_once()
        assert mock_docker_client.tag_image.call_count == 2
        assert mock_docker_client.push.call_count == 2


@pytest.mark.asyncio
async def test_publish_skip_build(
    publish_manager: PublishManager,
    mock_build_manager: BuildManager,
) -> None:
    """测试跳过构建的发布流程"""
    # Mock httpx responses
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "task_id": "deploy-abc123",
            "robot_id": "robot-test-123",
            "status": "deploying",
        },
    }
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await publish_manager.publish(skip_build=True)

        # 验证没有调用构建
        mock_build_manager.build_image.assert_not_called()

        # 验证仍然返回成功
        assert result["success"] is True


@pytest.mark.asyncio
async def test_publish_build_error(
    publish_manager: PublishManager,
    mock_build_manager: BuildManager,
) -> None:
    """测试构建失败时抛出异常"""
    from uni_agent_sdk.build_system.build_manager import BuildManagerError

    mock_build_manager.build_image.side_effect = BuildManagerError("构建失败")

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.publish()

    assert "发布失败" in str(exc_info.value)


# ============ 测试回滚发布 ============


@pytest.mark.asyncio
async def test_rollback_publish_success(publish_manager: PublishManager) -> None:
    """测试成功回滚发布"""
    publish_manager.deploy_config = {
        "robot_id": "robot-test-123",
        "registry": {"namespace": "robots"},
    }

    # Mock httpx response
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "task_id": "rollback-abc123",
            "robot_id": "robot-test-123",
            "status": "deploying",
        },
    }
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await publish_manager.rollback_publish("robot-test-123", "0.9.0")

        # 验证返回值
        assert result["task_id"] == "rollback-abc123"

        # 验证调用了正确的版本
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["version"] == "0.9.0"
        assert "0.9.0" in payload["image"]


@pytest.mark.asyncio
async def test_rollback_publish_missing_config(
    publish_manager: PublishManager,
    mock_config_provider: ConfigProvider,
) -> None:
    """测试配置不完整时抛出异常"""
    publish_manager.deploy_config = {"robot_id": "robot-test-123"}

    mock_config_provider.get_node_server_url.return_value = None

    with pytest.raises(PublishManagerError) as exc_info:
        await publish_manager.rollback_publish("robot-test-123", "0.9.0")

    assert "配置不完整" in str(exc_info.value)


@pytest.mark.asyncio
async def test_rollback_publish_server_error(
    publish_manager: PublishManager,
) -> None:
    """测试服务器返回错误时抛出异常"""
    publish_manager.deploy_config = {
        "robot_id": "robot-test-123",
        "registry": {"namespace": "robots"},
    }

    # Mock 错误响应
    mock_response = Mock()
    mock_response.json.return_value = {
        "code": 500,
        "message": "Internal server error",
    }
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(PublishManagerError) as exc_info:
            await publish_manager.rollback_publish("robot-test-123", "0.9.0")

        assert "回滚失败" in str(exc_info.value)


# ============ 测试重试机制 ============


@pytest.mark.asyncio
async def test_push_with_retry_success_on_first_try(
    publish_manager: PublishManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试第一次尝试就成功"""
    await publish_manager._push_with_retry("test-image:1.0.0")

    # 只调用了一次
    mock_docker_client.push.assert_called_once()


@pytest.mark.asyncio
async def test_push_with_retry_success_after_retry(
    publish_manager: PublishManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试重试后成功"""
    # 第一次失败，第二次成功
    mock_docker_client.push.side_effect = [
        DockerError("临时错误"),
        True,
    ]

    await publish_manager._push_with_retry("test-image:1.0.0", max_retries=3)

    # 调用了两次
    assert mock_docker_client.push.call_count == 2


@pytest.mark.asyncio
async def test_push_with_retry_all_failed(
    publish_manager: PublishManager,
    mock_docker_client: DockerClient,
) -> None:
    """测试所有重试都失败"""
    mock_docker_client.push.side_effect = DockerError("持续错误")

    with pytest.raises(DockerError):
        await publish_manager._push_with_retry("test-image:1.0.0", max_retries=2)

    # 调用了 2 次（max_retries）
    assert mock_docker_client.push.call_count == 2


@pytest.mark.asyncio
async def test_notify_with_retry_success() -> None:
    """测试通知重试机制成功"""
    publish_manager = Mock()
    publish_manager._notify_with_retry = PublishManager._notify_with_retry.__get__(
        publish_manager
    )

    mock_response = Mock()
    mock_response.json.return_value = {"code": 0, "data": {}}
    mock_response.raise_for_status = Mock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = await publish_manager._notify_with_retry(
            "http://test.com/api",
            {"test": "data"},
            {"Authorization": "Bearer token"},
        )

        assert result["code"] == 0
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_notify_with_retry_http_error() -> None:
    """测试 HTTP 状态错误不重试"""
    publish_manager = Mock()
    publish_manager._notify_with_retry = PublishManager._notify_with_retry.__get__(
        publish_manager
    )

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=Mock(),
            response=Mock(status_code=400),
        )
        mock_client_class.return_value = mock_client

        with pytest.raises(httpx.HTTPStatusError):
            await publish_manager._notify_with_retry(
                "http://test.com/api",
                {"test": "data"},
                {"Authorization": "Bearer token"},
            )

        # 只调用了一次，不重试
        mock_client.post.assert_called_once()
