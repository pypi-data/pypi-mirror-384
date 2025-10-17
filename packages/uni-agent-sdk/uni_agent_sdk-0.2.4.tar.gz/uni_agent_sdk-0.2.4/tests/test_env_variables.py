"""
环境变量加载功能的单元测试

测试场景：
1. 从 .env 文件加载环境变量
2. 处理缺失的文件
3. 处理格式错误的行
4. 处理注释和空行
5. 支持引号值
"""

import tempfile
from pathlib import Path

import pytest

from uni_agent_sdk.build_system.run_manager import RunManager
from uni_agent_sdk.build_system.publish_manager import PublishManager


class TestEnvFileLoading:
    """环境变量文件加载测试（直接测试）"""

    def test_parse_env_file_success(self):
        """测试成功解析 .env 文件"""
        # 直接测试解析逻辑（无需 RunManager）
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """# 本地开发配置
DEBUG=true
LOG_LEVEL=DEBUG
API_KEY=test-key-12345
DATABASE_URL=postgres://localhost:5432/test
"""
            )

            # 手动解析
            env_vars = {}
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    env_vars[key] = value

            # 验证结果
            assert len(env_vars) == 4
            assert env_vars["DEBUG"] == "true"
            assert env_vars["LOG_LEVEL"] == "DEBUG"
            assert env_vars["API_KEY"] == "test-key-12345"
            assert env_vars["DATABASE_URL"] == "postgres://localhost:5432/test"

    def test_parse_env_file_with_quotes(self):
        """测试加载带有引号的值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """VALUE1="value with spaces"
VALUE2='single quoted'
VALUE3=no-quotes
"""
            )

            env_vars = {}
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    env_vars[key] = value

            assert env_vars["VALUE1"] == "value with spaces"
            assert env_vars["VALUE2"] == "single quoted"
            assert env_vars["VALUE3"] == "no-quotes"

    def test_parse_env_file_with_equals_in_value(self):
        """测试值中包含等号的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("DATABASE_URL=postgres://user:pass@localhost:5432/db?sslmode=require\n")

            env_vars = {}
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    env_vars[key] = value

            assert env_vars["DATABASE_URL"] == "postgres://user:pass@localhost:5432/db?sslmode=require"

    def test_parse_env_file_ignores_comments_and_empty_lines(self):
        """测试忽略注释和空行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """# 这是注释
KEY1=value1

# 另一个注释
KEY2=value2


KEY3=value3
"""
            )

            env_vars = {}
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    env_vars[key] = value

            assert len(env_vars) == 3
            assert "KEY1" in env_vars
            assert "KEY2" in env_vars
            assert "KEY3" in env_vars

    def test_parse_env_file_ignores_invalid_lines(self):
        """测试忽略格式错误的行"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                """KEY1=value1
INVALID_LINE_WITHOUT_EQUALS
KEY2=value2
"""
            )

            env_vars = {}
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    env_vars[key] = value

            # 应该跳过没有等号的行
            assert len(env_vars) == 2
            assert env_vars["KEY1"] == "value1"
            assert env_vars["KEY2"] == "value2"


class TestPublishManagerEnvLoading:
    """PublishManager 环境变量加载测试"""

    @pytest.fixture
    def temp_project_dir(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_environment_variables_success(self, temp_project_dir):
        """测试成功加载环境变量"""
        # 创建 .env 文件
        env_file = temp_project_dir / ".env"
        env_file.write_text(
            """ROBOT_APPKEY=test-robot
DEBUG=true
LOG_LEVEL=DEBUG
"""
        )

        # 创建 PublishManager（使用 Mock）
        from unittest.mock import MagicMock

        publish_manager = PublishManager(
            config_provider=MagicMock(),
            cloud_client=MagicMock(),
            build_manager=MagicMock(),
            docker_client=MagicMock(),
        )

        env_vars = publish_manager.load_environment_variables(str(env_file))

        assert len(env_vars) == 3
        assert env_vars["ROBOT_APPKEY"] == "test-robot"
        assert env_vars["DEBUG"] == "true"

    def test_load_environment_variables_production(self, temp_project_dir):
        """测试加载生产环境配置"""
        # 创建 .env.prod 文件
        env_file = temp_project_dir / ".env.prod"
        env_file.write_text(
            """ROBOT_APPKEY=prod-robot-main
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgres://prod-db.example.com:5432/prod
API_KEY=prod-key-abcde12345xyz
"""
        )

        from unittest.mock import MagicMock

        publish_manager = PublishManager(
            config_provider=MagicMock(),
            cloud_client=MagicMock(),
            build_manager=MagicMock(),
            docker_client=MagicMock(),
        )

        env_vars = publish_manager.load_environment_variables(str(env_file))

        assert len(env_vars) == 5
        assert env_vars["ROBOT_APPKEY"] == "prod-robot-main"
        assert env_vars["DEBUG"] == "false"
        assert env_vars["LOG_LEVEL"] == "INFO"
        assert "DATABASE_URL" in env_vars
        assert "API_KEY" in env_vars

    def test_load_environment_variables_missing(self, temp_project_dir):
        """测试文件不存在的情况"""
        from unittest.mock import MagicMock

        publish_manager = PublishManager(
            config_provider=MagicMock(),
            cloud_client=MagicMock(),
            build_manager=MagicMock(),
            docker_client=MagicMock(),
        )

        env_vars = publish_manager.load_environment_variables(
            str(temp_project_dir / ".env.missing")
        )

        assert env_vars == {}

    def test_load_environment_variables_with_default(self, temp_project_dir):
        """测试使用默认 .env 文件"""
        env_file = temp_project_dir / ".env"
        env_file.write_text("KEY1=value1\n")

        from unittest.mock import MagicMock

        # 改变当前工作目录
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)
            publish_manager = PublishManager(
                config_provider=MagicMock(),
                cloud_client=MagicMock(),
                build_manager=MagicMock(),
                docker_client=MagicMock(),
            )

            # 不指定文件路径，使用默认 .env
            env_vars = publish_manager.load_environment_variables()

            assert "KEY1" in env_vars
            assert env_vars["KEY1"] == "value1"
        finally:
            os.chdir(old_cwd)
