"""
BuildManager 构建管理器测试

测试镜像构建的完整流程：
- 读取 pyproject.toml
- 版本确定逻辑
- Dockerfile 生成
- 镜像构建
- 镜像信息获取
"""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from uni_agent_sdk.build_system.build_manager import BuildManager, BuildManagerError
from uni_agent_sdk.build_system.docker_client import DockerClient, DockerError


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """创建临时项目目录"""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # 创建 pyproject.toml
    pyproject_content = """
[project]
name = "test-agent"
version = "1.2.3"
description = "Test agent"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # 创建 requirements.txt
    (project_dir / "requirements.txt").write_text("", encoding="utf-8")

    return project_dir


@pytest.fixture
def mock_docker_client() -> DockerClient:
    """创建 mock 的 DockerClient"""
    client = Mock(spec=DockerClient)
    client.build = Mock(return_value="abc123456789")
    client.inspect_image = Mock(
        return_value={
            "id": "abc123456789",
            "size": "104857600",
            "size_mb": "100.0",
            "created": "2024-01-01T00:00:00Z",
        }
    )
    return client


@pytest.fixture
def build_manager(
    temp_project_dir: Path, mock_docker_client: DockerClient
) -> BuildManager:
    """创建 BuildManager 实例"""
    return BuildManager(temp_project_dir, mock_docker_client)


# ============ 测试读取项目配置 ============


def test_read_project_config_success(build_manager: BuildManager) -> None:
    """测试成功读取 pyproject.toml"""
    config = build_manager.project_config

    assert config["name"] == "test-agent"
    assert config["version"] == "1.2.3"
    assert config["package_name"] == "test_agent"


def test_read_project_config_missing_file() -> None:
    """测试 pyproject.toml 不存在时报错"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        mock_client = Mock(spec=DockerClient)

        with pytest.raises(BuildManagerError) as exc_info:
            BuildManager(project_dir, mock_client)

        assert "pyproject.toml 不存在" in str(exc_info.value)


def test_read_project_config_missing_name(tmp_path: Path) -> None:
    """测试 pyproject.toml 缺少 name 字段时报错"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # 创建缺少 name 的 pyproject.toml
    pyproject_content = """
[project]
version = "1.0.0"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    mock_client = Mock(spec=DockerClient)

    with pytest.raises(BuildManagerError) as exc_info:
        BuildManager(project_dir, mock_client)

    assert "缺少 [project] name 字段" in str(exc_info.value)


def test_read_project_config_no_version(
    tmp_path: Path, mock_docker_client: DockerClient
) -> None:
    """测试 pyproject.toml 缺少 version 字段时使用空字符串"""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pyproject_content = """
[project]
name = "no-version-agent"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    manager = BuildManager(project_dir, mock_docker_client)

    assert manager.project_config["name"] == "no-version-agent"
    assert manager.project_config["version"] == ""
    assert manager.project_config["package_name"] == "no_version_agent"


# ============ 测试版本确定逻辑 ============


def test_determine_version_cli_priority(build_manager: BuildManager) -> None:
    """测试 CLI 参数优先级最高"""
    version = build_manager._determine_version("2.0.0-beta")

    assert version == "2.0.0-beta"


def test_determine_version_pyproject(build_manager: BuildManager) -> None:
    """测试使用 pyproject.toml 中的版本"""
    version = build_manager._determine_version(None)

    assert version == "1.2.3"


def test_determine_version_git_hash(
    tmp_path: Path, mock_docker_client: DockerClient
) -> None:
    """测试使用 git hash（当 pyproject.toml 无版本时）"""
    project_dir = tmp_path / "git-project"
    project_dir.mkdir()

    # 创建无版本的 pyproject.toml
    pyproject_content = """
[project]
name = "git-agent"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # 初始化 git 仓库
    subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Initial commit"],
        cwd=project_dir,
        capture_output=True,
    )

    manager = BuildManager(project_dir, mock_docker_client)
    version = manager._determine_version(None)

    # 应该是一个 7 位的 git hash
    assert len(version) == 7
    assert all(c in "0123456789abcdef" for c in version)


