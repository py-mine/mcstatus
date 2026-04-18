from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, final
from unittest.mock import call, patch

import pytest
import pytest_asyncio

from mcstatus._net.address import Address
from mcstatus.server import BedrockServer, JavaServer, LegacyServer
from tests.protocol.helpers import AsyncBufferConnection, SyncBufferConnection, SyncDatagramConnection

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from typing_extensions import override
else:
    override = lambda f: f  # noqa: E731


@final
class MockProtocolFactory(asyncio.Protocol):
    transport: asyncio.Transport

    def __init__(self, data_expected_to_receive: bytes, data_to_respond_with: bytes):
        self.data_expected_to_receive = data_expected_to_receive
        self.data_to_respond_with = data_to_respond_with

    @override
    def connection_made(self, transport: asyncio.Transport):  # pyright: ignore[reportIncompatibleMethodOverride]
        print("connection_made")
        self.transport = transport

    @override
    def connection_lost(self, exc):
        print("connection_lost")
        self.transport.close()

    @override
    def data_received(self, data):
        assert self.data_expected_to_receive in data
        self.transport.write(self.data_to_respond_with)

    @override
    def eof_received(self):
        print("eof_received")

    @override
    def pause_writing(self):
        print("pause_writing")

    @override
    def resume_writing(self):
        print("resume_writing")


@pytest_asyncio.fixture()
async def create_mock_packet_server():
    """Create a temporary asyncio packet servers used by tests."""
    event_loop = asyncio.get_running_loop()
    servers: list[asyncio.Server] = []

    async def create_server(port: int, data_expected_to_receive: bytes, data_to_respond_with: bytes) -> asyncio.Server:
        """Start a server that validates one request pattern and returns a fixed payload."""
        server = await event_loop.create_server(
            lambda: MockProtocolFactory(data_expected_to_receive, data_to_respond_with),
            host="127.0.0.1",
            port=port,
        )
        servers.append(server)
        return server

    yield create_server

    for server in servers:
        server.close()
        await server.wait_closed()


@final
class TestBedrockServer:
    def setup_method(self):
        self.server = BedrockServer("127.0.0.1")

    def test_default_port(self):
        assert self.server.address.port == 19132

    def test_lookup_constructor(self):
        s = BedrockServer.lookup("example.org")
        assert s.address.host == "example.org"
        assert s.address.port == 19132


@final
class TestAsyncJavaServer:
    @pytest.mark.asyncio
    async def test_async_ping(
        self,
        unused_tcp_port: int,
        create_mock_packet_server: Callable[..., Awaitable[asyncio.Server]],
    ):
        _ = await create_mock_packet_server(
            port=unused_tcp_port,
            data_expected_to_receive=bytearray.fromhex("09010000000001C54246"),
            data_to_respond_with=bytearray.fromhex("0F002F096C6F63616C686F737463DD0109010000000001C54246"),
        )
        minecraft_server = JavaServer("127.0.0.1", port=unused_tcp_port)

        latency = await minecraft_server.async_ping(ping_token=29704774, version=47)
        assert latency >= 0

    @pytest.mark.asyncio
    async def test_async_lookup_constructor(self):
        s = await JavaServer.async_lookup("example.org:3333")
        assert s.address.host == "example.org"
        assert s.address.port == 3333


def test_java_server_with_query_port():
    with patch("mcstatus.server.JavaServer._retry_query") as patched_query_func:
        server = JavaServer("127.0.0.1", query_port=12345)
        _ = server.query()
        assert server.query_port == 12345
        assert patched_query_func.call_args == call(Address("127.0.0.1", port=12345), tries=3)


@pytest.mark.asyncio
async def test_java_server_with_query_port_async():
    with patch("mcstatus.server.JavaServer._retry_async_query") as patched_query_func:
        server = JavaServer("127.0.0.1", query_port=12345)
        _ = await server.async_query()
        assert server.query_port == 12345
        assert patched_query_func.call_args == call(Address("127.0.0.1", port=12345), tries=3)


