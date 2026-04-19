import asyncio
import typing
from asyncio.exceptions import TimeoutError as AsyncioTimeoutError
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.io.connection import TCPAsyncSocketConnection

if typing.TYPE_CHECKING:
    from typing_extensions import override
else:
    override = lambda f: f  # noqa: E731


class FakeAsyncStream(asyncio.StreamReader):
    @override
    async def read(self, *args: typing.Any, **kwargs: typing.Any) -> typing.NoReturn:
        await asyncio.sleep(2)
        raise NotImplementedError("tests are designed to timeout before reaching this line")


async def fake_asyncio_asyncio_open_connection(hostname: str, port: int):  # should be async without await # noqa: RUF029
    return FakeAsyncStream(), None


class TestAsyncSocketConnection:
    async def test_tcp_socket_read(self):
        with patch("asyncio.open_connection", fake_asyncio_asyncio_open_connection):
            async with TCPAsyncSocketConnection(Address("dummy_address", 1234), timeout=0.01) as tcp_async_socket:
                with pytest.raises(AsyncioTimeoutError):
                    _ = await tcp_async_socket.read(10)

    async def test_tcp_socket_read_partial_data_then_eof(self):
        """Raise when the stream ends after only partial payload delivery."""
        tcp_async_socket = TCPAsyncSocketConnection(Address("dummy_address", 1234), timeout=0.01)
        tcp_async_socket.reader = Mock(read=AsyncMock(side_effect=[b"a", b""]))

        with pytest.raises(
            OSError,
            match=(
                r"^Server stopped responding \(got 1 bytes, but expected 2 bytes\). "
                r"Partial obtained data: bytearray\(b'a'\)$"
            ),
        ):
            _ = await tcp_async_socket.read(2)

    async def test_tcp_socket_read_eof_without_any_data(self):
        """Raise when the stream immediately ends without returning any data."""
        tcp_async_socket = TCPAsyncSocketConnection(Address("dummy_address", 1234), timeout=0.01)
        tcp_async_socket.reader = Mock(read=AsyncMock(return_value=b""))

        with pytest.raises(OSError, match=r"^Server did not respond with any information!$"):
            _ = await tcp_async_socket.read(2)

    async def test_tcp_socket_write_awaits_drain(self):
        """Ensure writes await ``drain`` so buffered data is flushed."""
        writer = Mock()
        writer.write = Mock()
        writer.drain = AsyncMock()

        tcp_async_socket = TCPAsyncSocketConnection(Address("dummy_address", 1234), timeout=0.01)
        tcp_async_socket.writer = writer

        await tcp_async_socket.write(b"hello")

        writer.write.assert_called_once_with(b"hello")
        writer.drain.assert_awaited_once_with()

    async def test_tcp_socket_close_waits_for_writer(self):
        """Ensure close awaits ``wait_closed`` on the stream writer."""
        writer = Mock()
        writer.close = Mock()
        writer.wait_closed = AsyncMock()

        tcp_async_socket = TCPAsyncSocketConnection(Address("dummy_address", 1234), timeout=0.01)
        tcp_async_socket.writer = typing.cast("asyncio.StreamWriter", writer)

        await tcp_async_socket.close()

        writer.close.assert_called_once_with()
        writer.wait_closed.assert_awaited_once_with()
