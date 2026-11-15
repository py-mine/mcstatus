"""Tests for compatibility shims and build-time packaging behavior."""

import contextlib
import importlib
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Literal

import pytest
from hatchling.build import build_sdist, build_wheel

from tests.helpers import patch_project_version


@pytest.mark.parametrize("raises", [False, True])
@pytest.mark.parametrize(
    ("module", "msg_pattern"),
    [
        ("mcstatus._compat.forge_data", r"use mcstatus\.responses\.forge instead"),
    ],
)
def test_deprecated_import_path(raises: bool, module: str, msg_pattern: str) -> None:
    """Test that the compatibility shims emit deprecation warnings at import time.

    Note that this does NOT test the actual inclusion of the compatibility modules into
    the source tree at build time. This test intentionally only uses the _compat imports,
    as the shim files are only included on build time, which means testing those directly
    would fail.
    """
    # importlib.import_module caches module, if it didn't raise
    _ = sys.modules.pop(module, None)

    context_manager = (
        pytest.raises(DeprecationWarning, match=msg_pattern) if raises else pytest.deprecated_call(match=msg_pattern)
    )
    with patch_project_version("100.0.0" if raises else "0.0.0"), context_manager:
        _ = importlib.import_module(module)


@pytest.fixture(scope="session")
def sdist_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build an sdist once and return the path of the temporary directory where it exists."""
    source_root = Path(__file__).resolve().parent.parent

    tmp_dir = tmp_path_factory.mktemp("build")

    tmp_path = Path(tmp_dir)
    build_root = tmp_path / "mcstatus"
    _ = shutil.copytree(
        source_root,
        build_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "build",
            "_build",
            ".ruff_cache",
        ),
    )
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()

    # Build from a clean temp copy so we validate the sdist contents.
    with contextlib.chdir(build_root):
        sdist_name = build_sdist(str(dist_dir))

    sdist_path = dist_dir / sdist_name
    return sdist_path


@pytest.fixture(scope="session")
def sdist_member_names(sdist_path: Path) -> set[str]:
    """Build an sdist once and return all archive member names."""
    with tarfile.open(sdist_path, "r:gz") as tar:
        tar_names = set(tar.getnames())
        return tar_names


@pytest.fixture(scope="session")
def wheel_member_names(sdist_path: Path, tmp_path_factory: pytest.TempPathFactory) -> set[str]:
    """Build a wheel once and return all archive member names."""
    tmp_path = tmp_path_factory.mktemp("wheel-build")

    # Extract the sdist files first
    sdist_extract_root = tmp_path / "sdist"
    sdist_extract_root.mkdir()
    with tarfile.open(sdist_path, "r:gz") as tar:
        tar.extractall(sdist_extract_root, filter="data")

    # Get the first (and only) subdir inside of the sdist extract directory.
    # This will contain the sdist files from this specific build (e.g. mcstatus-0.0.0).
    sdist_root = next(path for path in sdist_extract_root.iterdir() if path.is_dir())

    wheel_build_dir = tmp_path / "dist"
    wheel_build_dir.mkdir()

    # Build the wheel from the sdist content to ensure compat shims persist.
    with contextlib.chdir(sdist_root):
        wheel_name = build_wheel(str(wheel_build_dir))

    wheel_path = wheel_build_dir / wheel_name
    with zipfile.ZipFile(wheel_path) as wheel:
        wheel_names = set(wheel.namelist())
        return wheel_names


@pytest.mark.parametrize("member_names_from", ["sdist", "wheel"])
@pytest.mark.parametrize(
    "expected_path",
    [
        "mcstatus/forge_data.py",
    ],
)
def test_includes_compat_shims(
    sdist_member_names: set[str],
    wheel_member_names: set[str],
    member_names_from: Literal["sdist", "wheel"],
    expected_path: str,
) -> None:
    """Assert the built wheel and sdist both bundle compatibility shims into their legacy paths."""
    member_names = sdist_member_names if member_names_from == "sdist" else wheel_member_names
    assert any(name.endswith(expected_path) for name in member_names)
