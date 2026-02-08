"""Tests for compatibility shims and build-time packaging behavior."""

import importlib
import os
import shutil
import tarfile
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import pytest
from hatchling.build import build_sdist, build_wheel


@contextmanager
def _chdir(path: Path) -> Iterator[None]:
    """Temporarily change the working directory (Python 3.10 compatibility equivalent of ``contextlib.chdir``)."""
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def _extractall_compat(tar: tarfile.TarFile, destination: Path) -> None:
    """Extract a tar archive in a way that works across Python versions and platforms.

    This is a helper utility that avoids a deprecation warning from tarfile stdlib.

    Python 3.14 deprecates ``TarFile.extractall`` without a filter, but Python 3.10 on
    Windows does not accept the ``filter`` keyword. Use the secure filter when available,
    and fall back to the legacy call only when the runtime rejects the keyword argument.
    """
    try:
        tar.extractall(destination, filter="data")
    except TypeError as exc:
        if "unexpected keyword argument 'filter'" not in str(exc):
            raise
        # This call is unsafe for malicious archives, due to path escapes (like files
        # with ../foo getting placed outside of our destination) but we know what we
        # built and this is only used within unit-tests, so it's not really important
        # to be strict about handling this.
        tar.extractall(destination)  # noqa: S202


@pytest.mark.parametrize(
    ("module", "msg_pattern"),
    [
        ("mcstatus._compat.status_response", r"use mcstatus\.responses instead"),
        ("mcstatus._compat.forge_data", r"use mcstatus\.responses\.forge instead"),
        ("mcstatus._compat.motd_transformers", r"MOTD Transformers are no longer a part of mcstatus public API"),
    ],
)
def test_deprecated_import_path(module: str, msg_pattern: str):
    """Test that the compatibility shims emit deprecation warnings at import time.

    Note that this does NOT test the actual inclusion of the compatibility modules into
    the source tree at build time. This test intentionally only uses the _compat imports,
    as the shim files are only included on build time, which means testing those directly
    would fail.
    """
    with pytest.deprecated_call(match=msg_pattern):
        importlib.import_module(module)


@pytest.fixture(scope="session")
def sdist_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build an sdist once and return the path of the temporary directory where it exists."""
    source_root = Path(__file__).resolve().parent.parent

    tmp_dir = tmp_path_factory.mktemp("build")

    tmp_path = Path(tmp_dir)
    build_root = tmp_path / "mcstatus"
    shutil.copytree(
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
    with _chdir(build_root):
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
        _extractall_compat(tar, sdist_extract_root)

    # Get the first (and only) subdir inside of the sdist extract directory.
    # This will contain the sdist files from this specific build (e.g. mcstatus-0.0.0).
    sdist_root = next(path for path in sdist_extract_root.iterdir() if path.is_dir())

    wheel_build_dir = tmp_path / "dist"
    wheel_build_dir.mkdir()

    # Build the wheel from the sdist content to ensure compat shims persist.
    with _chdir(sdist_root):
        wheel_name = build_wheel(str(wheel_build_dir))

    wheel_path = wheel_build_dir / wheel_name
    with zipfile.ZipFile(wheel_path) as wheel:
        wheel_names = set(wheel.namelist())
        return wheel_names


@pytest.mark.parametrize("member_names_from", ["sdist", "wheel"])
@pytest.mark.parametrize(
    "expected_path",
    [
        "mcstatus/status_response.py",
        "mcstatus/forge_data.py",
        "mcstatus/motd/transformers.py",
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
