from __future__ import annotations

import asyncio
import queue
import threading
from typing import Any, TYPE_CHECKING, TypeVar, cast, final

from mcstatus.exceptions import McstatusError

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Sequence

__all__ = ["async_first_success", "first_success"]

T = TypeVar("T")


@final
class ChildCancelledError(McstatusError):
    """Raised as a result of handling a managed child asyncio Task being cancelled.

    This exception is used in some of our concurrency helpers that directly manage asyncio tasks, signalling
    that a managed task was cancelled (e.g. that it raised an :exc:`asyncio.CancelledError`). We use it to
    distinguish a child task getting cancelled from the main concurrency handler function getting cancelled,
    and to avoid the need for a ``BaseException`` level handling that ``asyncio.CancelledError`` normally
    requires.
    """

    def __init__(self, *, task: asyncio.Task[Any], exc: asyncio.CancelledError, msg: str | None = None) -> None:
        self.task = task
        self.__cause__ = exc

        if msg is None:
            msg = f"Child async Task: {task!r} failed with {exc!r}"

        super().__init__(msg)

    @property
    def exc(self) -> asyncio.CancelledError:
        """The underlying :exc:`asyncio.CancelledError` exception."""
        return cast("asyncio.CancelledError", self.__cause__)


def first_success(funcs: Sequence[Callable[[], T]], *, thread_name_prefix: str = "mcstatus-worker") -> T:
    """Run ``funcs`` concurrently and return the first result that doesn't raise.

    Workers are daemon threads: Python OS threads blocked on synchronous socket I/O cannot
    be cancelled externally from user space, so daemon status and socket timeouts ensure blocked
    threads terminate without delaying interpreter shutdown.

    If every function fails, an :exc:`ExceptionGroup` containing all errors is raised. The
    order of exceptions in the group is guaranteed to match the input sequence order of ``funcs``.
    """
    if len(funcs) == 0:
        raise ValueError("At least one function is required")

    if len(funcs) == 1:
        return funcs[0]()

    outcomes: queue.SimpleQueue[tuple[int, T | None, BaseException | None]] = queue.SimpleQueue()

    def run(index: int, func: Callable[[], T]) -> None:
        try:
            outcomes.put((index, func(), None))
        except BaseException as exc:  # ruff: ignore[blind-except]
            outcomes.put((index, None, exc))

    for idx, func in enumerate(funcs):
        threading.Thread(target=run, args=(idx, func), name=f"{thread_name_prefix}-{idx}", daemon=True).start()

    errors: dict[int, Exception] = {}
    for _ in funcs:
        idx, result, exc = outcomes.get()
        if exc is None:
            return cast("T", result)
        if not isinstance(exc, Exception):
            raise exc
        errors[idx] = exc

    raise ExceptionGroup("All concurrent operations failed", [errors[i] for i in range(len(funcs))])


async def async_first_success(coros: Sequence[Coroutine[Any, Any, T]], *, task_name_prefix: str = "mcstatus-task") -> T:
    """Run ``coros`` concurrently and return the first result that doesn't raise.

    The coroutines are scheduled concurrently by being converted into tasks and waited
    for. The first successful result observed is returned, and any remaining tasks are
    cancelled and completed (awaited).

    If some coroutines fail but at least one returns successfully, these failures will be
    discarded and the successful result will be returned. If several coroutines finish
    successfully at the same (or nearly the same) time, any of their results will be
    returned arbitrarily.

    If every coroutine fails, an :exc:`ExceptionGroup` containing all failures in the same
    order as ``coros`` is raised. If only one coroutine was passed, its exception is
    propagated directly instead.

    A ``asyncio.CancelledError`` being raised inside of any of the passed coroutines will
    be represented as :exc:`ChildCancelledError`.
    """
    if len(coros) == 0:
        raise ValueError("At least one coroutine is required")

    tasks = [asyncio.create_task(coro, name=f"{task_name_prefix}-{idx}") for idx, coro in enumerate(coros)]
    tasks_pending = set(tasks)
    tasks_done: set[asyncio.Task[T]] = set()
    excs: dict[asyncio.Task[T], Exception] = {}

    try:
        while len(tasks_pending) > 0:
            # Multiple tasks may finish before asyncio.wait() resumes, even with
            # FIRST_COMPLETED. The returned set is unordered, so if several tasks
            # succeed in the same batch, we arbitrarily pick one of their results.
            tasks_done, tasks_pending = await asyncio.wait(tasks_pending, return_when=asyncio.FIRST_COMPLETED)

            for task in tasks_done:
                try:
                    return task.result()
                except Exception as exc:  # ruff: ignore[blind-except]
                    excs[task] = exc
                except asyncio.CancelledError as exc:
                    excs[task] = ChildCancelledError(task=task, exc=exc)
    finally:
        # Cleanup the remaining pending tasks here, regardless of success.
        #
        # Most commonly, this is entered after one of the tasks reached the return statement,
        # as it successfully finished before the others. In this case, we just need to cancel
        # the remaining tasks.
        #
        # This can also be entered if none of the tasks succeeded, in which case this basically
        # does nothing, since all the tasks were already finished and their results were already
        # consumed (as raised exceptions that we suppressed).
        #
        # Less commonly, there could have been an unhandled exception raised from the above
        # code. Most notably that would be `asyncio.CancelledError` from the await statement
        # in `asyncio.wait` call. Meaning this function itself (not one of the tasks) got
        # cancelled. It could however also trigger for other exceptions raised above, like
        # any BaseException (other than async cancellation) occurring in one of the tasks.
        #
        # Either way, we want to do cleanup here and cancel all the tasks we started, so they
        # don't keep running in the background once this function exits. We also consume their
        # results/exceptions to avoid 'never awaited' warnings.
        for task in tasks:
            _ = task.cancel()
        _ = await asyncio.gather(*tasks, return_exceptions=True)

    # If we're here, all tasks got finished, but we never reached return => all tasks failed.
    excs_ordered: list[Exception] = [excs[task] for task in tasks]

    if len(excs_ordered) == 1:
        raise excs_ordered[0]

    raise ExceptionGroup("All concurrent operations failed", excs_ordered)
