from __future__ import annotations

import inspect
from functools import wraps
from typing import ParamSpec, TYPE_CHECKING, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["retry"]

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")
P2 = ParamSpec("P2")


def retry(tries: int, exceptions: tuple[type[BaseException]] = (Exception,)) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that re-runs given function ``tries`` times if error occurs.

    The amount of tries will either be the value given to the decorator,
    or if tries is present in keyword arguments on function call, this
    specified value will take precedence.

    If the function fails even after all the retries, raise the last
    exception that the function raised.

    .. note::
        Even if the previous failures caused a different exception, this will only raise the last one.
    """

    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def async_wrapper(
            *args: P.args,
            tries: int = tries,  # type: ignore # (No support for adding kw-only args)
            **kwargs: P.kwargs,
        ) -> R:
            last_exc: BaseException
            for _ in range(tries):
                try:
                    return await func(*args, **kwargs)  # type: ignore # (We know func is awaitable here)
                except exceptions as exc:
                    last_exc = exc
            raise last_exc  # type: ignore # (This won't actually be unbound)

        @wraps(func)
        def sync_wrapper(
            *args: P.args,
            tries: int = tries,  # type: ignore # (No support for adding kw-only args)
            **kwargs: P.kwargs,
        ) -> R:
            last_exc: BaseException
            for _ in range(tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
            raise last_exc  # type: ignore # (This won't actually be unbound)

        # We cast here since pythons typing doesn't support adding keyword-only arguments to signature
        # (Support for this was a rejected idea https://peps.python.org/pep-0612/#concatenating-keyword-parameters)
        if inspect.iscoroutinefunction(func):
            return cast("Callable[P, R]", async_wrapper)
        return cast("Callable[P, R]", sync_wrapper)

    return decorate
