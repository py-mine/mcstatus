from __future__ import annotations

import functools
import importlib.metadata
import re
import warnings
from functools import wraps
from typing import ParamSpec, Protocol, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["deprecated", "deprecation_warn"]

LIB_NAME = "mcstatus"

# This comes from the python packaging docs (PEP 440 compliant versioning):
# https://packaging.python.org/en/latest/specifications/version-specifiers/#appendix-parsing-version-strings-with-regular-expressions
VERSION_PATTERN_FULL = re.compile(
    r"""^\s*
    v?
    (?:
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
    \s*$""",
    re.VERBOSE | re.IGNORECASE,
)
# Intentionally restricted to X.Y.Z, unlike PEP 440 release segments.
# Used only for user-supplied removal_version values parsing.
REMOVAL_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")

P = ParamSpec("P")
R = TypeVar("R")


@functools.lru_cache(maxsize=1)
def _get_project_version() -> tuple[int, int, int]:
    """Return the installed project version normalized to a 3-part release tuple.

    The project version is obtained from :mod:`importlib.metadata` and parsed using the official PEP 440
    version parsing regular expression.

    All non-release components of the version (pre-releases, post-releases, development releases, and local
    version identifiers) are intentionally ignored. The release version segment of the version is then
    normalized to 3 components, padding with zeros if the actual version has less components, or truncating
    if it has more. Any performed normalizing will emit a :exc:`RuntimeWarning`.

    If the project version cannot be determined or parsed, ``(0, 0, 0)`` is returned and a runtime warning
    is emitted.
    """
    try:
        _project_version = importlib.metadata.version(LIB_NAME)
    except importlib.metadata.PackageNotFoundError:
        # v0.0.0 will never mark things as already deprecated (removal_version will always be newer)
        warnings.warn(f"Failed to get {LIB_NAME} project version, assuming v0.0.0", category=RuntimeWarning, stacklevel=1)
        return (0, 0, 0)

    m = VERSION_PATTERN_FULL.fullmatch(_project_version)
    if m is None:
        # This should never happen
        warnings.warn(
            f"Failed to parse {LIB_NAME} project version ({_project_version}), assuming v0.0.0",
            category=RuntimeWarning,
            stacklevel=1,
        )
        return (0, 0, 0)

    if m["epoch"] is not None:
        # we're not using epoch, and we don't expect to start doing so. If we do, the rest of this
        # implementation would likely need to be changed anyways. Generally, this should never happen.
        warnings.warn(f"Failed to parse {LIB_NAME} project version, assuming v0.0.0", category=RuntimeWarning, stacklevel=1)
        return (0, 0, 0)

    release = m["release"]
    nums = [int(p) for p in release.split(".")]

    if len(nums) < 3:
        warnings.warn(
            f"{LIB_NAME} version '{release}' has less than 3 release components; remaining components will become zeroes",
            category=RuntimeWarning,
            stacklevel=2,
        )
        nums.extend([0] * (3 - len(nums)))
    elif len(nums) > 3:
        warnings.warn(
            f"{LIB_NAME} version '{release}' has more than 3 release components; extra components are ignored",
            category=RuntimeWarning,
            stacklevel=2,
        )
        nums = nums[:3]

    return nums[0], nums[1], nums[2]


def deprecation_warn(
    *,
    obj_name: str,
    removal_version: str | tuple[int, int, int],
    replacement: str | None = None,
    extra_msg: str | None = None,
    stack_level: int = 2,
) -> None:
    """Produce an appropriate deprecation warning given the parameters.

    If the currently installed project version is already past the specified deprecation version,
    a :exc:`DeprecationWarning` will be raised as a full exception. Otherwise it will just get
    emitted as a warning.

    The deprecation message used will be constructed dynamically based on the input parameters.

    :param obj_name: Name of the object that got deprecated (such as ``my_function``).
    :param removal_version: Version at which this object should be considered as deprecated and should no longer be used.
    :param replacement: A new alternative to this (now deprecated) object.
    :param extra_msg: Additional message included in the deprecation warning/exception at the end.
    :param stack_level: Stack level at which the warning is emitted.

    .. note:
        If the project version contains any additional qualifiers (e.g. pre-release, post-release, dev/local versions),
        they will be ignored and the project version will be treated a simple stable (major, minor, micro) version.
    """
    if isinstance(removal_version, str):
        if m := REMOVAL_VERSION_RE.fullmatch(removal_version):
            removal_version = (int(m[1]), int(m[2]), int(m[3]))
        else:
            raise ValueError(f"removal_version must follow regex pattern of: {REMOVAL_VERSION_RE!r}")

    project_version = _get_project_version()
    already_deprecated = project_version >= removal_version

    msg = f"{obj_name}"
    removal_version_str = ".".join(str(num) for num in removal_version)
    if already_deprecated:
        msg += f" is passed its removal version ({removal_version_str})"
    else:
        msg += f" is deprecated and scheduled for removal in {removal_version_str}"

    if replacement is not None:
        msg += f", use {replacement} instead"

    msg += "."
    if extra_msg is not None:
        msg += f" ({extra_msg})"

    if already_deprecated:
        raise DeprecationWarning(msg)

    warnings.warn(msg, category=DeprecationWarning, stacklevel=stack_level)


class DecoratorFunction(Protocol):
    def __call__(self, /, func: Callable[P, R]) -> Callable[P, R]: ...


def deprecated(
    removal_version: str | tuple[int, int, int],
    display_name: str | None = None,
    replacement: str | None = None,
    extra_msg: str | None = None,
) -> DecoratorFunction:
    """Mark an object as deprecated.

    Decorator version of :func:`deprecation_warn` function.

    If the currently installed project version is already past the specified deprecation version,
    a :exc:`DeprecationWarning` will be raised as a full exception. Otherwise it will just get
    emitted as a warning.

    The deprecation message used will be constructed based on the input parameters.

    :param display_name:
            Name of the object that got deprecated (such as `my_function`).

            By default, the object name is obtained automatically from ``__qualname__`` (falling back
            to ``__name__``) of the decorated object. Setting this explicitly will override this obtained
            name and the `display_name` will be used instead.
    :param removal_version: Version at which this object should be considered as deprecated and should no longer be used.
    :param replacement: A new alternative to this (now deprecated) object.
    :param extra_msg: Additional message included in the deprecation warning/exception at the end.

    .. note:
        If the project version contains any additional qualifiers (e.g. pre-release, post-release, dev/local versions),
        they will be ignored and the project version will be treated a simple stable (major, minor, micro) version.
    """

    def inner(func: Callable[P, R]) -> Callable[P, R]:
        obj_name = getattr(func, "__qualname__", func.__name__) if display_name is None else display_name

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            deprecation_warn(
                obj_name=obj_name,
                removal_version=removal_version,
                replacement=replacement,
                extra_msg=extra_msg,
                stack_level=3,
            )
            return func(*args, **kwargs)

        return wrapper

    return inner
