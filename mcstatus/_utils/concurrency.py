from __future__ import annotations

import asyncio
import contextlib
import queue
import threading
from typing import Any, TYPE_CHECKING, TypeVar, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Sequence

__all__ = ["async_first_success", "first_success", "primary_error"]

T = TypeVar("T")


def primary_error(errors: Sequence[Exception]) -> Exception:
    """Return the first error, annotated with notes for remaining errors."""
    primary = errors[0]
    for other in errors[1:]:
        primary.add_note(f"Other Bedrock transport also failed: {other!r}")
    return primary


def first_success(funcs: Sequence[Callable[[], T]]) -> T:
    """Run ``funcs`` concurrently and return the first result that doesn't raise.

    Workers are daemon threads: a losing transport still blocked on I/O will not delay
    interpreter shutdown. If every function fails, the first function's exception is raised.
    """
    if len(funcs) == 1:
        return funcs[0]()

    outcomes: queue.SimpleQueue[tuple[int, T | None, BaseException | None]] = queue.SimpleQueue()

    def run(index: int, func: Callable[[], T]) -> None:
        try:
            outcomes.put((index, func(), None))
        except BaseException as exc:  # ruff: ignore[blind-except]
            outcomes.put((index, None, exc))

    for index, func in enumerate(funcs):
        threading.Thread(target=run, args=(index, func), name=f"mcstatus-bedrock-{index}", daemon=True).start()

    errors: dict[int, Exception] = {}
    for _ in funcs:
        index, result, exc = outcomes.get()
        if exc is None:
            return cast("T", result)
        if not isinstance(exc, Exception):
            raise exc
        errors[index] = exc

    raise primary_error([errors[i] for i in range(len(funcs))])


async def async_first_success(coros: Sequence[Coroutine[Any, Any, T]]) -> T:
    """Run ``coros`` concurrently and return the first result that doesn't raise.

    Remaining tasks are cancelled and awaited once a result is available (or if all fail).
    If every coroutine fails, the exception raised by the first coroutine in ``coros`` is re-raised.
    """
    if len(coros) == 1:
        return await coros[0]

    tasks = [asyncio.ensure_future(coro) for coro in coros]
    try:
        for next_done in asyncio.as_completed(tasks):
            with contextlib.suppress(Exception):
                return await next_done
        raise primary_error([cast("Exception", task.exception()) for task in tasks])
    finally:
        for task in tasks:
            _ = task.cancel()
        _ = await asyncio.gather(*tasks, return_exceptions=True)
