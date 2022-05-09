"TCP and UDP Connections, both asynchronous and not."

from __future__ import annotations

import asyncio
import socket
import struct
from abc import ABC, abstractmethod
from ipaddress import ip_address
from typing import Iterable, Optional, Union

from ctypes import c_uint32 as unsigned_int32
from ctypes import c_int32 as signed_int32
from ctypes import c_uint64 as unsigned_int64
from ctypes import c_int64 as signed_int64

from typing_extensions import SupportsIndex

import asyncio_dgram

BytesConvertable = Union[SupportsIndex, Iterable[SupportsIndex]]

def ip_type(address: Union[int, str]) -> Optional[int]:
    "Returns what version of ip a given address is."
    try:
        return ip_address(address).version
    except ValueError:
        return None

class BaseWriteSync(ABC):
    "Base syncronous write class"
    __slots__: tuple = tuple()
    @abstractmethod
    def write(self, data: bytes) -> None:
        "Write data to self."
        ...
    
    def __repr__(self) -> str:
        "Return representation of self."
        return f'<{self.__class__.__name__} Object>'
    
    @staticmethod
    def _pack(format_: str, data: int) -> bytes:
        "Pack data in with format in big-endian mode."
        return struct.pack('>' + format_, data)
    
    def write_varint(self, value: int) -> None:
        """Write varint with value value to self.
        Max: 2 ** 31 - 1, Min: -(2 ** 31).
        Raises ValueError if varint is too big."""
        remaining = unsigned_int32(value).value
        for _ in range(5):
            if not remaining & -0x80:#remaining & ~0x7F == 0:
                self.write(struct.pack('!B', remaining))
                if value > 2 ** 31 - 1 or value < -(2 ** 31):
                    break
                return
            self.write(struct.pack('!B', remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varint')
    
    def write_varlong(self, value: int) -> None:
        """Write varlong with value value to self.
        Max: 2 ** 63 - 1, Min: -(2 ** 63).
        Raises ValueError if varint is too big."""
        remaining = unsigned_int64(value).value
        for _ in range(10):
            if not remaining & -0x80:#remaining & ~0x7F == 0:
                self.write(struct.pack('!B', remaining))
                if value > 2 ** 63 - 1 or value < -(2 ** 31):
                    break
                return
            self.write(struct.pack('!B', remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varlong')
    
    def write_utf(self, value: str) -> None:
        "Write varint of length of value up to 32767 bytes, then write value encoded with utf8."
        self.write_varint(len(value))
        self.write(bytearray(value, 'utf8'))
    
    def write_ascii(self, value: str) -> None:
        "Write value encoded with ISO-8859-1, then write an additional 0x00 at the end."
        self.write(bytearray(value, 'ISO-8859-1'))
        self.write(bytearray.fromhex('00'))
    
    def write_short(self, value: int) -> None:
        "Write 2 bytes for value -32768 - 32767"
        self.write(self._pack('h', value))
    
    def write_ushort(self, value: int) -> None:
        "Write 2 bytes for value 0 - 65535 (2 ** 16 - 1)."
        self.write(self._pack('H', value))
    
    def write_int(self, value: int) -> None:
        "Write 4 bytes for value -2147483648 - 2147483647."
        self.write(self._pack('i', value))
    
    def write_uint(self, value: int) -> None:
        "Write 4 bytes for value 0 - 4294967295 (2 ** 32 - 1)."
        self.write(self._pack('I', value))
    
    def write_long(self, value: int) -> None:
        "Write 8 bytes for value -9223372036854775808 - 9223372036854775807."
        self.write(self._pack('q', value))
    
    def write_ulong(self, value: int) -> None:
        "Write 8 bytes for value 0 - 18446744073709551613 (2 ** 64 - 1)."
        self.write(self._pack('Q', value))
    
    def write_buffer(self, buffer: 'Connection') -> None:
        """Flush buffer, then write a varint of the length of the buffer's
        data, then write buffer data."""
        data = buffer.flush()
        self.write_varint(len(data))
        self.write(data)

class BaseWriteAsync(ABC):
    "Base syncronous write class"
    __slots__: tuple = tuple()
    @abstractmethod
    async def write(self, data: bytes) -> None:
        "Write data to self."
        ...
    
    def __repr__(self) -> str:
        "Return representation of self."
        return f'<{self.__class__.__name__} Object>'
    
    @staticmethod
    def _pack(format_: str, data: int) -> bytes:
        "Pack data in with format in big-endian mode."
        return struct.pack('>' + format_, data)
    
    async def write_varint(self, value: int) -> None:
        """Write varint with value value to self.
        Max: 2 ** 31 - 1, Min: -(2 ** 31).
        Raises ValueError if varint is too big."""
        remaining = unsigned_int32(value).value
        for _ in range(5):
            if not remaining & -0x80:#remaining & ~0x7F == 0:
                await self.write(struct.pack('!B', remaining))
                if value > 2 ** 31 - 1 or value < -(2 ** 31):
                    break
                return
            await self.write(struct.pack('!B', remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varint')
    
    async def write_varlong(self, value: int) -> None:
        """Write varlong with value value to self.
        Max: 2 ** 63 - 1, Min: -(2 ** 63).
        Raises ValueError if varint is too big."""
        remaining = unsigned_int64(value).value
        for _ in range(10):
            if not remaining & -0x80:#remaining & ~0x7F == 0:
                await self.write(struct.pack('!B', remaining))
                if value > 2 ** 63 - 1 or value < -(2 ** 31):
                    break
                return
            await self.write(struct.pack('!B', remaining & 0x7F | 0x80))
            remaining >>= 7
        raise ValueError(f'The value "{value}" is too big to send in a varlong')
    
    async def write_utf(self, value: str) -> None:
        "Write varint of length of value up to 32767 bytes, then write value encoded with utf8."
        await self.write_varint(len(value))
        await self.write(bytearray(value, 'utf8'))
    
    async def write_ascii(self, value: str) -> None:
        "Write value encoded with ISO-8859-1, then write an additional 0x00 at the end."
        await self.write(bytearray(value, 'ISO-8859-1'))
        await self.write(bytearray.fromhex('00'))
    
    async def write_short(self, value: int) -> None:
        "Write 2 bytes for value -32768 - 32767"
        await self.write(self._pack('h', value))
    
    async def write_ushort(self, value: int) -> None:
        "Write 2 bytes for value 0 - 65535 (2 ** 16 - 1)."
        await self.write(self._pack('H', value))
    
    async def write_int(self, value: int) -> None:
        "Write 4 bytes for value -2147483648 - 2147483647."
        await self.write(self._pack('i', value))
    
    async def write_uint(self, value: int) -> None:
        "Write 4 bytes for value 0 - 4294967295 (2 ** 32 - 1)."
        await self.write(self._pack('I', value))
    
    async def write_long(self, value: int) -> None:
        "Write 8 bytes for value -9223372036854775808 - 9223372036854775807."
        await self.write(self._pack('q', value))
    
    async def write_ulong(self, value: int) -> None:
        "Write 8 bytes for value 0 - 18446744073709551613 (2 ** 64 - 1)."
        await self.write(self._pack('Q', value))
    
    async def write_buffer(self, buffer: 'Connection') -> None:
        """Flush buffer, then write a varint of the length of the buffer's
        data, then write buffer data."""
        data = buffer.flush()
        await self.write_varint(len(data))
        await self.write(data)

class BaseReadSync(ABC):
    "Base syncronous read class"
    __slots__: tuple = tuple()
    @abstractmethod
    def read(self, length: int) -> bytearray:
        "Read length bytes from self, return a bytearray."
        ...
    
    def __repr__(self) -> str:
        "Return representation of self."
        return f'<{self.__class__.__name__} Object>'
    
    @staticmethod
    def _unpack(format_: str, data: bytes) -> int:
        "Unpack data as bytes with format in big-enidian."
        return struct.unpack('>' + format_, bytes(data))[0]
    
    def read_varint(self) -> int:
        """Read varint from self and return it.
        Max: 2 ** 31 - 1, Min: -(2 ** 31)
        Raises IOError when varint recieved is too big."""
        result = 0
        for i in range(5):
            part = self.read(1)[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError('Recieved varint is too big!')
    
    def read_varlong(self) -> int:
        """Read varlong from self and return it.
        Max: 2 ** 63 - 1, Min: -(2 ** 63).
        Raises IOError when varint recieved is too big."""
        result = 0
        for i in range(10):
            part = self.read(1)[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int64(result).value
        raise IOError('Recieved varlong is too big!')
    
    def read_utf(self) -> str:
        "Read up to 32767 bytes by reading a varint, then decode bytes as utf8."
        length = self.read_varint()
        return self.read(length).decode('utf8')
    
    def read_ascii(self) -> str:
        "Read self until last value is not zero, then return that decoded with ISO-8859-1"
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(self.read(1))
        return result[:-1].decode('ISO-8859-1')
    
    def read_short(self) -> int:
        "Return -32768 - 32767. Read 2 bytes."
        return self._unpack('h', self.read(2))
    
    def read_ushort(self) -> int:
        "Return 0 - 65535 (2 ** 16 - 1). Read 2 bytes."
        return self._unpack('H', self.read(2))
    
    def read_int(self) -> int:
        "Return -2147483648 - 2147483647. Read 4 bytes."
        return self._unpack('i', self.read(4))
    
    def read_uint(self) -> int:
        "Return 0 - 4294967295 (2 ** 32 - 1). 4 bytes read."
        return self._unpack('I', self.read(4))
    
    def read_long(self) -> int:
        "Return -9223372036854775808 - 9223372036854775807. Read 8 bytes."
        return self._unpack('q', self.read(8))
    
    def read_ulong(self) -> int:
        "Return 0 - 18446744073709551613 (2 ** 64 - 1). Read 8 bytes."
        return self._unpack('Q', self.read(8))
    
    def read_buffer(self) -> 'Connection':
        "Read a varint for length, then return a new connection from length read bytes."
        length = self.read_varint()
        result = Connection()
        result.receive(self.read(length))
        return result

class BaseReadAsync(ABC):
    "Asyncronous Read connection base class."
    __slots__: tuple = tuple()
    @abstractmethod
    async def read(self, length: int) -> bytearray:
        "Read length bytes from self, return a bytearray."
        ...
    
    def __repr__(self) -> str:
        "Return representation of self."
        return f'<{self.__class__.__name__} Object>'
    
    @staticmethod
    def _unpack(format_: str, data: bytes) -> int:
        "Unpack data as bytes with format in big-enidian."
        return struct.unpack('>' + format_, bytes(data))[0]
    
    async def read_varint(self) -> int:
        """Read varint from self and return it.
        Max: 2 ** 31 - 1, Min: -(2 ** 31)
        Raises IOError when varint recieved is too big."""
        result = 0
        for i in range(5):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << 7 * i
            if not part & 0x80:
                return signed_int32(result).value
        raise IOError('Recieved a varint that was too big!')
    
    async def read_varlong(self) -> int:
        """Read varlong from self and return it.
        Max: 2 ** 63 - 1, Min: -(2 ** 63).
        Raises IOError when varint recieved is too big."""
        result = 0
        for i in range(10):
            part = (await self.read(1))[0]
            result |= (part & 0x7F) << (7 * i)
            if not part & 0x80:
                return signed_int64(result).value
        raise IOError('Recieved varlong is too big!')
    
    async def read_utf(self) -> str:
        "Read up to 32767 bytes by reading a varint, then decode bytes as utf8."
        length = await self.read_varint()
        return (await self.read(length)).decode('utf8')
    
    async def read_ascii(self) -> str:
        "Read self until last value is not zero, then return that decoded with ISO-8859-1"
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            result.extend(await self.read(1))
        return result[:-1].decode('ISO-8859-1')
    
    async def read_short(self) -> int:
        "Return -32768 - 32767. Read 2 bytes."
        return self._unpack('h', await self.read(2))
    
    async def read_ushort(self) -> int:
        "Return 0 - 65535 (2 ** 16 - 1). Read 2 bytes."
        return self._unpack('H', await self.read(2))
    
    async def read_int(self) -> int:
        "Return -2147483648 - 2147483647. Read 4 bytes."
        return self._unpack('i', await self.read(4))
    
    async def read_uint(self) -> int:
        "Return 0 - 4294967295 (2 ** 32 - 1). 4 bytes read."
        return self._unpack('I', await self.read(4))
    
    async def read_long(self) -> int:
        "Return -9223372036854775808 - 9223372036854775807. Read 8 bytes."
        return self._unpack('q', await self.read(8))
    
    async def read_ulong(self) -> int:
        "Return 0 - 18446744073709551613 (2 ** 64 - 1). Read 8 bytes."
        return self._unpack('Q', await self.read(8))
    
    async def read_buffer(self) -> Connection:
        "Read a varint for length, then return a new connection from length read bytes."
        length = await self.read_varint()
        result = Connection()
        result.receive(await self.read(length))
        return result

class BaseConnection:
    "Base connection class, implements flush, receive, and remaining."
    __slots__: tuple = tuple()
    def __repr__(self) -> str:
        "Return representation of self."
        return f'<{self.__class__.__name__} Object>'
    
    def flush(self) -> bytearray:
        "Raise TypeError, unsupported."
        raise TypeError(f'{self.__class__.__name__} does not support flush()')
    
    def receive(self, data: Union[BytesConvertable, bytearray]) -> None:
        "Raise TypeError, unsupported."
        raise TypeError(f'{self.__class__.__name__} does not support receive()')
    
    def remaining(self) -> int:
        "Raise TypeError, unsupported."
        raise TypeError(f'{self.__class__.__name__} does not support remaining()')

class BaseSyncConnection(BaseConnection, BaseReadSync, BaseWriteSync):
    "Base syncronous read and write class"
    __slots__: tuple = tuple()
    
class BaseAsyncReadSyncWriteConnection(BaseConnection, BaseReadAsync, BaseWriteSync):
    "Base asyncronous read and syncronous write class"
    __slots__: tuple = tuple()

class BaseAsyncConnection(BaseConnection, BaseReadAsync, BaseWriteAsync):
    "Base asyncronous read and write class"
    __slots__: tuple = tuple()

class Connection(BaseSyncConnection):
    "Base connection class."
    __slots__: tuple = ('sent', 'received')
    def __init__(self):
        "Initialize self.send and self.received to an empty bytearray."
        self.sent = bytearray()
        self.received = bytearray()
    
    def read(self, length: int) -> bytearray:
        "Return self.recieved up to length bytes, then cut recieved up to that point."
        result = self.received[:length]
        self.received = self.received[length:]
        return result
    
    def write(self, data: Union['Connection', str, bytearray, bytes]) -> None:
        "Extend self.sent from data."
        if isinstance(data, Connection):
            data = data.flush()
        if isinstance(data, str):
            data = bytearray(data, 'utf-8')
        self.sent.extend(data)
    
    def receive(self, data: Union[BytesConvertable, bytearray]) -> None:
        "Extend self.received with data."
        if not isinstance(data, bytearray):
            data = bytearray(data)
        self.received.extend(data)
    
    def remaining(self) -> int:
        "Return length of self.received."
        return len(self.received)
    
    def flush(self) -> bytearray:
        "Return self.sent. Clears self.sent."
        result, self.sent = self.sent, bytearray()
        return result
    
    def copy(self) -> 'Connection':
        "Return a copy of self"
        new = self.__class__()
        new.receive(self.received)
        new.write(self.sent)
        return new

class SocketConnection(BaseSyncConnection):
    "Socket connection."
    __slots__ = ('socket',)
    def __init__(self):
        "Set socket to none"
        self.socket: socket.socket = None
    
    def close(self) -> None:
        "Close self."
        if self.socket is not None:# If initialized
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
    
    def __del__(self) -> None:
        "Shutdown and Close self.socket."
        self.close()

class TCPSocketConnection(SocketConnection):
    "TCP Connection to addr. Timeout defaults to 3 secconds."
    def __init__(self, addr: tuple[Optional[str], int], timeout: int=3):
        "Create a connection to addr with self.socket, set TCP NODELAY to True."
        super().__init__()
        self.socket = socket.create_connection(addr, timeout=timeout)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    def read(self, length: int) -> bytearray:
        "Return length bytes read from self.socket. Raises IOError when server doesn't respond."
        result = bytearray()
        while len(result) < length:
            new = self.socket.recv(length - len(result))
            if len(new) == 0:
                raise IOError('Server did not respond with any information!')
            result.extend(new)
        return result
    
    def write(self, data: bytes) -> None:
        "Send data on self.socket."
        self.socket.send(data)

class UDPSocketConnection(SocketConnection):
    "UDP Connection to addr. Default timout is 3 secconds."
    __slots__ = ('addr',)
    def __init__(self, addr: tuple[str, int], timeout: int=3):
        """Set self.addr to addr, set self.socket to new socket,
        AF_INET if IPv4, AF_INET6 otherwise."""
        super().__init__()
        self.addr = addr
        self.socket = socket.socket(
            socket.AF_INET if ip_type(addr[0]) == 4 else socket.AF_INET6,
            socket.SOCK_DGRAM,
        )
        self.socket.settimeout(timeout)
    
    def remaining(self) -> int:
        "Return 65535."
        return 65535
    
    def read(self, length: int) -> bytearray:
        "Return up to self.remaining() bytes. Length does nothing."
        result = bytearray()
        while len(result) == 0:
            result.extend(self.socket.recvfrom(self.remaining())[0])
        return result
    
    def write(self, data: bytes) -> None:
        "Use self.socket to send data to self.addr."
        self.socket.sendto(data, self.addr)

class TCPAsyncSocketConnection(BaseAsyncReadSyncWriteConnection):
    "Asyncronous TCP connection to addr. Default timeout is 3 secconds."
    __slots__ = ('reader', 'writer')
    def __init__(self):
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
    
    async def connect(self, addr: tuple[str, int], timeout: int=3) -> None:
        "Use asyncio to open a connection to addr (host, port)."
        conn = asyncio.open_connection(addr[0], addr[1])
        self.reader, self.writer = await asyncio.wait_for(conn, timeout=timeout)
    
    async def read(self, length: int) -> bytearray:
        "Read up to length bytes from self.reader."
        result = bytearray()
        while len(result) < length:
            new = await self.reader.read(length - len(result))
            if len(new) == 0:
                raise IOError('Socket did not respond with any information!')
            result.extend(new)
        return result
    
    def write(self, data: bytes) -> None:
        "Write data to self.writer."
        self.writer.write(data)
    
    def close(self) -> None:
        "Close self.writer."
        if self.writer is not None:# If initialized
            self.writer.close()
    
    def __del__(self) -> None:
        "Close self."
        self.close()

class UDPAsyncSocketConnection(BaseAsyncConnection):
    "Asyncronous UDP connection to addr. Default timeout is 3 secconds."
    __slots__ = ('stream', 'timeout')
    def __init__(self):
        self.stream: asyncio_dgram.aio.DatagramClient = None
        self.timeout: int = None
    
    async def connect(self, addr: tuple, timeout: int=3) -> None:
        "Connect to addr (host, port)"
        self.timeout = timeout
        conn = asyncio_dgram.connect((addr[0], addr[1]))
        self.stream = await asyncio.wait_for(conn, timeout=self.timeout)
    
    def remaining(self) -> int:
        "Return 65535 (2 ** 16 - 1)."
        return 65535
    
    async def read(self, length: int) -> bytearray:
        "Read from stream. Length does nothing."
        # pylint: disable=unused-variable
        data, remote_addr = await asyncio.wait_for(self.stream.recv(),
                                                   timeout=self.timeout)
        return bytearray(data)
    
    async def write(self, data: bytes) -> None:
        "Send data with self.stream."
        await self.stream.send(data)
    
    def close(self) -> None:
        "Close self.stream"
        if self.stream is not None:# If initialized
##            self.stream.socket.shutdown(socket.SHUT_RDWR)
##            self.stream.socket.close()
            self.stream.close()
    
    def __del__(self) -> None:
        "Close self.stream."
        try:
            self.close()
        except (asyncio.exceptions.CancelledError,
                asyncio.exceptions.TimeoutError):
            return
