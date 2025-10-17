"""
DockerClient 单元测试
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from uni_agent_sdk.build_system.docker_client import DockerClient, DockerError


class TestDockerClient:
    """DockerClient 测试类"""

    @pytest.fixture
    def client(self) -> DockerClient:
        """创建测试用的 DockerClient 实例"""
        return DockerClient(verbose=False)

    @pytest.fixture
    def verbose_client(self) -> DockerClient:
        """创建 verbose 模式的 DockerClient 实例"""
        return DockerClient(verbose=True)

    def test_is_docker_available_success(self, client: DockerClient) -> None:
        """测试 Docker 可用性检查 - 成功场景"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = client.is_docker_available()

            assert result is True
            mock_run.assert_called_once_with(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )

    def test_is_docker_available_failure(self, client: DockerClient) -> None:
        """测试 Docker 可用性检查 - 失败场景"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)

            result = client.is_docker_available()

            assert result is False

    def test_is_docker_available_not_installed(self, client: DockerClient) -> None:
        """测试 Docker 未安装的场景"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            result = client.is_docker_available()

            assert result is False

    def test_is_docker_available_timeout(self, client: DockerClient) -> None:
        """测试 Docker 检查超时"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("docker", 5)

            result = client.is_docker_available()

            assert result is False

    def test_build_success(self, client: DockerClient) -> None:
        """测试镜像构建 - 成功场景"""
        dockerfile_path = Path("/test/Dockerfile")
        tag = "test-image:1.0.0"
        context_dir = Path("/test")

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = [
            "Step 1/5 : FROM python:3.11-slim\n",
            "Step 2/5 : WORKDIR /app\n",
            "Step 3/5 : COPY . .\n",
            "Step 4/5 : RUN pip install -r requirements.txt\n",
            "Step 5/5 : CMD python app.py\n",
            "Successfully built abc123def456\n",
        ]

        with patch("subprocess.Popen", return_value=mock_process), patch.object(
            client, "is_docker_available", return_value=True
        ):
            image_id = client.build(dockerfile_path, tag, context_dir)

            assert image_id == "abc123def456"

    def test_build_with_no_cache(self, client: DockerClient) -> None:
        """测试带 --no-cache 参数的构建"""
        dockerfile_path = Path("/test/Dockerfile")
        tag = "test-image:1.0.0"
        context_dir = Path("/test")

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ["Successfully built abc123def456\n"]

        with patch(
            "subprocess.Popen", return_value=mock_process
        ) as mock_popen, patch.object(client, "is_docker_available", return_value=True):
            client.build(dockerfile_path, tag, context_dir, no_cache=True)

            # 验证命令包含 --no-cache 参数
            called_cmd = mock_popen.call_args[0][0]
            assert "--no-cache" in called_cmd

    def test_build_docker_not_available(self, client: DockerClient) -> None:
        """测试 Docker daemon 未运行时的构建"""
        with patch.object(client, "is_docker_available", return_value=False):
            with pytest.raises(DockerError, match="Docker daemon 未运行"):
                client.build(Path("/test/Dockerfile"), "test:1.0", Path("/test"))

    def test_build_failure(self, client: DockerClient) -> None:
        """测试镜像构建失败"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ["Error: build failed\n"]

        with patch("subprocess.Popen", return_value=mock_process), patch.object(
            client, "is_docker_available", return_value=True
        ):
            with pytest.raises(DockerError, match="镜像构建失败"):
                client.build(Path("/test/Dockerfile"), "test:1.0", Path("/test"))

    def test_build_docker_not_installed(self, client: DockerClient) -> None:
        """测试 Docker 未安装时的构建"""
        with patch("subprocess.Popen") as mock_popen, patch.object(
            client, "is_docker_available", return_value=True
        ):
            mock_popen.side_effect = FileNotFoundError()

            with pytest.raises(DockerError, match="未找到 docker 命令"):
                client.build(Path("/test/Dockerfile"), "test:1.0", Path("/test"))

    def test_push_success(self, client: DockerClient) -> None:
        """测试镜像推送 - 成功场景"""
        tag = "registry.example.com/test-image:1.0.0"

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = [
            "The push refers to repository [registry.example.com/test-image]\n",
            "1.0.0: digest: sha256:abc123 size: 1234\n",
        ]

        with patch("subprocess.Popen", return_value=mock_process), patch.object(
            client, "is_docker_available", return_value=True
        ):
            result = client.push(tag)

            assert result is True

    def test_push_docker_not_available(self, client: DockerClient) -> None:
        """测试 Docker daemon 未运行时的推送"""
        with patch.object(client, "is_docker_available", return_value=False):
            with pytest.raises(DockerError, match="Docker daemon 未运行"):
                client.push("test:1.0")

    def test_push_failure(self, client: DockerClient) -> None:
        """测试镜像推送失败"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = ["Error: unauthorized\n"]

        with patch("subprocess.Popen", return_value=mock_process), patch.object(
            client, "is_docker_available", return_value=True
        ):
            with pytest.raises(DockerError, match="镜像推送失败"):
                client.push("registry.example.com/test:1.0")

    def test_login_success(self, client: DockerClient) -> None:
        """测试 registry 登录 - 成功场景"""
        registry_url = "registry.example.com"
        username = "testuser"
        password = "testpass"

        mock_result = Mock(returncode=0, stdout="Login Succeeded\n", stderr="")

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            result = client.login(registry_url, username, password)

            assert result is True

    def test_login_docker_not_available(self, client: DockerClient) -> None:
        """测试 Docker daemon 未运行时的登录"""
        with patch.object(client, "is_docker_available", return_value=False):
            with pytest.raises(DockerError, match="Docker daemon 未运行"):
                client.login("registry.example.com", "user", "pass")

    def test_login_failure(self, client: DockerClient) -> None:
        """测试 registry 登录失败"""
        mock_result = Mock(returncode=1, stdout="", stderr="Error: unauthorized")

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            with pytest.raises(DockerError, match="Registry 登录失败"):
                client.login("registry.example.com", "user", "wrongpass")

    def test_login_timeout(self, client: DockerClient) -> None:
        """测试 registry 登录超时"""
        with patch("subprocess.run") as mock_run, patch.object(
            client, "is_docker_available", return_value=True
        ):
            mock_run.side_effect = subprocess.TimeoutExpired("docker", 30)

            with pytest.raises(DockerError, match="登录超时"):
                client.login("registry.example.com", "user", "pass")

    def test_inspect_image_success(self, client: DockerClient) -> None:
        """测试获取镜像信息 - 成功场景"""
        tag = "test-image:1.0.0"
        image_data = {
            "Id": "sha256:abc123def456789012345678901234567890123456789012345678901234",
            "Size": 524288000,  # 500 MB
            "Created": "2025-10-16T10:00:00.000000000Z",
        }

        mock_result = Mock(
            returncode=0,
            stdout=json.dumps(image_data),
            stderr="",
        )

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            info = client.inspect_image(tag)

            assert info["id"] == "abc123def456"
            assert info["size"] == "524288000"
            assert info["size_mb"] == "500.0"
            assert info["created"] == "2025-10-16T10:00:00.000000000Z"

    def test_inspect_image_not_found(self, client: DockerClient) -> None:
        """测试获取不存在的镜像信息"""
        mock_result = Mock(
            returncode=1,
            stdout="",
            stderr="Error: No such image: nonexistent:1.0",
        )

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            with pytest.raises(DockerError, match="镜像不存在"):
                client.inspect_image("nonexistent:1.0")

    def test_inspect_image_docker_not_available(self, client: DockerClient) -> None:
        """测试 Docker daemon 未运行时获取镜像信息"""
        with patch.object(client, "is_docker_available", return_value=False):
            with pytest.raises(DockerError, match="Docker daemon 未运行"):
                client.inspect_image("test:1.0")

    def test_inspect_image_invalid_json(self, client: DockerClient) -> None:
        """测试解析无效的 JSON 输出"""
        mock_result = Mock(returncode=0, stdout="invalid json", stderr="")

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            with pytest.raises(DockerError, match="解析镜像信息失败"):
                client.inspect_image("test:1.0")

    def test_tag_image_success(self, client: DockerClient) -> None:
        """测试镜像打标签 - 成功场景"""
        source_tag = "test-image:1.0.0"
        target_tag = "registry.example.com/test-image:1.0.0"

        mock_result = Mock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            result = client.tag_image(source_tag, target_tag)

            assert result is True

    def test_tag_image_docker_not_available(self, client: DockerClient) -> None:
        """测试 Docker daemon 未运行时打标签"""
        with patch.object(client, "is_docker_available", return_value=False):
            with pytest.raises(DockerError, match="Docker daemon 未运行"):
                client.tag_image("source:1.0", "target:1.0")

    def test_tag_image_source_not_found(self, client: DockerClient) -> None:
        """测试源镜像不存在时打标签"""
        mock_result = Mock(
            returncode=1,
            stdout="",
            stderr="Error: No such image: nonexistent:1.0",
        )

        with patch("subprocess.run", return_value=mock_result), patch.object(
            client, "is_docker_available", return_value=True
        ):
            with pytest.raises(DockerError, match="源镜像不存在"):
                client.tag_image("nonexistent:1.0", "target:1.0")

    def test_tag_image_timeout(self, client: DockerClient) -> None:
        """测试打标签超时"""
        with patch("subprocess.run") as mock_run, patch.object(
            client, "is_docker_available", return_value=True
        ):
            mock_run.side_effect = subprocess.TimeoutExpired("docker", 10)

            with pytest.raises(DockerError, match="打标签超时"):
                client.tag_image("source:1.0", "target:1.0")

    def test_extract_image_id_from_successfully_built(
        self, client: DockerClient
    ) -> None:
        """测试从 'Successfully built' 输出中提取镜像 ID"""
        output = """
        Step 1/5 : FROM python:3.11-slim
        Step 2/5 : WORKDIR /app
        Successfully built abc123def456
        """

        image_id = client._extract_image_id(output)
        assert image_id == "abc123def456"

    def test_extract_image_id_from_sha256(self, client: DockerClient) -> None:
        """测试从 sha256 输出中提取镜像 ID"""
        output = """
        #8 writing image sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
        #8 naming to docker.io/library/test:latest
        """

        image_id = client._extract_image_id(output)
        assert image_id == "1234567890ab"

    def test_extract_image_id_failure(self, client: DockerClient) -> None:
        """测试无法提取镜像 ID 的场景"""
        output = "Build completed but no image ID found"

        with pytest.raises(DockerError, match="无法从构建输出中提取镜像 ID"):
            client._extract_image_id(output)

    def test_verbose_mode_output(
        self, verbose_client: DockerClient, capsys: pytest.CaptureFixture
    ) -> None:
        """测试 verbose 模式下的输出"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ["Successfully built abc123def456\n"]

        with patch("subprocess.Popen", return_value=mock_process), patch.object(
            verbose_client, "is_docker_available", return_value=True
        ):
            verbose_client.build(Path("/test/Dockerfile"), "test:1.0", Path("/test"))

            captured = capsys.readouterr()
            assert "正在构建镜像" in captured.out
            assert "镜像构建成功" in captured.out

    def test_command_generation_correctness(self, client: DockerClient) -> None:
        """测试命令生成的正确性"""
        dockerfile_path = Path("/path/to/Dockerfile")
        tag = "myimage:1.0.0"
        context_dir = Path("/path/to/context")

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ["Successfully built abc123def456\n"]

        with patch(
            "subprocess.Popen", return_value=mock_process
        ) as mock_popen, patch.object(client, "is_docker_available", return_value=True):
            client.build(dockerfile_path, tag, context_dir)

            # 验证命令参数
            called_cmd = mock_popen.call_args[0][0]
            assert called_cmd[0] == "docker"
            assert called_cmd[1] == "build"
            assert "-f" in called_cmd
            assert str(dockerfile_path) in called_cmd
            assert "-t" in called_cmd
            assert tag in called_cmd
            assert str(context_dir) in called_cmd
