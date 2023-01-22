import asyncio
import typing
from asyncio.exceptions import TimeoutError
from unittest.mock import patch

import pytest

from mcstatus.address import Address
from mcstatus.protocol.connection import TCPAsyncSocketConnection


class FakeAsyncStream(asyncio.StreamReader):
    async def read(self, *args, **kwargs) -> typing.NoReturn:
        await asyncio.sleep(2)
        raise NotImplementedError("tests are designed to timeout before reaching this line")


async def fake_asyncio_asyncio_open_connection(hostname: str, port: int):
    return FakeAsyncStream(), None


class TestAsyncSocketConnection:
    @pytest.mark.asyncio
    async def test_tcp_socket_read(self):
        with patch("asyncio.open_connection", fake_asyncio_asyncio_open_connection):
            async with TCPAsyncSocketConnection(Address("dummy_address", 1234), timeout=0.01) as tcp_async_socket:
                with pytest.raises(TimeoutError):
                    await tcp_async_socket.read(10)
