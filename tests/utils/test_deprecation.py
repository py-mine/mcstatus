from __future__ import annotations

import re
import warnings

import pytest

from mcstatus._utils.deprecation import _get_project_version, deprecated, deprecation_warn
from tests.helpers import patch_project_version

LIB_NAME = "mcstatus"


def test_invalid_lib_version():
    with (
        patch_project_version("foo bar"),
        pytest.warns(match=f"^Failed to parse {LIB_NAME} project version \\(foo bar\\), assuming v0\\.0\\.0$"),
    ):
        _get_project_version()


def test_epoch_in_lib_version():
    with (
        patch_project_version("2!1.2.3"),
        pytest.warns(
            match=f"^Failed to parse {LIB_NAME} project version, assuming v0\\.0\\.0$",
        ),
    ):
        _get_project_version()


@pytest.mark.parametrize("removal_version", ["0.9.0", (0, 9, 0)])
def test_deprecation_warn_produces_error(removal_version: str | tuple[int, int, int]):
    """Test deprecation_warn with older removal_version than current version produces exception."""
    with (
        patch_project_version("1.0.0"),
        pytest.raises(
            DeprecationWarning,
            match=r"^test is passed its removal version \(0\.9\.0\)\.$",
        ),
    ):
        deprecation_warn(obj_name="test", removal_version=removal_version)


@pytest.mark.parametrize("removal_version", ["1.0.1", (1, 0, 1)])
def test_deprecation_warn_produces_warning(removal_version: str | tuple[int, int, int]):
    """Test deprecation_warn with newer removal_version than current version produces warning."""
    with (
        patch_project_version("1.0.0"),
        pytest.deprecated_call(
            match=r"^test is deprecated and scheduled for removal in 1\.0\.1\.$",
        ),
    ):
        deprecation_warn(obj_name="test", removal_version=removal_version)


def test_deprecation_invalid_removal_version():
    """Test deprecation_warn with invalid removal_version."""
    pattern = re.escape(r"(\d+)\.(\d+)\.(\d+)")
    with (
        patch_project_version("1.0.0"),
        pytest.raises(
            ValueError,
            match=f"^removal_version must follow regex pattern of: {pattern}$",
        ),
    ):
        deprecation_warn(obj_name="test", removal_version="foo!")


def test_deprecation_warn_unknown_version():
    """Test deprecation_warn with unknown project version.

    This could occur if the project wasn't installed as a package. (e.g. when running directly from
    source, like via a git submodule.)
    """
    with (
        patch_project_version(None),
        pytest.warns(match=f"Failed to get {LIB_NAME} project version", expected_warning=RuntimeWarning),
        pytest.deprecated_call(match=r"^test is deprecated and scheduled for removal in 1\.0\.0\.$"),
    ):
        deprecation_warn(obj_name="test", removal_version="1.0.0")


def test_deprecation_decorator_warn():
    """Check deprecated decorator triggers a deprecation warning."""
    with patch_project_version("1.0.0"):

        @deprecated(display_name="func", removal_version="1.0.1")
        def func(x: object) -> object:
            """Return input value.

            .. deprecated:: 0.0.1
            """
            return x

        with pytest.deprecated_call(match=r"^func is deprecated and scheduled for removal in 1\.0\.1\.$"):
            assert func(5) == 5


def test_deprecation_decorator_inferred_name():
    """Check deprecated decorator properly infers qualified name of decorated object shown in warning."""
    with patch_project_version("1.0.0"):

        @deprecated(removal_version="1.0.1")
        def func(x: object) -> object:
            """Return input value.

            .. deprecated:: 0.0.1
            """
            return x

        qualname = r"test_deprecation_decorator_inferred_name\.<locals>\.func"
        with pytest.deprecated_call(match=rf"^{qualname} is deprecated and scheduled for removal in 1\.0\.1\.$"):
            assert func(5) == 5


def test_deprecation_decorator_missing_docstring_directive():
    """Check deprecated decorator validates a docstring contains a deprecation directive."""
    with (
        patch_project_version("1.0.0"),
        pytest.raises(
            ValueError,
            match=r"^Deprecated object does not contain '\.\. deprecated::' sphinx directive in its docstring$",
        ),
    ):

        @deprecated(display_name="func", removal_version="1.0.1")
        def func(x: object) -> object:
            return x


def test_deprecation_decorator_no_docstring_check_opt_out():
    """Check deprecated decorator can skip docstring validation when requested."""
    with patch_project_version("1.0.0"):

        @deprecated(display_name="func", removal_version="1.0.1", no_docstring_check=True)
        def func(x: object) -> object:
            return x

        with pytest.deprecated_call(match=r"^func is deprecated and scheduled for removal in 1\.0\.1\.$"):
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
def test_project_version_non_normalized_parsing(version: str, expected: tuple[int, int, int]):
    """Ensure PEP440 release versions get parsed out properly, with non-release components are ignored."""
    with patch_project_version(version), warnings.catch_warnings():
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
    version: str,
    expected: tuple[int, int, int],
    warning: str,
):
    """Ensure release segments normalize to a 3-component version and warn."""
    with patch_project_version(version), pytest.warns(RuntimeWarning, match=rf"^{re.escape(warning)}$"):
        assert _get_project_version() == expected
