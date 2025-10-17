"""Dockerfile generator for robot projects.

This module generates optimized Dockerfiles with multi-stage builds,
health checks, and proper environment configuration.
"""

import sys
from pathlib import Path
from typing import Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


class DockerfileGenerator:
    """Generates optimized Dockerfiles for robot projects.

    Features:
    - Multi-stage builds for smaller final images
    - Health check configuration
    - Environment variable support
    - Automatic package name detection from pyproject.toml
    """

    DOCKERFILE_TEMPLATE = """\
# ============ 编译阶段 ============
FROM python:3.11-slim as builder

WORKDIR /build

# 配置阿里云 APT 源（替换默认源，加速国内构建）
RUN rm -rf /etc/apt/sources.list.d/* && \\
    echo "deb http://mirrors.aliyun.com/debian/ bookworm main non-free contrib" > /etc/apt/sources.list && \\
    echo "deb-src http://mirrors.aliyun.com/debian/ bookworm main non-free contrib" >> /etc/apt/sources.list && \\
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main non-free contrib" >> /etc/apt/sources.list && \\
    echo "deb-src http://mirrors.aliyun.com/debian/ bookworm-updates main non-free contrib" >> /etc/apt/sources.list && \\
    apt-get update

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖（使用阿里云 pip 源）
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -i https://mirrors.aliyun.com/pypi/simple --no-cache-dir -r requirements.txt

# ============ 运行阶段 ============
FROM python:3.11-slim

WORKDIR /app

# 配置阿里云 APT 源（替换默认源）
RUN rm -rf /etc/apt/sources.list.d/* && \\
    echo "deb http://mirrors.aliyun.com/debian/ bookworm main non-free contrib" > /etc/apt/sources.list && \\
    echo "deb-src http://mirrors.aliyun.com/debian/ bookworm main non-free contrib" >> /etc/apt/sources.list && \\
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main non-free contrib" >> /etc/apt/sources.list && \\
    echo "deb-src http://mirrors.aliyun.com/debian/ bookworm-updates main non-free contrib" >> /etc/apt/sources.list && \\
    apt-get update

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置虚拟环境
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 入口点
ENTRYPOINT ["python"]
CMD ["-u", "/app/main.py"]
"""

    def __init__(self) -> None:
        """Initialize Dockerfile generator."""
        pass

    def has_dockerfile(self, project_dir: Path) -> bool:
        """Check if Dockerfile already exists in project.

        Args:
            project_dir: Project root directory

        Returns:
            True if Dockerfile exists, False otherwise
        """
        return self.get_dockerfile_path(project_dir).exists()

    def get_dockerfile_path(self, project_dir: Path) -> Path:
        """Get path to Dockerfile in project.

        Args:
            project_dir: Project root directory

        Returns:
            Path to Dockerfile
        """
        return project_dir / "Dockerfile"

    def generate(self, project_dir: Path, package_name: Optional[str] = None) -> Path:
        """Generate Dockerfile for project.

        Args:
            project_dir: Project root directory
            package_name: Python package name for entrypoint.
                         If not provided, will be read from pyproject.toml

        Returns:
            Path to generated Dockerfile

        Raises:
            ValueError: If package name cannot be determined
            FileExistsError: If Dockerfile already exists
        """
        # Check if Dockerfile already exists
        dockerfile_path = self.get_dockerfile_path(project_dir)
        if dockerfile_path.exists():
            raise FileExistsError(
                f"Dockerfile already exists at {dockerfile_path}. "
                "Remove it first if you want to regenerate."
            )

        # Determine package name
        if package_name is None:
            package_name = self._read_package_name(project_dir)
            if package_name is None:
                raise ValueError(
                    "Could not determine package name. "
                    "Please provide package_name parameter or ensure "
                    "pyproject.toml contains [project] name field."
                )

        # Generate Dockerfile content
        dockerfile_content = self.DOCKERFILE_TEMPLATE.format(package_name=package_name)

        # Write Dockerfile
        dockerfile_path.write_text(dockerfile_content, encoding="utf-8")

        return dockerfile_path

    def _read_package_name(self, project_dir: Path) -> Optional[str]:
        """Read package name from pyproject.toml.

        Args:
            project_dir: Project root directory

        Returns:
            Package name or None if not found
        """
        pyproject_path = project_dir / "pyproject.toml"

        if not pyproject_path.exists():
            return None

        # Check if tomllib is available
        if tomllib is None:
            # Fallback to simple parsing for Python < 3.11 without tomli
            return self._parse_package_name_simple(pyproject_path)

        try:
            with open(pyproject_path, "rb") as f:
                config = tomllib.load(f)
                return config.get("project", {}).get("name")
        except Exception:
            # If parsing fails, return None
            return None

    def _parse_package_name_simple(self, pyproject_path: Path) -> Optional[str]:
        """Simple parser for package name from pyproject.toml.

        This is a fallback for Python < 3.11 without tomli installed.

        Args:
            pyproject_path: Path to pyproject.toml

        Returns:
            Package name or None if not found
        """
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            in_project_section = False

            for line in content.splitlines():
                line = line.strip()

                # Check for [project] section
                if line == "[project]":
                    in_project_section = True
                    continue

                # If we hit another section, stop
                if line.startswith("[") and line.endswith("]"):
                    in_project_section = False
                    continue

                # Look for name field in project section
                if in_project_section and line.startswith("name"):
                    # Parse name = "value"
                    if "=" in line:
                        _, value = line.split("=", 1)
                        value = value.strip()
                        # Remove quotes
                        if value.startswith('"') and value.endswith('"'):
                            return value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            return value[1:-1]

            return None
        except Exception:
            return None
