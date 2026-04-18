from __future__ import annotations

import asyncio
from typing import Any, ParamSpec, TYPE_CHECKING, TypeVar, final

from mcstatus._protocol.io.buffer import Buffer
from mcstatus._protocol.io.connection import BaseAsyncConnection, BaseSyncConnection

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from typing_extensions import override
else:
    override = lambda f: f  # noqa: E731

P = ParamSpec("P")
T = TypeVar("T")


def async_decorator(f: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    """Wrap an async callable so it can be invoked from synchronous tests."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        """Execute the wrapped coroutine function using ``asyncio.run``."""
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@final
class SyncBufferConnection(BaseSyncConnection):
    """In-memory synchronous stream-style transport used by protocol tests."""

    def __init__(self, incoming: bytes | bytearray = b"") -> None:
        """Initialize in-memory read/write buffers with optional incoming bytes."""
        self.sent = Buffer()
        self.received = Buffer(incoming)

    @override
    def read(self, length: int, /) -> bytes:
        """Read ``length`` bytes from the queued incoming data."""
        return self.received.read(length)

    @override
    def write(self, data: bytes | bytearray, /) -> None:
        """Append outgoing payload data to the send buffer."""
        self.sent.write(data)

    def receive(self, data: bytes | bytearray) -> None:
        """Queue incoming payload data for subsequent reads."""
        self.received.write(data)

    def remaining(self) -> int:
        """Return unread byte count from the incoming buffer."""
        return self.received.remaining

    def flush(self) -> bytes:
        """Return and clear all bytes written to the send buffer."""
        return self.sent.flush()


@final
class AsyncBufferConnection(BaseAsyncConnection):
    """In-memory asynchronous stream-style transport used by protocol tests."""

    def __init__(self, incoming: bytes | bytearray = b"") -> None:
        """Initialize in-memory read/write buffers with optional incoming bytes."""
        self.sent = Buffer()
        self.received = Buffer(incoming)

    @override
    async def read(self, length: int, /) -> bytes:
        """Read ``length`` bytes from the queued incoming data."""
        return self.received.read(length)

    @override
    async def write(self, data: bytes | bytearray, /) -> None:
        """Append outgoing payload data to the send buffer."""
        self.sent.write(data)

    def receive(self, data: bytes | bytearray) -> None:
        """Queue incoming payload data for subsequent reads."""
        self.received.write(data)

    def remaining(self) -> int:
        """Return unread byte count from the incoming buffer."""
        return self.received.remaining

    def flush(self) -> bytes:
        """Return and clear all bytes written to the send buffer."""
        return self.sent.flush()


@final
class SyncDatagramConnection(BaseSyncConnection):
    """Datagram-like synchronous transport returning one queued packet per read."""

    def __init__(self) -> None:
        self.sent = Buffer()
        self.received: list[bytes] = []

    @override
    def read(self, _length: int, /) -> bytes:
        """Pop and return the next queued datagram payload."""
        if not self.received:
            raise OSError("No datagram data to read.")
        return self.received.pop(0)

    @override
    def write(self, data: bytes | bytearray, /) -> None:
        """Append outgoing datagram payload to the send buffer."""
        self.sent.write(data)

    def receive(self, data: bytes | bytearray) -> None:
        """Queue one incoming datagram payload for future reads."""
        self.received.append(bytes(data))

    def remaining(self) -> int:
        """Return size of the next queued datagram, or ``0`` when empty."""
        if not self.received:
            return 0
        return len(self.received[0])

    def flush(self) -> bytes:
        """Return and clear all bytes written to the send buffer."""
        return self.sent.flush()


@final
class AsyncDatagramConnection(BaseAsyncConnection):
    """Datagram-like asynchronous transport returning one queued packet per read."""

    def __init__(self) -> None:
        self.sent = Buffer()
        self.received: list[bytes] = []

    @override
    async def read(self, _length: int, /) -> bytes:
        """Pop and return the next queued datagram payload."""
        if not self.received:
            raise OSError("No datagram data to read.")
        return self.received.pop(0)

    @override
    async def write(self, data: bytes | bytearray, /) -> None:
        """Append outgoing datagram payload to the send buffer."""
        self.sent.write(data)

    def receive(self, data: bytes | bytearray) -> None:
        """Queue one incoming datagram payload for future reads."""
        self.received.append(bytes(data))

    def remaining(self) -> int:
        """Return size of the next queued datagram, or ``0`` when empty."""
        if not self.received:
            return 0
        return len(self.received[0])

    def flush(self) -> bytes:
        """Return and clear all bytes written to the send buffer."""
        return self.sent.flush()
