from __future__ import annotations

import importlib.metadata
import warnings
from collections.abc import Callable
from functools import wraps
from packaging.version import Version
from typing import TypeVar, ParamSpec, Protocol

__all__ = ["deprecated", "deprecation_warn"]

LIB_NAME = "mcstatus"
P = ParamSpec("P")
R = TypeVar("R")


def deprecation_warn(
    *,
    obj_name: str,
    removal_version: str | Version,
    replacement: str | None = None,
    extra_msg: str | None = None,
    stack_level: int = 2,
) -> None:
    """Produce an appropriate deprecation warning given the parameters.

    If the currently installed project version is already past the specified deprecation version,
    a :exc:`DeprecationWarning` will be raised as a full exception. Otherwise it will just get
    emitted as a warning.

    The deprecation message used will be constructed dynamically based on the input parameters.

    Args:
        obj_name: Name of the object that got deprecated (such as ``my_function``).
        removal_version:
            Version at which this object should be considered as deprecated and should no longer be used.
        replacement: A new alternative to this (now deprecated) object.
        extra_msg: Additional message included in the deprecation warning/exception at the end.
        stack_level: Stack level at which the warning is emitted.
    """
    if isinstance(removal_version, str):
        removal_version = Version(removal_version)

    try:
        _project_version = importlib.metadata.version(LIB_NAME)
    except importlib.metadata.PackageNotFoundError:
        # v0.0.0 will never mark things as already deprecated (removal_version will always be newer)
        warnings.warn(f"Failed to get {LIB_NAME} project version, assuming v0.0.0", category=RuntimeWarning, stacklevel=1)
        project_version = Version("0.0.0")
    else:
        project_version = Version(_project_version)

    already_deprecated = project_version >= removal_version

    msg = f"{obj_name}"
    if already_deprecated:
        msg += f" is passed its removal version ({removal_version})"
    else:
        msg += f" is deprecated and scheduled for removal in {removal_version}"

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
    removal_version: str | Version,
    display_name: str | None = None,
    replacement: str | None = None,
    extra_msg: str | None = None,
) -> DecoratorFunction:
    """Mark an object as deprecated.

    Decorator version of :func:`deprecation_warn`] function.

    If the currently installed project version is already past the specified deprecation version,
    a :exc:`DeprecationWarning` will be raised as a full exception. Otherwise it will just get
    emitted as a warning.

    The deprecation message used will be constructed based on the input parameters.

    Args:
        display_name:
            Name of the object that got deprecated (such as `my_function`).

            By default, the object name is obtained automatically from ``__qualname__`` (falling back
            to ``__name__``) of the decorated object. Setting this explicitly will override this obtained
            name and the `display_name` will be used instead.
        removal_version:
            Version at which this object should be considered as deprecated and should no longer be used.
        replacement: A new alternative to this (now deprecated) object.
        extra_msg: Additional message included in the deprecation warning/exception at the end.
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
