"""Tests for the detector module: sensitive files, bloat detection, and stack signatures."""

from pathlib import Path
import pytest

from agentignore.detector import (
    detect_project_stacks,
    get_stack_patterns,
    is_bloat_path,
    is_lockfile_path,
    is_sensitive_path,
)


class TestSensitiveDetection:
    """Deterministic tests for secret/sensitive path recognition."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            ".env",
            ".env.local",
            ".env.production",
            ".env.staging.local",
            "secrets/app.env",
            "certs/server.key",
            "ssl/private.pem",
            "auth/id_rsa",
            "id_ed25519",
            "config/service-account.json",
            "keys/production-secret.json",
            "app.keystore",
        ],
    )
    def test_sensitive_files_are_correctly_identified(self, rel_path: str):
        assert is_sensitive_path(rel_path) is True, f"Expected '{rel_path}' to be detected as sensitive"

    @pytest.mark.parametrize(
        "rel_path",
        [
            "src/index.ts",
            "auth/id_rsa.pub",
            "certs/server.crt",
            "main.py",
            "README.md",
            "package.json",
            "Cargo.toml",
            "tests/test_auth.py",
            "docs/environment_guide.md",  # Not an actual .env file
            "controllers/user.controller.ts",
        ],
    )
    def test_normal_source_files_are_not_sensitive(self, rel_path: str):
        assert is_sensitive_path(rel_path) is False, f"Expected '{rel_path}' NOT to be detected as sensitive"


class TestBloatDetection:
    """Deterministic tests for context-bloating artifacts."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "node_modules/lodash/index.js",
            "dist/bundle.js",
            "build/main.js",
            "target/release/app",
            "__pycache__/module.cpython-311.pyc",
            ".pytest_cache/v/cache/lastfailed",
            "app.min.js",
            "styles.min.css",
            "bundle.js.map",
            ".DS_Store",
            "logs/error.log",
            "data/local.sqlite",
        ],
    )
    def test_bloat_files_are_correctly_identified(self, rel_path: str):
        assert is_bloat_path(rel_path) is True, f"Expected '{rel_path}' to be detected as bloat"

    @pytest.mark.parametrize(
        "rel_path",
        [
            "src/app.py",
            "src/components/Button.tsx",
            "tests/conftest.py",
            "Cargo.toml",
        ],
    )
    def test_normal_source_files_are_not_bloat(self, rel_path: str):
        assert is_bloat_path(rel_path) is False, f"Expected '{rel_path}' NOT to be detected as bloat"


class TestLockfileDetection:
    """Tests for package manager lockfile recognition."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "Cargo.lock",
            "composer.lock",
        ],
    )
    def test_lockfiles_are_recognized(self, rel_path: str):
        assert is_lockfile_path(rel_path) is True


class TestStackDetection:
    """Tests for repository technology stack detection."""

    def test_detects_node_stack(self, tmp_path: Path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        stacks = detect_project_stacks(tmp_path)
        assert "Node.js / TypeScript" in stacks

    def test_detects_python_stack(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[project]", encoding="utf-8")
        stacks = detect_project_stacks(tmp_path)
        assert "Python" in stacks

    def test_detects_multi_stack(self, tmp_path: Path):
        (tmp_path / "package.json").write_text("{}", encoding="utf-8")
        (tmp_path / "Cargo.toml").write_text("[package]", encoding="utf-8")
        (tmp_path / "Dockerfile").write_text("FROM alpine", encoding="utf-8")

        stacks = detect_project_stacks(tmp_path)
        assert "Node.js / TypeScript" in stacks
        assert "Rust" in stacks
        assert "Docker" in stacks

    def test_get_stack_patterns_includes_relevant_ignores(self):
        patterns = get_stack_patterns(["Node.js / TypeScript", "Python"])
        assert "node_modules/" in patterns
        assert "__pycache__/" in patterns
