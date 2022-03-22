import asyncio
from unittest.mock import patch

import pytest

from mcstatus.address import Address
from mcstatus.protocol.connection import TCPAsyncSocketConnection


class FakeAsyncStream(asyncio.StreamReader):
    async def read(self, n: int) -> bytes:
        await asyncio.sleep(delay=2)
        return bytes([0] * n)


async def fake_asyncio_asyncio_open_connection(hostname: str, port: int):
    return FakeAsyncStream(), None


class TestAsyncSocketConnection:
    def setup_method(self):
        self.tcp_async_socket = TCPAsyncSocketConnection()
        self.test_addr = Address("dummy_address", 1234)

    def test_tcp_socket_read(self):
        try:
            from asyncio.exceptions import TimeoutError
        except ImportError:
            from asyncio import TimeoutError

        loop = asyncio.get_event_loop()
        with patch("asyncio.open_connection", fake_asyncio_asyncio_open_connection):
            loop.run_until_complete(self.tcp_async_socket.connect(self.test_addr, timeout=0.01))

            with pytest.raises(TimeoutError):
                loop.run_until_complete(self.tcp_async_socket.read(10))
