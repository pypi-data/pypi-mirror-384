"""Tests for Dockerfile generator."""

import tempfile
from pathlib import Path

import pytest

from uni_agent_sdk.build_system.dockerfile_generator import DockerfileGenerator


class TestDockerfileGenerator:
    """Test suite for DockerfileGenerator."""

    @pytest.fixture
    def generator(self) -> DockerfileGenerator:
        """Create a DockerfileGenerator instance."""
        return DockerfileGenerator()

    @pytest.fixture
    def temp_project_dir(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        return tmp_path

    @pytest.fixture
    def project_with_pyproject(self, temp_project_dir: Path) -> Path:
        """Create a project directory with pyproject.toml."""
        pyproject_content = """\
[project]
name = "test_robot"
version = "0.1.0"
"""
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")
        return temp_project_dir

    def test_has_dockerfile_returns_false_when_not_exists(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test has_dockerfile returns False when Dockerfile doesn't exist."""
        print("\n=== Test: has_dockerfile returns False when not exists ===")
        result = generator.has_dockerfile(temp_project_dir)
        print(f"Result: {result}")
        assert result is False

    def test_has_dockerfile_returns_true_when_exists(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test has_dockerfile returns True when Dockerfile exists."""
        print("\n=== Test: has_dockerfile returns True when exists ===")
        # Create a Dockerfile
        dockerfile_path = temp_project_dir / "Dockerfile"
        dockerfile_path.write_text("FROM python:3.11-slim", encoding="utf-8")

        result = generator.has_dockerfile(temp_project_dir)
        print(f"Dockerfile exists at: {dockerfile_path}")
        print(f"Result: {result}")
        assert result is True

    def test_get_dockerfile_path(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test get_dockerfile_path returns correct path."""
        print("\n=== Test: get_dockerfile_path returns correct path ===")
        expected_path = temp_project_dir / "Dockerfile"
        result = generator.get_dockerfile_path(temp_project_dir)
        print(f"Expected path: {expected_path}")
        print(f"Result path: {result}")
        assert result == expected_path

    def test_generate_with_explicit_package_name(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generate creates Dockerfile with explicit package name."""
        print("\n=== Test: generate with explicit package name ===")
        package_name = "my_robot"

        result_path = generator.generate(temp_project_dir, package_name)

        print(f"Generated Dockerfile at: {result_path}")
        assert result_path.exists()
        assert result_path == temp_project_dir / "Dockerfile"

        # Verify content
        content = result_path.read_text(encoding="utf-8")
        print(f"Dockerfile content length: {len(content)} bytes")
        print("Checking for required content...")

        # Check for multi-stage build
        assert "FROM python:3.11-slim as builder" in content
        print("✓ Builder stage found")
        assert "FROM python:3.11-slim" in content
        print("✓ Final stage found")

        # Check for package name in entrypoint
        assert f'CMD ["python", "-m", "{package_name}.main"]' in content
        print(f"✓ Package name '{package_name}' in CMD")

        # Check for health check
        assert "HEALTHCHECK" in content
        print("✓ HEALTHCHECK found")

        # Check for environment variables
        assert "ENV PYTHONUNBUFFERED=1" in content
        assert "ENV PYTHONDONTWRITEBYTECODE=1" in content
        print("✓ Environment variables found")

        # Check for virtual environment setup
        assert "/opt/venv" in content
        print("✓ Virtual environment setup found")

    def test_generate_reads_package_name_from_pyproject(
        self, generator: DockerfileGenerator, project_with_pyproject: Path
    ) -> None:
        """Test generate reads package name from pyproject.toml."""
        print("\n=== Test: generate reads package name from pyproject.toml ===")

        result_path = generator.generate(project_with_pyproject)

        print(f"Generated Dockerfile at: {result_path}")
        assert result_path.exists()

        # Verify content uses package name from pyproject.toml
        content = result_path.read_text(encoding="utf-8")
        print("Checking for package name from pyproject.toml...")
        assert 'CMD ["python", "-m", "test_robot.main"]' in content
        print("✓ Package name 'test_robot' from pyproject.toml found in CMD")

    def test_generate_raises_error_when_dockerfile_exists(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generate raises FileExistsError when Dockerfile exists."""
        print("\n=== Test: generate raises error when Dockerfile exists ===")

        # Create existing Dockerfile
        dockerfile_path = temp_project_dir / "Dockerfile"
        dockerfile_path.write_text("FROM python:3.11-slim", encoding="utf-8")
        print(f"Created existing Dockerfile at: {dockerfile_path}")

        with pytest.raises(FileExistsError) as excinfo:
            generator.generate(temp_project_dir, "test_robot")

        print(f"Raised exception: {excinfo.value}")
        assert "already exists" in str(excinfo.value)

    def test_generate_raises_error_when_package_name_not_found(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generate raises ValueError when package name cannot be determined."""
        print("\n=== Test: generate raises error when package name not found ===")

        # No pyproject.toml and no explicit package_name
        with pytest.raises(ValueError) as excinfo:
            generator.generate(temp_project_dir)

        print(f"Raised exception: {excinfo.value}")
        assert "Could not determine package name" in str(excinfo.value)

    def test_read_package_name_from_valid_pyproject(
        self, generator: DockerfileGenerator, project_with_pyproject: Path
    ) -> None:
        """Test _read_package_name extracts name from valid pyproject.toml."""
        print("\n=== Test: read package name from valid pyproject.toml ===")

        result = generator._read_package_name(project_with_pyproject)

        print(f"Package name: {result}")
        assert result == "test_robot"

    def test_read_package_name_returns_none_when_file_missing(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _read_package_name returns None when pyproject.toml missing."""
        print("\n=== Test: read package name returns None when file missing ===")

        result = generator._read_package_name(temp_project_dir)

        print(f"Result: {result}")
        assert result is None

    def test_read_package_name_returns_none_when_name_missing(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _read_package_name returns None when name field missing."""
        print("\n=== Test: read package name returns None when name missing ===")

        # Create pyproject.toml without name field
        pyproject_content = """\
[project]
version = "0.1.0"
"""
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        result = generator._read_package_name(temp_project_dir)

        print(f"Result: {result}")
        assert result is None

    def test_dockerfile_contains_required_stages(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generated Dockerfile contains required build stages."""
        print("\n=== Test: Dockerfile contains required stages ===")

        result_path = generator.generate(temp_project_dir, "test_robot")
        content = result_path.read_text(encoding="utf-8")

        print("Checking for build stages...")

        # Check for builder stage
        assert "FROM python:3.11-slim as builder" in content
        print("✓ Builder stage with 'as builder' alias")

        # Check for final stage
        lines = content.splitlines()
        final_stage_found = False
        for i, line in enumerate(lines):
            if (
                line.strip().startswith("FROM python:3.11-slim")
                and "as builder" not in line
            ):
                final_stage_found = True
                print(f"✓ Final stage found at line {i + 1}")
                break

        assert final_stage_found, "Final stage not found"

    def test_dockerfile_contains_healthcheck(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generated Dockerfile contains proper health check."""
        print("\n=== Test: Dockerfile contains health check ===")

        result_path = generator.generate(temp_project_dir, "test_robot")
        content = result_path.read_text(encoding="utf-8")

        print("Checking health check configuration...")

        # Check for HEALTHCHECK instruction
        assert "HEALTHCHECK" in content
        print("✓ HEALTHCHECK instruction found")

        # Check for health check parameters
        assert "--interval=30s" in content
        print("✓ Interval parameter: 30s")

        assert "--timeout=3s" in content
        print("✓ Timeout parameter: 3s")

        assert "--start-period=5s" in content
        print("✓ Start period parameter: 5s")

        assert "--retries=3" in content
        print("✓ Retries parameter: 3")

        # Check for health check command
        assert 'CMD python -c "import sys; sys.exit(0)"' in content
        print("✓ Health check command found")

    def test_dockerfile_contains_environment_variables(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generated Dockerfile contains required environment variables."""
        print("\n=== Test: Dockerfile contains environment variables ===")

        result_path = generator.generate(temp_project_dir, "test_robot")
        content = result_path.read_text(encoding="utf-8")

        print("Checking environment variables...")

        # Check for Python environment variables
        assert "ENV PYTHONUNBUFFERED=1" in content
        print("✓ PYTHONUNBUFFERED=1")

        assert "ENV PYTHONDONTWRITEBYTECODE=1" in content
        print("✓ PYTHONDONTWRITEBYTECODE=1")

        # Check for PATH configuration
        assert 'ENV PATH="/opt/venv/bin:$PATH"' in content
        print("✓ PATH configuration for virtual environment")

    def test_dockerfile_contains_copy_instructions(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generated Dockerfile contains proper COPY instructions."""
        print("\n=== Test: Dockerfile contains COPY instructions ===")

        result_path = generator.generate(temp_project_dir, "test_robot")
        content = result_path.read_text(encoding="utf-8")

        print("Checking COPY instructions...")

        # Check for requirements.txt copy in builder stage
        assert "COPY requirements.txt ." in content
        print("✓ COPY requirements.txt in builder stage")

        # Check for virtual environment copy from builder
        assert "COPY --from=builder /opt/venv /opt/venv" in content
        print("✓ COPY virtual environment from builder stage")

        # Check for application code copy
        assert "COPY . ." in content
        print("✓ COPY application code")

    def test_dockerfile_uses_slim_base_image(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generated Dockerfile uses slim Python base image."""
        print("\n=== Test: Dockerfile uses slim base image ===")

        result_path = generator.generate(temp_project_dir, "test_robot")
        content = result_path.read_text(encoding="utf-8")

        print("Checking base image...")

        # Check for slim variant
        assert "python:3.11-slim" in content
        print("✓ Uses python:3.11-slim base image")

        # Ensure we're not using full python image
        assert "FROM python:3.11\n" not in content
        print("✓ Not using full python:3.11 image")

    def test_dockerfile_workdir_configuration(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test generated Dockerfile has proper WORKDIR configuration."""
        print("\n=== Test: Dockerfile WORKDIR configuration ===")

        result_path = generator.generate(temp_project_dir, "test_robot")
        content = result_path.read_text(encoding="utf-8")

        print("Checking WORKDIR configuration...")

        # Check for builder workdir
        assert "WORKDIR /build" in content
        print("✓ Builder stage WORKDIR /build")

        # Check for final stage workdir
        assert "WORKDIR /app" in content
        print("✓ Final stage WORKDIR /app")

    def test_parse_package_name_simple_fallback(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _parse_package_name_simple fallback parser."""
        print("\n=== Test: simple parser fallback ===")

        # Create pyproject.toml
        pyproject_content = """\
[project]
name = "fallback_test"
version = "1.0.0"
"""
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        result = generator._parse_package_name_simple(pyproject_path)

        print(f"Package name from simple parser: {result}")
        assert result == "fallback_test"

    def test_parse_package_name_simple_handles_single_quotes(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _parse_package_name_simple handles single quotes."""
        print("\n=== Test: simple parser handles single quotes ===")

        # Create pyproject.toml with single quotes
        pyproject_content = """\
[project]
name = 'single_quote_test'
version = '1.0.0'
"""
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        result = generator._parse_package_name_simple(pyproject_path)

        print(f"Package name: {result}")
        assert result == "single_quote_test"

    def test_parse_package_name_simple_stops_at_next_section(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _parse_package_name_simple stops at next section."""
        print("\n=== Test: simple parser stops at next section ===")

        # Create pyproject.toml with another section containing 'name'
        pyproject_content = """\
[project]
name = "correct_name"

[tool.something]
name = "wrong_name"
"""
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        result = generator._parse_package_name_simple(pyproject_path)

        print(f"Package name: {result}")
        assert result == "correct_name"

    def test_parse_package_name_simple_handles_malformed_file(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _parse_package_name_simple handles malformed files gracefully."""
        print("\n=== Test: simple parser handles malformed file ===")

        # Create malformed pyproject.toml
        pyproject_content = "[project]\nname = unquoted value that breaks parsing"
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        # Should not raise exception, just return None
        result = generator._parse_package_name_simple(pyproject_path)

        print(f"Result: {result}")
        assert result is None

    def test_read_package_name_handles_toml_parsing_error(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _read_package_name handles TOML parsing errors gracefully."""
        print("\n=== Test: read package name handles TOML parsing error ===")

        # Create invalid TOML file
        pyproject_content = "[project\nname = 'broken"
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        # Should not raise exception, just return None
        result = generator._read_package_name(temp_project_dir)

        print(f"Result: {result}")
        assert result is None

    def test_parse_package_name_simple_with_no_equals_sign(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _parse_package_name_simple handles line without equals sign."""
        print("\n=== Test: simple parser handles line without equals ===")

        # Create pyproject.toml with malformed name line
        pyproject_content = """\
[project]
name
version = "1.0.0"
"""
        pyproject_path = temp_project_dir / "pyproject.toml"
        pyproject_path.write_text(pyproject_content, encoding="utf-8")

        result = generator._parse_package_name_simple(pyproject_path)

        print(f"Result: {result}")
        assert result is None

    def test_parse_package_name_simple_returns_none_on_io_error(
        self, generator: DockerfileGenerator, temp_project_dir: Path
    ) -> None:
        """Test _parse_package_name_simple handles IO errors."""
        print("\n=== Test: simple parser handles IO error ===")

        # Use non-existent file path
        non_existent_path = temp_project_dir / "non_existent.toml"

        result = generator._parse_package_name_simple(non_existent_path)

        print(f"Result: {result}")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
