"""
构建管理器模块

统筹构建流程：读取配置、生成 Dockerfile、构建镜像、获取镜像信息
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .docker_client import DockerClient, DockerError
from .dockerfile_generator import DockerfileGenerator

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


class BuildManagerError(Exception):
    """构建管理器异常"""

    pass


class BuildManager:
    """构建管理器

    统筹整个镜像构建流程：
    1. 读取 pyproject.toml 获取项目信息
    2. 自动修复 Dockerfile（添加阿里云源）
    3. 自动修复 requirements.txt（添加缺失依赖）
    4. 调用 DockerClient 构建镜像
    5. 获取并返回镜像信息

    零配置策略：所有配置均硬编码在代码中，支持环境变量覆盖
    TODO: 未来将这些配置移到 ~/.uni-agent/config.yaml 和 .robot.yaml
    """

    # 默认配置（零配置优先）
    # TODO: 迁移到 ConfigProvider，支持 .robot.yaml 和环境变量覆盖
    DEFAULT_CONFIG = {
        "apt_mirror": "mirrors.aliyun.com/debian",  # APT 源
        "pip_mirror": "mirrors.aliyun.com/pypi/simple",  # pip 源
        "required_dependencies": [
            "aio-pika>=9.5.0",  # uni_agent_sdk 的隐含依赖
        ],
    }

    def __init__(self, project_dir: Path, docker_client: DockerClient) -> None:
        """
        初始化构建管理器

        Args:
            project_dir: 项目根目录（包含 pyproject.toml）
            docker_client: Docker 客户端实例
        """
        self.project_dir = project_dir.resolve()
        self.docker_client = docker_client
        self.dockerfile_generator = DockerfileGenerator()

        # 读取项目配置
        self.project_config = self.read_project_config()

    def read_project_config(self) -> Dict[str, str]:
        """
        读取 pyproject.toml 获取项目信息

        Returns:
            包含以下字段的字典：
            - name: 项目名称（如 "oss-agent"）
            - version: 项目版本（如 "1.0.0"）
            - package_name: Python 包名（如 "oss_agent"）

        Raises:
            BuildManagerError: 如果配置文件不存在或格式错误
        """
        pyproject_path = self.project_dir / "pyproject.toml"

        if not pyproject_path.exists():
            raise BuildManagerError(
                f"pyproject.toml 不存在: {pyproject_path}\n"
                "请确保在项目根目录运行构建命令。"
            )

        # 使用 tomllib/tomli 解析
        if tomllib is None:
            raise BuildManagerError(
                "缺少 TOML 解析库。\n"
                "Python 3.11+ 自带 tomllib，Python 3.8-3.10 需要安装 tomli:\n"
                "  pip install tomli"
            )

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise BuildManagerError(f"解析 pyproject.toml 失败: {e}")

        # 提取项目信息
        project = data.get("project", {})

        name = project.get("name")
        if not name:
            raise BuildManagerError(
                "pyproject.toml 中缺少 [project] name 字段。\n"
                "请确保配置文件包含项目名称。"
            )

        version = project.get("version", "")
        package_name = name.replace("-", "_")

        return {
            "name": name,
            "version": version,
            "package_name": package_name,
        }

    def build_image(self, version: Optional[str] = None, rebuild: bool = False) -> str:
        """
        构建 Docker 镜像

        自动化流程：
        1. 自动修复 requirements.txt（添加缺失依赖）
        2. 确保 Dockerfile 存在且已修复（添加阿里云源）
        3. 构建镜像
        4. 返回镜像标签

        Args:
            version: 指定版本号（可选）
                    如果不指定，按优先级使用：pyproject.toml > git hash > 时间戳
            rebuild: 是否强制重新构建（--no-cache）

        Returns:
            镜像标签（如 "robot-oss-agent:1.0.0"）

        Raises:
            BuildManagerError: 如果构建失败
            DockerError: 如果 Docker 操作失败
        """
        # 自动修复 requirements.txt（添加缺失的隐含依赖）
        requirements_path = self.project_dir / "requirements.txt"
        self._auto_patch_requirements(requirements_path)

        # 确定版本号
        determined_version = self._determine_version(version)

        # 生成镜像标签（格式：robot-{project_name}:{version}）
        image_tag = f"robot-{self.project_config['name']}:{determined_version}"

        # 确保 Dockerfile 存在且已修复
        dockerfile_path = self._ensure_dockerfile()

        # 显示构建信息
        print("\n" + "=" * 60)
        print(f"📦 项目名称: {self.project_config['name']}")
        print(f"🏷️  项目版本: {determined_version}")
        print(f"📝 Dockerfile: {dockerfile_path}")
        print("=" * 60 + "\n")

        # 记录开始时间
        start_time = datetime.now()

        # 计算 build context（使用 monorepo 根目录以支持本地依赖）
        context_dir = self._find_monorepo_root() or self.project_dir
        print(f"📁 Build Context: {context_dir}\n")

        # 构建镜像
        try:
            image_id = self.docker_client.build(
                dockerfile_path=dockerfile_path,
                tag=image_tag,
                context_dir=context_dir,
                no_cache=rebuild,
            )
        except DockerError as e:
            raise BuildManagerError(f"镜像构建失败: {e}")

        # 计算耗时
        elapsed = datetime.now() - start_time
        elapsed_seconds = elapsed.total_seconds()

        # 获取镜像信息
        try:
            image_info = self.get_image_info(image_tag)
        except DockerError:
            # 如果获取信息失败，使用默认值
            image_info = {"size_mb": "未知"}

        # 显示构建结果
        print("\n" + "=" * 60)
        print("✅ 镜像构建成功！")
        print(f"🏷️  镜像标签: {image_tag}")
        print(f"🆔 镜像 ID: {image_id}")
        print(f"📦 镜像大小: {image_info['size_mb']} MB")
        print(f"⏱️  构建耗时: {elapsed_seconds:.1f} 秒")
        print("=" * 60)

        # 提示下一步操作
        print("\n💡 下一步操作：")
        print(f"   • 测试运行: docker run --rm {image_tag}")
        print(f"   • 推送镜像: uni-agent publish {self.project_config['name']}")
        print()

        return image_tag

    def get_image_info(self, tag: str) -> Dict[str, str]:
        """
        获取镜像详细信息

        Args:
            tag: 镜像标签

        Returns:
            包含镜像信息的字典：
            - id: 镜像 ID（12位短格式）
            - size: 镜像大小（字节）
            - size_mb: 镜像大小（MB）
            - created: 创建时间

        Raises:
            DockerError: 如果获取信息失败
        """
        return self.docker_client.inspect_image(tag)

    def _determine_version(self, specified_version: Optional[str]) -> str:
        """
        确定版本号

        优先级（从高到低）：
        1. CLI 参数指定的版本
        2. pyproject.toml 中的版本
        3. Git commit hash（短格式）
        4. 时间戳（YYYY-MM-DD-HHmmss）

        Args:
            specified_version: 用户指定的版本号

        Returns:
            确定的版本号字符串
        """
        # 1. 优先使用 CLI 参数
        if specified_version:
            return specified_version

        # 2. 使用 pyproject.toml 中的版本
        if self.project_config.get("version"):
            return self.project_config["version"]

        # 3. 尝试获取 git hash
        git_hash = self._get_git_hash()
        if git_hash:
            return git_hash

        # 4. 使用时间戳
        return datetime.now().strftime("%Y-%m-%d-%H%M%S")

    def _get_git_hash(self) -> Optional[str]:
        """
        获取当前 git commit 的短 hash

        Returns:
            7位 git hash，如果不在 git 仓库或获取失败则返回 None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _ensure_dockerfile(self) -> Path:
        """
        确保 Dockerfile 存在且已自动修复

        如果 Dockerfile 不存在，自动生成一个
        然后自动修复：添加阿里云源配置

        Returns:
            Dockerfile 的路径

        Raises:
            BuildManagerError: 如果生成或修复 Dockerfile 失败
        """
        dockerfile_path = self.dockerfile_generator.get_dockerfile_path(
            self.project_dir
        )

        if not dockerfile_path.exists():
            print(f"📝 Dockerfile 不存在，正在生成...")

            try:
                self.dockerfile_generator.generate(
                    project_dir=self.project_dir,
                    package_name=self.project_config["package_name"],
                )
                print(f"✅ Dockerfile 已生成: {dockerfile_path}\n")
            except Exception as e:
                raise BuildManagerError(f"生成 Dockerfile 失败: {e}")

        # 自动修复 Dockerfile（添加阿里云源）
        self._auto_patch_dockerfile(dockerfile_path)

        return dockerfile_path

    def _auto_patch_dockerfile(self, dockerfile_path: Path) -> None:
        """
        自动修复 Dockerfile：添加阿里云源配置

        检测 Dockerfile 是否已有阿里云源配置，如果没有则添加

        Args:
            dockerfile_path: Dockerfile 的路径

        Raises:
            BuildManagerError: 如果修复失败
        """
        try:
            content = dockerfile_path.read_text(encoding="utf-8")

            # 检查是否已有阿里云源配置（避免重复）
            if "mirrors.aliyun.com" in content:
                print("✅ Dockerfile 已包含阿里云源配置")
                return

            print("🔧 Dockerfile 缺少阿里云源配置，正在自动添加...")

            # 添加源配置到编译阶段（builder）
            builder_stage_pattern = r"(FROM python:.+-slim as builder\s+WORKDIR /build)"
            apt_config = (
                "# 配置阿里云 APT 源（替换默认源）\n"
                'RUN rm -rf /etc/apt/sources.list.d/* && \\\n'
                '    echo "deb http://mirrors.aliyun.com/debian/ bookworm main non-free contrib" '
                "> /etc/apt/sources.list && \\\n"
                '    echo "deb-src http://mirrors.aliyun.com/debian/ bookworm main non-free contrib" '
                ">> /etc/apt/sources.list && \\\n"
                '    echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main non-free contrib" '
                ">> /etc/apt/sources.list && \\\n"
                '    echo "deb-src http://mirrors.aliyun.com/debian/ bookworm-updates main non-free contrib" '
                ">> /etc/apt/sources.list && \\\n"
                "    apt-get update\n"
            )

            builder_replacement = r"\1\n\n" + apt_config

            content = re.sub(builder_stage_pattern, builder_replacement, content)

            # 添加源配置到运行阶段（runtime）
            runtime_stage_pattern = r"(FROM python:.+-slim\s+WORKDIR /app)(?!\s*#)"
            content = re.sub(runtime_stage_pattern, r"\1\n\n" + apt_config, content)

            # 修改 pip install 命令添加阿里云源
            # 替换 "pip install " 为 "pip install -i https://mirrors.aliyun.com/pypi/simple "
            pip_pattern = r"pip install(\s+)"
            pip_replacement = f"pip install -i https://{self.DEFAULT_CONFIG['pip_mirror']}\\1"
            content = re.sub(pip_pattern, pip_replacement, content)

            # 修复 ENTRYPOINT：检查是否使用了模块运行方式（-m package.main）
            # 如果 main.py 直接存在于项目根目录，改为直接运行脚本
            if 'CMD ["python", "-m"' in content and self.project_dir.joinpath("main.py").exists():
                # 替换 CMD ["python", "-m", "package.main"] 为 ENTRYPOINT ["python"] + CMD ["-u", "/app/main.py"]
                content = re.sub(
                    r'CMD \["python", "-m", "[^"]+"\]',
                    'ENTRYPOINT ["python"]\nCMD ["-u", "/app/main.py"]',
                    content
                )

            # 写回文件
            dockerfile_path.write_text(content, encoding="utf-8")
            print("✅ Dockerfile 已自动修复：添加了阿里云源配置\n")

        except Exception as e:
            raise BuildManagerError(f"修复 Dockerfile 失败: {e}")

    def _auto_patch_requirements(self, requirements_path: Path) -> None:
        """
        自动修复 requirements.txt：添加缺失的隐含依赖

        检测项目中使用的隐含依赖并自动添加到 requirements.txt

        Args:
            requirements_path: requirements.txt 的路径

        Raises:
            BuildManagerError: 如果修复失败
        """
        try:
            # 读取 requirements.txt
            if not requirements_path.exists():
                print("ℹ️  requirements.txt 不存在，跳过依赖检查")
                return

            content = requirements_path.read_text(encoding="utf-8")
            existing_deps = self._parse_requirements(content)

            # 检查缺失的必需依赖
            missing_deps = []
            for dep in self.DEFAULT_CONFIG["required_dependencies"]:
                dep_name = dep.split(">=")[0].split("==")[0].strip()
                # 检查是否已存在
                if not any(dep_name.lower() in existing.lower() for existing in existing_deps):
                    missing_deps.append(dep)

            if not missing_deps:
                print("✅ requirements.txt 已包含所有必需依赖")
                return

            # 添加缺失的依赖
            print(
                f"🔧 发现缺失依赖: {', '.join(missing_deps)}，正在自动添加..."
            )

            # 追加到 requirements.txt
            if not content.endswith("\n"):
                content += "\n"

            for dep in missing_deps:
                content += f"{dep}\n"

            requirements_path.write_text(content, encoding="utf-8")
            print(f"✅ requirements.txt 已自动修复：添加了缺失依赖\n")

        except Exception as e:
            raise BuildManagerError(f"修复 requirements.txt 失败: {e}")

    def _parse_requirements(self, content: str) -> List[str]:
        """
        解析 requirements.txt 中的依赖列表

        Args:
            content: requirements.txt 的内容

        Returns:
            依赖列表，如 ['aiohttp>=3.8.0', 'pydantic>=2.0.0']
        """
        deps = []
        for line in content.splitlines():
            line = line.strip()
            # 跳过空行和注释
            if line and not line.startswith("#"):
                deps.append(line)
        return deps

    def _find_monorepo_root(self) -> Optional[Path]:
        """
        查找 monorepo 根目录（包含 uni_agent_sdk 的目录）

        从项目目录向上查找，直到找到包含 uni_agent_sdk 的目录

        Returns:
            monorepo 根目录路径，如果不在 monorepo 中则返回 None
        """
        current = self.project_dir
        # 最多向上查找 5 层
        for _ in range(5):
            if (current / "uni_agent_sdk").exists():
                return current
            parent = current.parent
            if parent == current:  # 到达了文件系统根目录
                break
            current = parent

        return None