def test_determine_version_timestamp_fallback(
    tmp_path: Path, mock_docker_client: DockerClient
) -> None:
    """测试使用时间戳作为兜底方案"""
    project_dir = tmp_path / "timestamp-project"
    project_dir.mkdir()

    # 创建无版本的 pyproject.toml（且不在 git 仓库）
    pyproject_content = """
[project]
name = "timestamp-agent"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    manager = BuildManager(project_dir, mock_docker_client)
    version = manager._determine_version(None)

    # 应该是时间戳格式：YYYY-MM-DD-HHmmss
    try:
        datetime.strptime(version, "%Y-%m-%d-%H%M%S")
        timestamp_valid = True
    except ValueError:
        timestamp_valid = False

    assert timestamp_valid, f"版本号 '{version}' 不是有效的时间戳格式"


def test_get_git_hash_not_git_repo(build_manager: BuildManager) -> None:
    """测试非 git 仓库返回 None"""
    git_hash = build_manager._get_git_hash()

    assert git_hash is None


def test_get_git_hash_success(tmp_path: Path, mock_docker_client: DockerClient) -> None:
    """测试成功获取 git hash"""
    project_dir = tmp_path / "git-repo"
    project_dir.mkdir()

    pyproject_content = """
[project]
name = "git-test"
version = "1.0.0"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # 初始化 git 仓库
    subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "Test"],
        cwd=project_dir,
        capture_output=True,
    )

    manager = BuildManager(project_dir, mock_docker_client)
    git_hash = manager._get_git_hash()

    assert git_hash is not None
    assert len(git_hash) == 7


# ============ 测试镜像构建 ============


def test_build_image_success(
    build_manager: BuildManager,
    mock_docker_client: DockerClient,
    capsys: pytest.CaptureFixture,
) -> None:
    """测试成功构建镜像"""
    # 先创建 Dockerfile
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    dockerfile_path.write_text(
        'FROM python:3.11-slim\nCMD ["python", "-m", "test_agent.main"]',
        encoding="utf-8",
    )

    tag = build_manager.build_image()

    # 验证返回的标签格式
    assert tag == "robot-test-agent:1.2.3"

    # 验证调用了 docker client
    mock_docker_client.build.assert_called_once()
    call_args = mock_docker_client.build.call_args

    assert call_args.kwargs["tag"] == "robot-test-agent:1.2.3"
    assert call_args.kwargs["context_dir"] == build_manager.project_dir
    assert call_args.kwargs["no_cache"] is False

    # 验证输出信息
    captured = capsys.readouterr()
    assert "项目名称: test-agent" in captured.out
    assert "项目版本: 1.2.3" in captured.out
    assert "镜像构建成功" in captured.out
    assert "镜像标签: robot-test-agent:1.2.3" in captured.out
    assert "镜像大小: 100.0 MB" in captured.out


def test_build_image_with_custom_version(
    build_manager: BuildManager, mock_docker_client: DockerClient
) -> None:
    """测试使用自定义版本号构建"""
    # 创建 Dockerfile
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.11-slim", encoding="utf-8")

    tag = build_manager.build_image(version="3.0.0-dev")

    assert tag == "robot-test-agent:3.0.0-dev"

    call_args = mock_docker_client.build.call_args
    assert call_args.kwargs["tag"] == "robot-test-agent:3.0.0-dev"


def test_build_image_with_rebuild(
    build_manager: BuildManager, mock_docker_client: DockerClient
) -> None:
    """测试强制重建镜像（--no-cache）"""
    # 创建 Dockerfile
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.11-slim", encoding="utf-8")

    build_manager.build_image(rebuild=True)

    call_args = mock_docker_client.build.call_args
    assert call_args.kwargs["no_cache"] is True


def test_build_image_auto_generate_dockerfile(
    build_manager: BuildManager,
    mock_docker_client: DockerClient,
    capsys: pytest.CaptureFixture,
) -> None:
    """测试自动生成 Dockerfile"""
    # 确保 Dockerfile 不存在
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    assert not dockerfile_path.exists()

    build_manager.build_image()

    # 验证 Dockerfile 被生成
    assert dockerfile_path.exists()
    content = dockerfile_path.read_text(encoding="utf-8")
    assert "test_agent" in content

    # 验证输出提示
    captured = capsys.readouterr()
    assert "Dockerfile 不存在，正在生成" in captured.out
    assert "Dockerfile 已生成" in captured.out


