import asyncio
import sys
from typing import final
from unittest import mock

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.java_client import AsyncJavaClient
from tests.protocol.helpers import AsyncBufferConnection, async_decorator


@final
class TestAsyncJavaClient:
    def setup_method(self):
        self.connection = AsyncBufferConnection()
        self.java_client = AsyncJavaClient(
            self.connection,  # pyright: ignore[reportArgumentType]
            address=Address("localhost", 25565),
            version=44,
        )

    def test_handshake(self):
        async_decorator(self.java_client.handshake)()

        assert self.connection.flush() == bytearray.fromhex("0F002C096C6F63616C686F737463DD01")

    def test_read_status(self):
        self.connection.receive(
            bytearray.fromhex(
                "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C22"
                "70726F746F636F6C223A34347D7D"
            )
        )
        status = async_decorator(self.java_client.read_status)()

        assert status.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
        }
        assert self.connection.flush() == bytearray.fromhex("0100")

    def test_read_status_invalid_json(self):
        self.connection.receive(bytearray.fromhex("0300017B"))
        with pytest.raises(IOError, match=r"^Received invalid JSON$"):
            _ = async_decorator(self.java_client.read_status)()

    def test_read_status_invalid_reply(self):
        self.connection.receive(
            bytearray.fromhex(
                "4F004D7B22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616"
                "D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"
            )
        )

        _ = async_decorator(self.java_client.read_status)()

    def test_read_status_invalid_status(self):
        self.connection.receive(bytearray.fromhex("0105"))

        with pytest.raises(IOError, match=r"^Received invalid status response packet.$"):
            _ = async_decorator(self.java_client.read_status)()

    def test_test_ping(self):
        self.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.java_client.ping_token = 14515484

        assert async_decorator(self.java_client.test_ping)() >= 0
        assert self.connection.flush() == bytearray.fromhex("09010000000000DD7D1C")

    def test_test_ping_invalid(self):
        self.connection.receive(bytearray.fromhex("011F"))
        self.java_client.ping_token = 14515484

        with pytest.raises(IOError, match=r"^Received invalid ping response packet.$"):
            _ = async_decorator(self.java_client.test_ping)()

    def test_test_ping_wrong_token(self):
        self.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.java_client.ping_token = 12345

        with pytest.raises(IOError, match=r"^Received mangled ping response \(expected token 12345, got 14515484\)$"):
            _ = async_decorator(self.java_client.test_ping)()

    @pytest.mark.asyncio
    # Windows CI can occasionally measure <1ms despite a 1ms sleep;
    # see https://github.com/py-mine/mcstatus/issues/442.
    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    async def test_latency_is_real_number(self):
        self.connection.receive(
            bytearray.fromhex(
                "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C22"
                "70726F746F636F6C223A34347D7D"
            )
        )

        async def mocked_read_bytearray() -> bytes:
            """Delay reads while still delegating to the real async connection implementation."""
            await asyncio.sleep(0.001)
            return await original_read_bytearray()

        original_read_bytearray = self.connection.read_bytearray

        with mock.patch.object(self.connection, "read_bytearray", side_effect=mocked_read_bytearray):
            # Latency should be in milliseconds, so somewhere just above 1
            #
            # We give it a pretty big leeway with the max here, as the MacOS CI runs can
            # sometimes take quite long (upwards of 10s).
            latency = (await self.java_client.read_status()).latency
            assert 1 <= latency <= 20

    @pytest.mark.asyncio
    # Windows CI can occasionally measure <1ms despite a 1ms sleep;
    # see https://github.com/py-mine/mcstatus/issues/442.
    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    async def test_test_ping_is_in_milliseconds(self):
        self.java_client.ping_token = 14515484
        self.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))

        async def mocked_read_bytearray() -> bytes:
            """Delay reads while still delegating to the real async connection implementation."""
            await asyncio.sleep(0.001)
            return await original_read_bytearray()

        original_read_bytearray = self.connection.read_bytearray

        with mock.patch.object(self.connection, "read_bytearray", side_effect=mocked_read_bytearray):
            # Latency should be in milliseconds, so somewhere just above 1
            #
            # We give it a pretty big leeway with the max here, as the MacOS CI runs can
            # sometimes take quite long (upwards of 10s).
            latency = await self.java_client.test_ping()
            assert 1 <= latency <= 20
