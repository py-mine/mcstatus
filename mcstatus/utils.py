from __future__ import annotations

import asyncio
import inspect
import warnings
from functools import wraps
from typing import Callable, Iterable, Optional, TYPE_CHECKING, Tuple, Type, TypeVar, Union, cast, overload

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, Protocol

    P = ParamSpec("P")
    P2 = ParamSpec("P2")
else:
    Protocol = object
    P = []

T = TypeVar("T")
R = TypeVar("R")
R2 = TypeVar("R2")


def retry(tries: int, exceptions: Tuple[Type[BaseException]] = (Exception,)) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that re-runs given function tries times if error occurs.

    The amount of tries will either be the value given to the decorator,
    or if tries is present in keyword arguments on function call, this
    specified value will take precedense.

    If the function fails even after all of the retries, raise the last
    exception that the function raised (even if the previous failures caused
    a different exception, this will only raise the last one!).
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
            else:
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
            else:
                raise last_exc  # type: ignore # (This won't actually be unbound)

        # We cast here since pythons typing doesn't support adding keyword-only arguments to signature
        # (Support for this was a rejected idea https://peps.python.org/pep-0612/#concatenating-keyword-parameters)
        if asyncio.iscoroutinefunction(func):
            return cast("Callable[P, R]", async_wrapper)
        return cast("Callable[P, R]", sync_wrapper)

    return decorate


class DeprecatedReturn(Protocol):
    @overload
    def __call__(self, __x: Type[T]) -> Type[T]:
        ...

    @overload
    def __call__(self, __x: Callable[P, R]) -> Callable[P, R]:
        ...


@overload
def deprecated(
    obj: Callable[P, R],
    *,
    replacement: Optional[str] = None,
    version: Optional[str] = None,
    date: Optional[str] = None,
    msg: Optional[str] = None,
) -> Callable[P, R]:
    ...


@overload
def deprecated(
    obj: Type[T],
    *,
    replacement: Optional[str] = None,
    version: Optional[str] = None,
    date: Optional[str] = None,
    msg: Optional[str] = None,
    methods: Iterable[str],
) -> Type[T]:
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
) -> DeprecatedReturn:
    ...


def deprecated(
    obj: Optional[Union[Callable, Type[object]]] = None,
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
            warnings.warn(warn_message, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    @overload
    def decorate(obj: Callable[P, R]) -> Callable[P, R]:
        ...

    @overload
    def decorate(obj: Type[T]) -> Type[T]:
        ...

    def decorate(obj: Union[Callable[P, R], Type[T]]) -> Union[Callable[P, R], Type[T]]:
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
            obj = cast(Type[T], obj)

            if methods is None:
                raise ValueError("When deprecating a class, you need to specify 'methods' which will get the notice")

            for method in methods:
                new_func = decorate_func(getattr(obj, method), warn_message)
                setattr(obj, method, new_func)

            return obj

        # Regular function deprecation
        obj = cast(Callable[P, R], obj)
        if methods is not None:
            raise ValueError("Methods can only be specified when decorating a class, not a function")
        return decorate_func(obj, warn_message)

    # In case the decorator was used like @deprecated, instead of @deprecated()
    # we got the object already, pass it over to the local decorate function
    # This can happen since all of the arguments are optional and can be omitted
    if obj:
        return decorate(obj)
    return decorate
