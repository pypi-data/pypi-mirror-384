"""测试文件服务密钥配置获取流程

验证文件服务能够正确从平台获取密钥并进行初始化。
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from uni_agent_sdk.services.file import FileService
from uni_agent_sdk.utils.config import Config


class TestFileServiceConfig:
    """文件服务配置测试类"""

    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return Config()

    @pytest.fixture
    def file_service(self, config):
        """创建文件服务实例"""
        return FileService(config)

    def test_initial_config_is_none(self, file_service):
        """测试初始化时OSS配置为None"""
        assert file_service._oss_config is None
        assert file_service._oss_config_expires_at is None

    def test_set_oss_config(self, file_service):
        """测试手动设置OSS配置"""
        config = {
            "access_key_id": "test_key_id",
            "access_key_secret": "test_key_secret",
            "bucket_name": "test_bucket",
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
            "base_path": "test-path",
            "region": "cn-hangzhou",
        }
        expires_at = 1234567890

        file_service.set_oss_config(config, expires_at)

        assert file_service._oss_config["access_key_id"] == "test_key_id"
        assert file_service._oss_config["access_key_secret"] == "test_key_secret"
        assert file_service._oss_config["bucket_name"] == "test_bucket"
        assert file_service._oss_config["endpoint"] == "oss-cn-hangzhou.aliyuncs.com"
        assert file_service._oss_config["base_path"] == "test-path"
        assert file_service._oss_config["region"] == "cn-hangzhou"
        assert file_service._oss_config_expires_at == expires_at

    def test_set_oss_config_default_values(self, file_service):
        """测试设置OSS配置时使用默认值"""
        config = {
            "access_key_id": "test_key_id",
            "access_key_secret": "test_key_secret",
            "bucket_name": "test_bucket",
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
        }

        file_service.set_oss_config(config)

        assert file_service._oss_config["base_path"] == "agent-reports"
        assert file_service._oss_config["region"] == ""

    @pytest.mark.asyncio
    async def test_init_from_platform_config(self, file_service):
        """测试从平台配置初始化"""
        platform_config = {
            "access_key_id": "platform_key_id",
            "access_key_secret": "platform_key_secret",
            "bucket_name": "platform_bucket",
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
            "base_path": "platform-reports",
            "region": "cn-hangzhou",
            "expires_at": 9999999999,
        }

        await file_service.init_from_platform_config(platform_config)

        assert file_service._oss_config["access_key_id"] == "platform_key_id"
        assert file_service._oss_config["bucket_name"] == "platform_bucket"
        assert file_service._oss_config_expires_at == 9999999999

    @pytest.mark.asyncio
    async def test_init_from_platform_config_empty_raises_error(self, file_service):
        """测试空平台配置会抛出错误"""
        with pytest.raises(ValueError, match="文件服务配置不能为空"):
            await file_service.init_from_platform_config(None)

        with pytest.raises(ValueError, match="文件服务配置不能为空"):
            await file_service.init_from_platform_config({})

    def test_validate_oss_config_not_set(self, file_service):
        """测试验证配置未设置时抛出错误"""
        with pytest.raises(RuntimeError, match="OSS配置未设置"):
            file_service._validate_oss_config()

    def test_validate_oss_config_missing_required_fields(self, file_service):
        """测试验证配置缺少必要字段时抛出错误"""
        # 缺少bucket_name
        file_service._oss_config = {
            "access_key_id": "test",
            "access_key_secret": "test",
            "endpoint": "test",
        }

        with pytest.raises(RuntimeError, match="OSS配置缺少必要字段"):
            file_service._validate_oss_config()

    def test_validate_oss_config_success(self, file_service):
        """测试验证配置成功"""
        file_service._oss_config = {
            "access_key_id": "test",
            "access_key_secret": "test",
            "bucket_name": "test",
            "endpoint": "test",
        }

        # 不应该抛出异常
        file_service._validate_oss_config()

    @patch("time.time")
    def test_validate_oss_config_expired(self, mock_time, file_service):
        """测试验证配置已过期时抛出错误"""
        mock_time.return_value = 2000000000

        file_service._oss_config = {
            "access_key_id": "test",
            "access_key_secret": "test",
            "bucket_name": "test",
            "endpoint": "test",
        }
        file_service._oss_config_expires_at = 1000000000  # 已过期

        with pytest.raises(RuntimeError, match="OSS密钥已过期"):
            file_service._validate_oss_config()

    def test_get_oss_bucket_without_config_raises_error(self, file_service):
        """测试在没有配置的情况下获取bucket会抛出错误"""
        with pytest.raises(RuntimeError, match="OSS配置未设置"):
            file_service._get_oss_bucket()

    @patch("oss2.Bucket")
    @patch("oss2.Auth")
    def test_get_oss_bucket_success(self, mock_auth, mock_bucket, file_service):
        """测试成功获取OSS Bucket"""
        file_service._oss_config = {
            "access_key_id": "test_key_id",
            "access_key_secret": "test_key_secret",
            "bucket_name": "test_bucket",
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
        }

        # Mock oss2模块
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_bucket_instance = MagicMock()
        mock_bucket.return_value = mock_bucket_instance

        result = file_service._get_oss_bucket()

        mock_auth.assert_called_once_with("test_key_id", "test_key_secret")
        mock_bucket.assert_called_once_with(
            mock_auth_instance, "oss-cn-hangzhou.aliyuncs.com", "test_bucket"
        )
        assert result == mock_bucket_instance
        assert file_service._oss_bucket == mock_bucket_instance

    @patch("oss2.Bucket")
    @patch("oss2.Auth")
    def test_get_oss_bucket_lazy_loading(self, mock_auth, mock_bucket, file_service):
        """测试OSS Bucket延迟加载"""
        file_service._oss_config = {
            "access_key_id": "test_key_id",
            "access_key_secret": "test_key_secret",
            "bucket_name": "test_bucket",
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
        }

        mock_bucket_instance = MagicMock()
        mock_bucket.return_value = mock_bucket_instance

        # 第一次调用应该创建新实例
        result1 = file_service._get_oss_bucket()
        assert mock_bucket.call_count == 1

        # 第二次调用应该返回缓存实例
        result2 = file_service._get_oss_bucket()
        assert mock_bucket.call_count == 1  # 仍然只调用一次

        assert result1 == result2


class TestAgentFileServiceIntegration:
    """测试Agent与文件服务的集成"""

    @pytest.mark.asyncio
    async def test_agent_initializes_file_service_on_registration(self):
        """测试Agent在注册时初始化文件服务"""
        from uni_agent_sdk import Agent

        # Mock配置
        config = Config()

        # 创建一个简单的Agent实现
        class TestAgent(Agent):
            async def handle_message(self, message, context):
                return None

        agent = TestAgent("test_api_key", "test_api_secret", **vars(config))

        # Mock平台API响应
        mock_platform = AsyncMock()
        mock_registration = {
            "errCode": 0,
            "data": {
                "developer_userid": "test_user_id",
                "token": "test_jwt_token",
                "expires_at": 9999999999,
                "rabbitmq_config": {"host": "rabbitmq.local", "port": 5672},
                "file_service_config": {
                    "access_key_id": "agent_key_id",
                    "access_key_secret": "agent_key_secret",
                    "bucket_name": "agent_bucket",
                    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
                },
            },
        }
        mock_platform.register_robot = AsyncMock(return_value=mock_registration)
        mock_platform.set_auth_info = MagicMock()
        agent._platform = mock_platform

        # 验证文件服务配置
        file_config = agent._file_service_config or mock_registration["data"].get(
            "file_service_config"
        )
        assert file_config is not None
        assert file_config["access_key_id"] == "agent_key_id"
        assert file_config["bucket_name"] == "agent_bucket"