@final
class TestJavaServer:
    def setup_method(self):
        self.socket = SyncBufferConnection()
        self.server = JavaServer("127.0.0.1")

    def test_default_port(self):
        assert self.server.address.port == 25565

    def test_ping(self):
        self.socket.receive(bytearray.fromhex("09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value.__enter__.return_value = self.socket
            latency = self.server.ping(ping_token=29704774, version=47)

        assert self.socket.flush() == bytearray.fromhex("0F002F093132372E302E302E3163DD0109010000000001C54246")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert latency >= 0

    def test_ping_retry(self):
        # Use a blank mock for the connection, we don't want to actually create any connections
        with patch("mcstatus.server.TCPSocketConnection"), patch("mcstatus.server.JavaClient") as java_client:
            java_client.side_effect = [RuntimeError, RuntimeError, RuntimeError]
            with pytest.raises(RuntimeError, match=r"^$"):
                _ = self.server.ping()
            assert java_client.call_count == 3

    def test_status(self):
        self.socket.receive(
            bytearray.fromhex(
                "6D006B7B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E38222C2270726F746F"
                "636F6C223A34377D7D"
            )
        )

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value.__enter__.return_value = self.socket
            info = self.server.status(version=47)

        assert self.socket.flush() == bytearray.fromhex("0F002F093132372E302E302E3163DD010100")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert info.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8", "protocol": 47},
        }
        assert info.latency >= 0

    def test_status_retry(self):
        # Use a blank mock for the connection, we don't want to actually create any connections
        with patch("mcstatus.server.TCPSocketConnection"), patch("mcstatus.server.JavaClient") as java_client:
            java_client.side_effect = [RuntimeError, RuntimeError, RuntimeError]
            with pytest.raises(RuntimeError, match=r"^$"):
                _ = self.server.status()
            assert java_client.call_count == 3

    def test_query(self):
        socket = SyncDatagramConnection()
        socket.receive(bytearray.fromhex("090000000035373033353037373800"))
        socket.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d6574797"
                "06500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d61700077"
                "6f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f737"
                "46970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053"
                "746576650000"
            )
        )

        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value.__enter__.return_value = socket
            info = self.server.query()

        conn_bytes = socket.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD09")
        assert info.raw == {
            "hostname": "A Minecraft Server",
            "gametype": "SMP",
            "game_id": "MINECRAFT",
            "version": "1.8",
            "plugins": "",
            "map": "world",
            "numplayers": "3",
            "maxplayers": "20",
            "hostport": "25565",
            "hostip": "192.168.56.1",
        }

    def test_query_retry(self):
        # Use a blank mock for the connection, we don't want to actually create any connections
        with patch("mcstatus.server.UDPSocketConnection"), patch("mcstatus.server.QueryClient") as query_client:
            query_client.side_effect = [RuntimeError, RuntimeError, RuntimeError]
            with pytest.raises(RuntimeError, match=r"^$"):
                _ = self.server.query()
            assert query_client.call_count == 3

    def test_lookup_constructor(self):
        s = JavaServer.lookup("example.org:4444")
        assert s.address.host == "example.org"
        assert s.address.port == 4444


@final
class TestLegacyServer:
    def setup_method(self):
        self.socket = SyncBufferConnection()
        self.server = LegacyServer("127.0.0.1")

    def test_default_port(self):
        assert self.server.address.port == 25565

    def test_lookup_constructor(self):
        s = LegacyServer.lookup("example.org:4444")
        assert s.address.host == "example.org"
        assert s.address.port == 4444

    def test_status(self):
        self.socket.receive(
            bytearray.fromhex(
                "ff002300a70031000000340037000000"
                "31002e0034002e003200000041002000"
                "4d0069006e0065006300720061006600"
                "74002000530065007200760065007200"
                "000030000000320030"
            )
        )

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value.__enter__.return_value = self.socket
            info = self.server.status()

        assert self.socket.flush() == bytearray.fromhex("fe01fa")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert info.as_dict() == {
            "latency": info.latency,
            "motd": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.4.2", "protocol": 47},
        }
        assert info.latency >= 0


@final
class TestAsyncLegacyServer:
    def setup_method(self):
        self.socket = AsyncBufferConnection()
        self.server = LegacyServer("127.0.0.1")

    @pytest.mark.asyncio
    async def test_async_lookup_constructor(self):
        s = await LegacyServer.async_lookup("example.org:3333")
        assert s.address.host == "example.org"
        assert s.address.port == 3333

    @pytest.mark.asyncio
    async def test_async_status(self):
        self.socket.receive(
            bytearray.fromhex(
                "ff002300a70031000000340037000000"
                "31002e0034002e003200000041002000"
                "4d0069006e0065006300720061006600"
                "74002000530065007200760065007200"
                "000030000000320030"
            )
        )

        with patch("mcstatus.server.TCPAsyncSocketConnection") as connection:
            connection.return_value.__aenter__.return_value = self.socket
            info = await self.server.async_status()

        assert self.socket.flush() == bytearray.fromhex("fe01fa")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert info.as_dict() == {
            "latency": info.latency,
            "motd": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.4.2", "protocol": 47},
        }
        assert info.latency >= 0
