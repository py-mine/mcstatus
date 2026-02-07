from __future__ import annotations

import importlib.metadata
import re
from functools import wraps
import warnings

import pytest

from mcstatus.utils.deprecation import deprecated, deprecation_warn, _get_project_version

LIB_NAME = "mcstatus"


def _patch_project_version(monkeypatch: pytest.MonkeyPatch, version: str | None):
    """Patch the project version reported by ``importlib.metadata.version``.

    This is used to simulate different project versions for testing purposes.
    If ``version`` is ``None``, a :exc:`PackageNotFoundError` will be raised
    when trying to get the project version.
    """
    orig_version_func = importlib.metadata.version

    @wraps(orig_version_func)
    def patched_version_func(distribution_name: str) -> str:
        if distribution_name == LIB_NAME:
            if version is None:
                raise importlib.metadata.PackageNotFoundError
            return version
        return orig_version_func(distribution_name)

    _get_project_version.cache_clear()
    monkeypatch.setattr(importlib.metadata, "version", patched_version_func)


def test_deprecation_warn_produces_error(monkeypatch: pytest.MonkeyPatch):
    """Test deprecation_warn with older removal_version than current version produces exception."""
    _patch_project_version(monkeypatch, "1.0.0")

    with pytest.raises(DeprecationWarning, match=r"^test is passed its removal version \(0\.9\.0\)\.$"):
        deprecation_warn(obj_name="test", removal_version="0.9.0")


def test_deprecation_warn_produces_warning(monkeypatch: pytest.MonkeyPatch):
    """Test deprecation_warn with newer removal_version than current version produces warning."""
    _patch_project_version(monkeypatch, "1.0.0")

    with pytest.deprecated_call(match=r"^test is deprecated and scheduled for removal in 1\.0\.1\.$"):
        deprecation_warn(obj_name="test", removal_version="1.0.1")


def test_deprecation_warn_unknown_version(monkeypatch: pytest.MonkeyPatch):
    """Test deprecation_warn with unknown project version.

    This could occur if the project wasn't installed as a package. (e.g. when running directly from
    source, like via a git submodule.)
    """
    _patch_project_version(monkeypatch, None)

    with pytest.warns(match=f"Failed to get {LIB_NAME} project version", expected_warning=RuntimeWarning):
        with pytest.deprecated_call(match=r"^test is deprecated and scheduled for removal in 1\.0\.0\.$"):
            deprecation_warn(obj_name="test", removal_version="1.0.0")


def test_deprecation_decorator_warn(monkeypatch: pytest.MonkeyPatch):
    """Check deprecated decorator triggers a deprecation warning."""
    _patch_project_version(monkeypatch, "1.0.0")

    @deprecated(display_name="func", removal_version="1.0.1")
    def func(x: object) -> object:
        return x

    with pytest.deprecated_call(match=r"^func is deprecated and scheduled for removal in 1\.0\.1\.$"):
        assert func(5) == 5


def test_deprecation_decorator_inferred_name(monkeypatch: pytest.MonkeyPatch):
    """Check deprecated decorator properly infers qualified name of decorated object shown in warning."""
    _patch_project_version(monkeypatch, "1.0.0")

    @deprecated(removal_version="1.0.1")
    def func(x: object) -> object:
        return x

    qualname = r"test_deprecation_decorator_inferred_name\.<locals>\.func"
    with pytest.deprecated_call(match=rf"^{qualname} is deprecated and scheduled for removal in 1\.0\.1\.$"):
        assert func(5) == 5


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.2.3", (1, 2, 3)),
        ("0.0.1", (0, 0, 1)),
        ("1.0.0", (1, 0, 0)),
        ("10.20.30", (10, 20, 30)),
        ("1.2.3rc1", (1, 2, 3)),
        ("1.2.3-rc1", (1, 2, 3)),
        ("1.2.3.post1", (1, 2, 3)),
        ("1.2.3-1", (1, 2, 3)),
        ("1.2.3.dev4", (1, 2, 3)),
        ("1.2.3+local", (1, 2, 3)),
        ("1.2.3rc1.post2.dev3+loc.1", (1, 2, 3)),
    ],
)
def test_project_version_non_normalized_parsing(monkeypatch: pytest.MonkeyPatch, version: str, expected: tuple[int, int, int]):
    """Ensure PEP440 release versions get parsed out properly, with non-release components are ignored."""
    _patch_project_version(monkeypatch, version)

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # raise warnings as errors (test there are no warnings)

        assert _get_project_version() == expected


@pytest.mark.parametrize(
    ("version", "expected", "warning"),
    [
        (
            "1.2",
            (1, 2, 0),
            f"{LIB_NAME} version '1.2' has less than 3 release components; remaining components will become zeroes",
        ),
        (
            "1.2.3.4",
            (1, 2, 3),
            f"{LIB_NAME} version '1.2.3.4' has more than 3 release components; extra components are ignored",
        ),
    ],
    ids=["1.2", "1.2.3.4"],
)
def test_project_version_normalizes_release_components(
    monkeypatch: pytest.MonkeyPatch,
    version: str,
    expected: tuple[int, int, int],
    warning: str,
):
    """Ensure release segments normalize to a 3-component version and warn."""
    _patch_project_version(monkeypatch, version)

    with pytest.warns(RuntimeWarning, match=rf"^{re.escape(warning)}$"):
        assert _get_project_version() == expected
