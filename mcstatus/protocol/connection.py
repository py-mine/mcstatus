from __future__ import annotations

import asyncio
import socket
import struct
from abc import ABC, abstractmethod
from collections.abc import Iterable
from ctypes import c_int32 as signed_int32
from ctypes import c_int64 as signed_int64
from ctypes import c_uint32 as unsigned_int32
from ctypes import c_uint64 as unsigned_int64
from ipaddress import ip_address
from typing import TYPE_CHECKING

import asyncio_dgram

from mcstatus.address import Address

if TYPE_CHECKING:
    from typing_extensions import SupportsIndex, TypeAlias

    BytesConvertable: TypeAlias = "SupportsIndex | Iterable[SupportsIndex]"


def ip_type(address: int | str) -> int | None:
    """Returns what version of IP a given address is."""
    try:
        return ip_address(address).version
    except ValueError:
        return None


class BaseWriteSync(ABC):
    """Base synchronous write class"""

    __slots__ = ()

    @abstractmethod
    def write(self, data: Connection | str | bytearray | bytes) -> None:
        """Write data to self."""
        ...

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__} Object>"

    @staticmethod
    def _pack(format_: str, data: int) -> bytes:
        """Pack data in with format in big-endian mode."""
        return struct.pack(">" + format_, data)

    def write_varint(self, value: int) -> None:
        """
        Write varint with value value to self.

        :param value: Max 2 ** 31 - 1, min -(2 ** 31).
        :raises ValueError: If value is out of range.
        """
        remaining = unsigned_int32(value).value
        for _ in range(5):
            if not remaining & -0x80:  # remaining & ~0x7F == 0:
                self.write(struct.pack("!B", remaining))
                if value > 2**31 - 1 or value < -(2**31):
                    break
                return
            self.write(struct.pack("!B", remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varint')

    def write_varlong(self, value: int) -> None:
        """
        Write varlong with value value to self.

        :param value: Max 2 ** 63 - 1, min -(2 ** 63).
        :raises ValueError: If value is out of range.
        """
        remaining = unsigned_int64(value).value
        for _ in range(10):
            if not remaining & -0x80:  # remaining & ~0x7F == 0:
                self.write(struct.pack("!B", remaining))
                if value > 2**63 - 1 or value < -(2**31):
                    break
                return
            self.write(struct.pack("!B", remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varlong')

    def write_utf(self, value: str) -> None:
        """Write varint of length of value up to 32767 bytes, then write value encoded with utf8."""
        self.write_varint(len(value))
        self.write(bytearray(value, "utf8"))

    def write_ascii(self, value: str) -> None:
        """Write value encoded with ISO-8859-1, then write an additional 0x00 at the end."""
        self.write(bytearray(value, "ISO-8859-1"))
        self.write(bytearray.fromhex("00"))

    def write_short(self, value: int) -> None:
        """Write 2 bytes for value -32768 - 32767."""
        self.write(self._pack("h", value))

    def write_ushort(self, value: int) -> None:
        """Write 2 bytes for value 0 - 65535 (2 ** 16 - 1)."""
        self.write(self._pack("H", value))

    def write_int(self, value: int) -> None:
        """Write 4 bytes for value -2147483648 - 2147483647."""
        self.write(self._pack("i", value))

    def write_uint(self, value: int) -> None:
        """Write 4 bytes for value 0 - 4294967295 (2 ** 32 - 1)."""
        self.write(self._pack("I", value))

    def write_long(self, value: int) -> None:
        """Write 8 bytes for value -9223372036854775808 - 9223372036854775807."""
        self.write(self._pack("q", value))

    def write_ulong(self, value: int) -> None:
        """Write 8 bytes for value 0 - 18446744073709551613 (2 ** 64 - 1)."""
        self.write(self._pack("Q", value))

    def write_buffer(self, buffer: "Connection") -> None:
        """Flush buffer, then write a varint of the length of the buffer's data, then write buffer data."""
        data = buffer.flush()
        self.write_varint(len(data))
        self.write(data)


class BaseWriteAsync(ABC):
    """Base synchronous write class"""

    __slots__ = ()

    @abstractmethod
    async def write(self, data: Connection | str | bytearray | bytes) -> None:
        """Write data to self."""
        ...

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__} Object>"

    @staticmethod
    def _pack(format_: str, data: int) -> bytes:
        """Pack data in with format in big-endian mode."""
        return struct.pack(">" + format_, data)

    async def write_varint(self, value: int) -> None:
        """
        Write varint with value value to self.

        :param value: Max 2 ** 31 - 1, min -(2 ** 31).
        :raises ValueError: If value is out of range.
        """
        remaining = unsigned_int32(value).value
        for _ in range(5):
            if not remaining & -0x80:  # remaining & ~0x7F == 0:
                await self.write(struct.pack("!B", remaining))
                if value > 2**31 - 1 or value < -(2**31):
                    break
                return
            await self.write(struct.pack("!B", remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varint')

    async def write_varlong(self, value: int) -> None:
        """
        Write varlong with value value to self.

        :param value: Max 2 ** 63 - 1, min -(2 ** 63).
        :raises ValueError: If value is out of range.
        """
        remaining = unsigned_int64(value).value
        for _ in range(10):
            if not remaining & -0x80:  # remaining & ~0x7F == 0:
                await self.write(struct.pack("!B", remaining))
                if value > 2**63 - 1 or value < -(2**31):
                    break
                return
            await self.write(struct.pack("!B", remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varlong')

    async def write_utf(self, value: str) -> None:
        """Write varint of length of value up to 32767 bytes, then write value encoded with utf8."""
        await self.write_varint(len(value))
        await self.write(bytearray(value, "utf8"))

    async def write_ascii(self, value: str) -> None:
        """Write value encoded with ISO-8859-1, then write an additional 0x00 at the end."""
        await self.write(bytearray(value, "ISO-8859-1"))
        await self.write(bytearray.fromhex("00"))

    async def write_short(self, value: int) -> None:
        """Write 2 bytes for value -32768 - 32767."""
        await self.write(self._pack("h", value))

    async def write_ushort(self, value: int) -> None:
        """Write 2 bytes for value 0 - 65535 (2 ** 16 - 1)."""
        await self.write(self._pack("H", value))

    async def write_int(self, value: int) -> None:
        """Write 4 bytes for value -2147483648 - 2147483647."""
        await self.write(self._pack("i", value))

    async def write_uint(self, value: int) -> None:
        """Write 4 bytes for value 0 - 4294967295 (2 ** 32 - 1)."""
        await self.write(self._pack("I", value))

    async def write_long(self, value: int) -> None:
        """Write 8 bytes for value -9223372036854775808 - 9223372036854775807."""
        await self.write(self._pack("q", value))

    async def write_ulong(self, value: int) -> None:
        """Write 8 bytes for value 0 - 18446744073709551613 (2 ** 64 - 1)."""
        await self.write(self._pack("Q", value))

    async def write_buffer(self, buffer: "Connection") -> None:
        """Flush buffer, then write a varint of the length of the buffer's
        data, then write buffer data."""
        data = buffer.flush()
        await self.write_varint(len(data))
        await self.write(data)


class BaseReadSync(ABC):
    """Base synchronous read class"""

    __slots__ = ()

    @abstractmethod
    def read(self, length: int) -> bytearray:
        """Read length bytes from self, return a byte array."""
        ...

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__} Object>"

    @staticmethod
    def _unpack(format_: str, data: bytes) -> int:
        """Unpack data as bytes with format in big-endian."""
        return struct.unpack(">" + format_, bytes(data))[0]

    def read_varint(self) -> int:
        """
        Read varint from self and return it.

        :param value: Max 2 ** 31 - 1, min -(2 ** 31)
        :raises IOError: If varint received is out of range.
        """
        result = 0
        for i in range(5):
            part = self.read(1)[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError("Received varint is too big!")

    def read_varlong(self) -> int:
        """
        Read varlong from self and return it.

        :param value: Max 2 ** 63 - 1, min -(2 ** 63).
        :raises IOError: If varint received is out of range.
        """
        result = 0
        for i in range(10):
            part = self.read(1)[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int64(result).value
        raise IOError("Received varlong is too big!")

    def read_utf(self) -> str:
        """Read up to 32767 bytes by reading a varint, then decode bytes as utf8."""
        length = self.read_varint()
        return self.read(length).decode("utf8")

    def read_ascii(self) -> str:
        """Read self until last value is not zero, then return that decoded with ISO-8859-1"""
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(self.read(1))
        return result[:-1].decode("ISO-8859-1")

    def read_short(self) -> int:
        """Return -32768 - 32767. Read 2 bytes."""
        return self._unpack("h", self.read(2))

    def read_ushort(self) -> int:
        """Return 0 - 65535 (2 ** 16 - 1). Read 2 bytes."""
        return self._unpack("H", self.read(2))

    def read_int(self) -> int:
        """Return -2147483648 - 2147483647. Read 4 bytes."""
        return self._unpack("i", self.read(4))

    def read_uint(self) -> int:
        """Return 0 - 4294967295 (2 ** 32 - 1). 4 bytes read."""
        return self._unpack("I", self.read(4))

    def read_long(self) -> int:
        """Return -9223372036854775808 - 9223372036854775807. Read 8 bytes."""
        return self._unpack("q", self.read(8))

    def read_ulong(self) -> int:
        """Return 0 - 18446744073709551613 (2 ** 64 - 1). Read 8 bytes."""
        return self._unpack("Q", self.read(8))

    def read_buffer(self) -> "Connection":
        """Read a varint for length, then return a new connection from length read bytes."""
        length = self.read_varint()
        result = Connection()
        result.receive(self.read(length))
        return result


class BaseReadAsync(ABC):
    """Asynchronous Read connection base class."""

    __slots__ = ()

    @abstractmethod
    async def read(self, length: int) -> bytearray:
        """Read length bytes from self, return a byte array."""
        ...

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__} Object>"

    @staticmethod
    def _unpack(format_: str, data: bytes) -> int:
        """Unpack data as bytes with format in big-endian."""
        return struct.unpack(">" + format_, bytes(data))[0]

    async def read_varint(self) -> int:
        """
        Read varint from self and return it.

        :param value: Max 2 ** 31 - 1, min -(2 ** 31)
        :raises IOError: If varint received is out of range.
        """
        result = 0
        for i in range(5):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << 7 * i
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError("Received a varint that was too big!")

    async def read_varlong(self) -> int:
        """
        Read varlong from self and return it.

        :param value: Max 2 ** 63 - 1, min -(2 ** 63).
        :raises IOError: If varint received is out of range.
        """
        result = 0
        for i in range(10):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int64(result).value
        raise IOError("Received varlong is too big!")

    async def read_utf(self) -> str:
        """Read up to 32767 bytes by reading a varint, then decode bytes as utf8."""
        length = await self.read_varint()
        return (await self.read(length)).decode("utf8")

    async def read_ascii(self) -> str:
        """Read self until last value is not zero, then return that decoded with ISO-8859-1"""
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(await self.read(1))
        return result[:-1].decode("ISO-8859-1")

    async def read_short(self) -> int:
        """Return -32768 - 32767. Read 2 bytes."""
        return self._unpack("h", await self.read(2))

    async def read_ushort(self) -> int:
        """Return 0 - 65535 (2 ** 16 - 1). Read 2 bytes."""
        return self._unpack("H", await self.read(2))

    async def read_int(self) -> int:
        """Return -2147483648 - 2147483647. Read 4 bytes."""
        return self._unpack("i", await self.read(4))

    async def read_uint(self) -> int:
        """Return 0 - 4294967295 (2 ** 32 - 1). 4 bytes read."""
        return self._unpack("I", await self.read(4))

    async def read_long(self) -> int:
        """Return -9223372036854775808 - 9223372036854775807. Read 8 bytes."""
        return self._unpack("q", await self.read(8))

    async def read_ulong(self) -> int:
        """Return 0 - 18446744073709551613 (2 ** 64 - 1). Read 8 bytes."""
        return self._unpack("Q", await self.read(8))

    async def read_buffer(self) -> Connection:
        """Read a varint for length, then return a new connection from length read bytes."""
        length = await self.read_varint()
        result = Connection()
        result.receive(await self.read(length))
        return result


class BaseConnection:
    """Base Connection class. Implements flush, receive, and remaining."""

    __slots__ = ()

    def __repr__(self) -> str:
        """Return representation of self."""
        return f"<{self.__class__.__name__} Object>"

    def flush(self) -> bytearray:
        """Raise TypeError, unsupported."""
        raise TypeError(f"{self.__class__.__name__} does not support flush()")

    def receive(self, data: BytesConvertable | bytearray) -> None:
        """Raise TypeError, unsupported."""
        raise TypeError(f"{self.__class__.__name__} does not support receive()")

    def remaining(self) -> int:
        """Raise TypeError, unsupported."""
        raise TypeError(f"{self.__class__.__name__} does not support remaining()")


class BaseSyncConnection(BaseConnection, BaseReadSync, BaseWriteSync):
    """Base synchronous read and write class"""

    __slots__ = ()


class BaseAsyncReadSyncWriteConnection(BaseConnection, BaseReadAsync, BaseWriteSync):
    """Base asynchronous read and synchronous write class"""

    __slots__ = ()


class BaseAsyncConnection(BaseConnection, BaseReadAsync, BaseWriteAsync):
    """Base asynchronous read and write class"""

    __slots__ = ()


class Connection(BaseSyncConnection):
    """Base connection class."""

    __slots__ = ("sent", "received")

    def __init__(self) -> None:
        """Initialize self.send and self.received to an empty byte array."""
        self.sent = bytearray()
        self.received = bytearray()

    def read(self, length: int) -> bytearray:
        """Return self.received up to length bytes, then cut received up to that point."""
        result = self.received[:length]
        self.received = self.received[length:]
        return result

    def write(self, data: Connection | str | bytearray | bytes) -> None:
        """Extend self.sent from data."""
        if isinstance(data, Connection):
            data = data.flush()
        if isinstance(data, str):
            data = bytearray(data, "utf-8")
        self.sent.extend(data)

    def receive(self, data: BytesConvertable | bytearray) -> None:
        """Extend self.received with data."""
        if not isinstance(data, bytearray):
            data = bytearray(data)
        self.received.extend(data)

    def remaining(self) -> int:
        """Return length of self.received."""
        return len(self.received)

    def flush(self) -> bytearray:
        """Return self.sent. Clears self.sent."""
        result, self.sent = self.sent, bytearray()
        return result

    def copy(self) -> "Connection":
        """Return a copy of self"""
        new = self.__class__()
        new.receive(self.received)
        new.write(self.sent)
        return new


class SocketConnection(BaseSyncConnection):
    """Socket connection."""

    __slots__ = ("socket",)

    def __init__(self) -> None:
        """Set socket to none"""
        # These will only be None until connect is called, ignore the None type assignment
        self.socket: socket.socket = None  # type: ignore[assignment]

    def close(self) -> None:
        """Close self.socket."""
        if self.socket is not None:  # If initialized
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def __del__(self) -> None:
        """Close self.socket."""
        try:
            self.close()
        except OSError:  # Probably, the socket was already closed by the OS
            pass


class TCPSocketConnection(SocketConnection):
    """TCP Connection to address. Timeout defaults to 3 seconds."""

    __slots__ = ()

    def __init__(self, addr: tuple[str | None, int], timeout: float = 3):
        """Create a connection to address with self.socket, set TCP NODELAY to True."""
        super().__init__()
        self.socket = socket.create_connection(addr, timeout=timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def read(self, length: int) -> bytearray:
        """Return length bytes read from self.socket. Raises IOError when server doesn't respond."""
        result = bytearray()
        while len(result) < length:
            new = self.socket.recv(length - len(result))
            if len(new) == 0:
                raise IOError("Server did not respond with any information!")
            result.extend(new)
        return result

    def write(self, data: Connection | str | bytes | bytearray) -> None:
        """Send data on self.socket."""
        if isinstance(data, Connection):
            data = bytearray(data.flush())
        elif isinstance(data, str):
            data = bytearray(data, "utf-8")
        self.socket.send(data)


class UDPSocketConnection(SocketConnection):
    """UDP Connection class"""

    __slots__ = ("addr",)

    def __init__(self, addr: Address, timeout: float = 3):
        """Set self.addr to address, set self.socket to new socket, AF_INET if IPv4, AF_INET6 otherwise."""
        super().__init__()
        self.addr = addr
        self.socket = socket.socket(
            socket.AF_INET if ip_type(addr[0]) == 4 else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )
        self.socket.settimeout(timeout)

    def remaining(self) -> int:
        """Return 65535."""
        return 65535

    def read(self, length: int) -> bytearray:
        """Return up to self.remaining() bytes. Length does nothing."""
        result = bytearray()
        while len(result) == 0:
            result.extend(self.socket.recvfrom(self.remaining())[0])
        return result

    def write(self, data: Connection | str | bytes | bytearray) -> None:
        """Use self.socket to send data to self.addr."""
        if isinstance(data, Connection):
            data = bytearray(data.flush())
        elif isinstance(data, str):
            data = bytearray(data, "utf-8")
        self.socket.sendto(data, self.addr)


class TCPAsyncSocketConnection(BaseAsyncReadSyncWriteConnection):
    """Asynchronous TCP Connection class"""

    __slots__ = ("reader", "writer", "timeout")

    def __init__(self) -> None:
        # These will only be None until connect is called, ignore the None type assignment
        self.reader: asyncio.StreamReader = None  # type: ignore[assignment]
        self.writer: asyncio.StreamWriter = None  # type: ignore[assignment]
        self.timeout: float = None  # type: ignore[assignment]

    async def connect(self, addr: Address, timeout: float = 3) -> None:
        """Use asyncio to open a connection to address. Timeout is in seconds."""
        self.timeout = timeout
        conn = asyncio.open_connection(addr[0], addr[1])
        self.reader, self.writer = await asyncio.wait_for(conn, timeout=self.timeout)

    async def read(self, length: int) -> bytearray:
        """Read up to length bytes from self.reader."""
        result = bytearray()
        while len(result) < length:
            new = await asyncio.wait_for(self.reader.read(length - len(result)), timeout=self.timeout)
            if len(new) == 0:
                raise IOError("Socket did not respond with any information!")
            result.extend(new)
        return result

    def write(self, data: Connection | str | bytes | bytearray) -> None:
        """Write data to self.writer."""
        if isinstance(data, Connection):
            data = bytearray(data.flush())
        elif isinstance(data, str):
            data = bytearray(data, "utf-8")
        self.writer.write(data)

    def close(self) -> None:
        """Close self.writer."""
        if self.writer is not None:  # If initialized
            try:
                self.writer.close()
            except RuntimeError:  # There is a case where event loop is closed
                pass

    def __del__(self) -> None:
        """Close self."""
        self.close()


class UDPAsyncSocketConnection(BaseAsyncConnection):
    """Asynchronous UDP Connection class"""

    __slots__ = ("stream", "timeout")

    def __init__(self) -> None:
        # This will only be None until connect is called, ignore the None type assignment
        self.stream: asyncio_dgram.aio.DatagramClient = None  # type: ignore[assignment]
        self.timeout: float = None  # type: ignore[assignment]

    async def connect(self, addr: Address, timeout: float = 3) -> None:
        """Connect to address. Timeout is in seconds."""
        self.timeout = timeout
        conn = asyncio_dgram.connect((addr[0], addr[1]))
        self.stream = await asyncio.wait_for(conn, timeout=self.timeout)

    def remaining(self) -> int:
        """Return 65535 (2 ** 16 - 1)."""
        return 65535

    async def read(self, length: int) -> bytearray:
        """Read from stream. Length does nothing."""
        data, remote_addr = await asyncio.wait_for(self.stream.recv(), timeout=self.timeout)
        return bytearray(data)

    async def write(self, data: Connection | str | bytes | bytearray) -> None:
        """Send data with self.stream."""
        if isinstance(data, Connection):
            data = bytearray(data.flush())
        elif isinstance(data, str):
            data = bytearray(data, "utf-8")
        await self.stream.send(data)

    def close(self) -> None:
        """Close self.stream"""
        if self.stream is not None:  # If initialized
            self.stream.close()

    def __del__(self) -> None:
        """Close self.stream"""
        try:
            self.close()
        except (asyncio.exceptions.CancelledError, asyncio.exceptions.TimeoutError):
            return
