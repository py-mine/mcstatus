import asyncio
from abc import ABC
from typing import Any, cast, final


class McstatusError(Exception, ABC):
    """Base exception class for any mcstatus managed errors.

    This exception base class is never raised directly, it is only used to define further
    exception classes within mcstatus.
    """

    def __init__(self, msg: str) -> None:
        self.msg: str = msg
        super().__init__(self.msg)


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