def test_build_image_docker_error(
    build_manager: BuildManager, mock_docker_client: DockerClient
) -> None:
    """测试 Docker 构建失败时抛出异常"""
    # 创建 Dockerfile
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    dockerfile_path.write_text("FROM python:3.11-slim", encoding="utf-8")

    # Mock 构建失败
    mock_docker_client.build.side_effect = DockerError("构建失败")

    with pytest.raises(BuildManagerError) as exc_info:
        build_manager.build_image()

    assert "镜像构建失败" in str(exc_info.value)


# ============ 测试获取镜像信息 ============


def test_get_image_info_success(
    build_manager: BuildManager, mock_docker_client: DockerClient
) -> None:
    """测试成功获取镜像信息"""
    info = build_manager.get_image_info("robot-test-agent:1.2.3")

    assert info["id"] == "abc123456789"
    assert info["size"] == "104857600"
    assert info["size_mb"] == "100.0"
    assert info["created"] == "2024-01-01T00:00:00Z"

    mock_docker_client.inspect_image.assert_called_once_with("robot-test-agent:1.2.3")


def test_get_image_info_not_found(
    build_manager: BuildManager, mock_docker_client: DockerClient
) -> None:
    """测试镜像不存在时抛出异常"""
    mock_docker_client.inspect_image.side_effect = DockerError("镜像不存在")

    with pytest.raises(DockerError):
        build_manager.get_image_info("non-existent:1.0.0")


# ============ 测试 Dockerfile 管理 ============


def test_ensure_dockerfile_exists(build_manager: BuildManager) -> None:
    """测试已存在的 Dockerfile 不会被覆盖"""
    # 创建自定义 Dockerfile
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    custom_content = "FROM ubuntu:22.04\nRUN echo 'custom'"
    dockerfile_path.write_text(custom_content, encoding="utf-8")

    result_path = build_manager._ensure_dockerfile()

    # 验证返回的路径正确
    assert result_path == dockerfile_path

    # 验证内容未被修改
    assert dockerfile_path.read_text(encoding="utf-8") == custom_content


def test_ensure_dockerfile_generates_new(build_manager: BuildManager) -> None:
    """测试自动生成新的 Dockerfile"""
    dockerfile_path = build_manager.project_dir / "Dockerfile"
    assert not dockerfile_path.exists()

    result_path = build_manager._ensure_dockerfile()

    assert result_path == dockerfile_path
    assert dockerfile_path.exists()

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "test_agent" in content
    assert "python:3.11-slim" in content


# ============ 集成测试 ============


def test_full_build_workflow(tmp_path: Path, mock_docker_client: DockerClient) -> None:
    """测试完整的构建工作流"""
    # 创建项目目录
    project_dir = tmp_path / "full-test"
    project_dir.mkdir()

    pyproject_content = """
[project]
name = "workflow-agent"
version = "2.0.0"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
    (project_dir / "requirements.txt").write_text("", encoding="utf-8")

    # 初始化构建管理器
    manager = BuildManager(project_dir, mock_docker_client)

    # 执行构建
    tag = manager.build_image()

    # 验证结果
    assert tag == "robot-workflow-agent:2.0.0"
    assert (project_dir / "Dockerfile").exists()

    # 验证获取镜像信息
    info = manager.get_image_info(tag)
    assert info["id"] == "abc123456789"


def test_build_with_package_name_conversion(
    tmp_path: Path, mock_docker_client: DockerClient
) -> None:
    """测试包名转换（连字符转下划线）"""
    project_dir = tmp_path / "conversion-test"
    project_dir.mkdir()

    pyproject_content = """
[project]
name = "my-awesome-agent"
version = "1.0.0"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")
    (project_dir / "requirements.txt").write_text("", encoding="utf-8")

    manager = BuildManager(project_dir, mock_docker_client)

    assert manager.project_config["package_name"] == "my_awesome_agent"

    # 构建并验证 Dockerfile
    manager.build_image()

    dockerfile_content = (project_dir / "Dockerfile").read_text(encoding="utf-8")
    assert "my_awesome_agent" in dockerfile_content
