from __future__ import annotations

import asyncio
import errno
import socket
from ipaddress import ip_address
from typing import TYPE_CHECKING, TypeAlias, final

import asyncio_dgram

from mcstatus._protocol.io.base_io import BaseAsyncReader, BaseAsyncWriter, BaseSyncReader, BaseSyncWriter

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typing_extensions import Self, SupportsIndex, override

    from mcstatus._net.address import Address
else:
    override = lambda f: f  # noqa: E731

__all__ = [
    "BaseAsyncConnection",
    "BaseSyncConnection",
    "TCPAsyncSocketConnection",
    "TCPSocketConnection",
    "UDPAsyncSocketConnection",
    "UDPSocketConnection",
]

BytesConvertable: TypeAlias = "SupportsIndex | Iterable[SupportsIndex]"


class BaseSyncConnection(BaseSyncReader, BaseSyncWriter):
    """Base synchronous read and write class."""

    __slots__ = ()


class BaseAsyncConnection(BaseAsyncReader, BaseAsyncWriter):
    """Base asynchronous read and write class."""

    __slots__ = ()


class _SocketConnection(BaseSyncConnection):
    """Socket connection."""

    __slots__ = ("socket",)

    def __init__(self) -> None:
        # These will only be None until connect is called, ignore the None type assignment
        self.socket: socket.socket = None  # pyright: ignore[reportAttributeAccessIssue]

    def close(self) -> None:
        """Close :attr:`.socket`."""
        if self.socket is not None:  # If initialized
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError as exception:  # Socket wasn't connected (nothing to shut down)
                if exception.errno != errno.ENOTCONN:
                    raise

            self.socket.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


@final
class TCPSocketConnection(_SocketConnection):
    """TCP Connection to address. Timeout defaults to 3 seconds."""

    __slots__ = ()

    def __init__(self, addr: tuple[str | None, int], timeout: float = 3) -> None:
        super().__init__()
        self.socket = socket.create_connection(addr, timeout=timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    @override
    def read(self, length: int, /) -> bytearray:
        """Return length bytes read from :attr:`.socket`. Raises :exc:`OSError` when server doesn't respond."""
        result = bytearray()
        while len(result) < length:
            new = self.socket.recv(length - len(result))
            if len(new) == 0:
                raise OSError("Server did not respond with any information!")
            result.extend(new)
        return result

    def write(self, data: str | bytes | bytearray, /) -> None:
        """Send data on :attr:`.socket`."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.socket.sendall(data)


@final
class UDPSocketConnection(_SocketConnection):
    """UDP Connection class."""

    __slots__ = ("addr",)

    def __init__(self, addr: Address, timeout: float = 3) -> None:
        super().__init__()
        self.addr = addr
        self.socket = socket.socket(
            socket.AF_INET if ip_address(addr[0]).version == 4 else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )
        self.socket.settimeout(timeout)

    def remaining(self) -> int:
        """Always return ``65535`` (``2 ** 16 - 1``)."""  # noqa: D401 # imperative mood
        return 65535

    @override
    def read(self, _length: int, /) -> bytearray:
        """Return up to :meth:`.remaining` bytes. Length does nothing here."""
        result = bytearray()
        while len(result) == 0:
            result.extend(self.socket.recvfrom(self.remaining())[0])
        return result

    @override
    def write(self, data: str | bytes | bytearray, /) -> None:
        """Use :attr:`.socket` to send data to :attr:`.addr`."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.socket.sendto(data, self.addr)


@final
class TCPAsyncSocketConnection(BaseAsyncConnection):
    """Asynchronous TCP Connection class."""

    __slots__ = ("_addr", "reader", "timeout", "writer")

    def __init__(self, addr: Address, timeout: float = 3) -> None:
        # These will only be None until connect is called, ignore the None type assignment
        self.reader: asyncio.StreamReader = None  # pyright: ignore[reportAttributeAccessIssue]
        self.writer: asyncio.StreamWriter = None  # pyright: ignore[reportAttributeAccessIssue]
        self.timeout: float = timeout
        self._addr = addr

    async def connect(self) -> None:
        """Use :mod:`asyncio` to open a connection to address. Timeout is in seconds."""
        conn = asyncio.open_connection(*self._addr)
        self.reader, self.writer = await asyncio.wait_for(conn, timeout=self.timeout)
        if self.writer is not None:  # it might be None in unittest
            sock: socket.socket = self.writer.transport.get_extra_info("socket")
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    @override
    async def read(self, length: int, /) -> bytearray:
        """Read up to ``length`` bytes from :attr:`.reader`."""
        result = bytearray()
        while len(result) < length:
            new = await asyncio.wait_for(self.reader.read(length - len(result)), timeout=self.timeout)
            if len(new) == 0:
                # No information at all
                if len(result) == 0:
                    raise OSError("Server did not respond with any information!")
                # We did get a few bytes, but we requested more
                raise OSError(
                    f"Server stopped responding (got {len(result)} bytes, but expected {length} bytes)."
                    f" Partial obtained data: {result!r}"
                )
            result.extend(new)
        return result

    @override
    async def write(self, data: str | bytes | bytearray, /) -> None:
        """Write data to :attr:`.writer`."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.writer.write(data)
        await self.writer.drain()

    async def close(self) -> None:
        """Close :attr:`.writer`."""
        if self.writer is not None:  # If initialized
            self.writer.close()
            await self.writer.wait_closed()

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()


@final
class UDPAsyncSocketConnection(BaseAsyncConnection):
    """Asynchronous UDP Connection class."""

    __slots__ = ("_addr", "stream", "timeout")

    def __init__(self, addr: Address, timeout: float = 3) -> None:
        # This will only be None until connect is called, ignore the None type assignment
        self.stream: asyncio_dgram.aio.DatagramClient = None  # pyright: ignore[reportAttributeAccessIssue]
        self.timeout: float = timeout
        self._addr = addr

    async def connect(self) -> None:
        """Connect to address. Timeout is in seconds."""
        conn = asyncio_dgram.connect(self._addr)
        self.stream = await asyncio.wait_for(conn, timeout=self.timeout)

    def remaining(self) -> int:
        """Always return ``65535`` (``2 ** 16 - 1``)."""  # noqa: D401 # imperative mood
        return 65535

    @override
    async def read(self, _length: int, /) -> bytearray:
        """Read from :attr:`.stream`. Length does nothing here."""
        data, _remote_addr = await asyncio.wait_for(self.stream.recv(), timeout=self.timeout)
        return bytearray(data)

    @override
    async def write(self, data: str | bytes | bytearray, /) -> None:
        """Send data with :attr:`.stream`."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        await self.stream.send(data)

    def close(self) -> None:
        """Close :attr:`.stream`."""
        if self.stream is not None:  # If initialized
            self.stream.close()

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        self.close()
