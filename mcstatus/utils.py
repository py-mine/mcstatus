from __future__ import annotations

import asyncio
import inspect
import warnings
from functools import wraps
from typing import Callable, Iterable, Optional, TYPE_CHECKING, Tuple, Type, TypeVar, overload

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    P = ParamSpec("P")
    P2 = ParamSpec("P2")

R = TypeVar("R")
R2 = TypeVar("R2")


def retry(tries: int, exceptions: Tuple[Type[BaseException]] = (Exception,)) -> Callable:
    """
    Decorator that re-runs given function tries times if error occurs.

    The amount of tries will either be the value given to the decorator,
    or if tries is present in keyword arguments on function call, this
    specified value will take precedense.

    If the function fails even after all of the retries, raise the last
    exception that the function raised (even if the previous failures caused
    a different exception, this will only raise the last one!).
    """

    def decorate(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, tries: int = tries, **kwargs):
            last_exc: BaseException
            for _ in range(tries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
            else:
                raise last_exc  # type: ignore # (This won't actually be unbound)

        @wraps(func)
        def sync_wrapper(*args, tries: int = tries, **kwargs):
            last_exc: BaseException
            for _ in range(tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
            else:
                raise last_exc  # type: ignore # (This won't actually be unbound)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorate


@overload
def deprecated(
    obj: Callable[P, R],
    *,
    replacement: Optional[str] = None,
    version: Optional[str] = None,
    date: Optional[str] = None,
    msg: Optional[str] = None,
    methods: Optional[Iterable[str]] = None,
) -> Callable[P, R]:
    ...


@overload
def deprecated(
    obj: None = None,
    *,
    replacement: Optional[str] = None,
    version: Optional[str] = None,
    date: Optional[str] = None,
    msg: Optional[str] = None,
    methods: Optional[Iterable[str]] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    ...


def deprecated(
    obj: Optional[Callable] = None,
    *,
    replacement: Optional[str] = None,
    version: Optional[str] = None,
    date: Optional[str] = None,
    msg: Optional[str] = None,
    methods: Optional[Iterable[str]] = None,
) -> Callable:
    if date is not None and version is not None:
        raise ValueError("Expected removal timeframe can either be a date, or a version, not both.")

    def decorate_func(func: Callable[P2, R2], warn_message: str) -> Callable[P2, R2]:
        @wraps(func)
        def wrapper(*args: P2.args, **kwargs: P2.kwargs) -> R2:
            warnings.simplefilter("always", DeprecationWarning)
            warnings.warn(warn_message, category=DeprecationWarning)
            warnings.simplefilter("default", DeprecationWarning)
            return func(*args, **kwargs)

        return wrapper

    def decorate(obj: Callable[P, R]) -> Callable[P, R]:
        # Construct and send the warning message
        name = getattr(obj, "__qualname__", obj.__name__)
        warn_message = f"'{name}' is deprecated and is expected to be removed"
        if version is not None:
            warn_message += f" in {version}"
        elif date is not None:
            warn_message += f" on {date}"
        else:
            warn_message += " eventually"
        if replacement is not None:
            warn_message += f", use '{replacement}' instead"
        warn_message += "."
        if msg is not None:
            warn_message += f" ({msg})"

        # If we're deprecating class, deprecate it's methods and return the class
        if inspect.isclass(obj):
            if methods is None:
                raise ValueError("When deprecating a class, you need to specify 'methods' which will get the notice")

            for method in methods:
                new_func = decorate_func(getattr(obj, method), warn_message)
                setattr(obj, method, new_func)

            return obj

        # Regular function deprecation
        if methods is not None:
            raise ValueError("Methods can only be specified when decorating a class, not a function")
        return decorate_func(obj, warn_message)

    # In case the decorator was used like @deprecated, instead of @deprecated()
    # we got the object already, pass it over to the local decorate function
    # This can happen since all of the arguments are optional and can be omitted
    if obj:
        return decorate(obj)
    return decorate
