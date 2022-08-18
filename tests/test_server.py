import asyncio
import sys
from unittest.mock import patch

import pytest
import pytest_asyncio

from mcstatus.protocol.connection import Connection
from mcstatus.server import AsyncJavaServer, BedrockServer, JavaServer


class MockProtocolFactory(asyncio.Protocol):
    transport: asyncio.Transport

    def __init__(self, data_expected_to_receive, data_to_respond_with):
        self.data_expected_to_receive = data_expected_to_receive
        self.data_to_respond_with = data_to_respond_with

    def connection_made(self, transport: asyncio.Transport):
        print("connection_made")
        self.transport = transport

    def connection_lost(self, exc):
        print("connection_lost")
        self.transport.close()

    def data_received(self, data):
        assert self.data_expected_to_receive in data
        self.transport.write(self.data_to_respond_with)

    def eof_received(self):
        print("eof_received")

    def pause_writing(self):
        print("pause_writing")

    def resume_writing(self):
        print("resume_writing")


@pytest_asyncio.fixture()
async def create_mock_packet_server(event_loop):
    servers = []

    async def create_server(port, data_expected_to_receive, data_to_respond_with):
        server = await event_loop.create_server(
            lambda: MockProtocolFactory(data_expected_to_receive, data_to_respond_with),
            host="localhost",
            port=port,
        )
        servers.append(server)
        return server

    yield create_server

    for server in servers:
        server.close()
        await server.wait_closed()


class TestBedrockServer:
    def setup_method(self):
        self.server = BedrockServer("localhost")

    def test_default_port(self):
        assert self.server.address.port == 19132

    def test_lookup_constructor(self):
        s = BedrockServer.lookup("example.org")
        assert s.address.host == "example.org"
        assert s.address.port == 19132


class TestAsyncJavaServer:
    @pytest.mark.asyncio
    async def test_async_ping(self, unused_tcp_port, create_mock_packet_server):
        await create_mock_packet_server(
            port=unused_tcp_port,
            data_expected_to_receive=bytearray.fromhex("09010000000001C54246"),
            data_to_respond_with=bytearray.fromhex("0F002F096C6F63616C686F737463DD0109010000000001C54246"),
        )
        minecraft_server = AsyncJavaServer("localhost", port=unused_tcp_port)

        latency = await minecraft_server.ping(ping_token=29704774, version=47)
        assert latency >= 0

    @pytest.mark.asyncio
    async def test_async_lookup_constructor(self):
        s = await AsyncJavaServer.lookup("example.org:3333")
        assert s.address.host == "example.org"
        assert s.address.port == 3333


class TestJavaServer:
    def setup_method(self):
        self.socket = Connection()
        self.server = JavaServer("localhost")

    def test_default_port(self):
        assert self.server.address.port == 25565

    def test_ping(self):
        self.socket.receive(bytearray.fromhex("09010000000001C54246"))

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            latency = self.server.ping(ping_token=29704774, version=47)

        assert self.socket.flush() == bytearray.fromhex("0F002F096C6F63616C686F737463DD0109010000000001C54246")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert latency >= 0

    def test_ping_retry(self):
        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerPinger") as pinger:
                pinger.side_effect = [Exception, Exception, Exception]
                with pytest.raises(Exception):
                    self.server.ping()
                assert pinger.call_count == 3

    def test_status(self):
        self.socket.receive(
            bytearray.fromhex(
                "6D006B7B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E38222C2270726F746F"
                "636F6C223A34377D7D09010000000001C54246"
            )
        )

        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = self.socket
            info = self.server.status(ping_token=29704774, version=47)

        assert self.socket.flush() == bytearray.fromhex("0F002F096C6F63616C686F737463DD01010009010000000001C54246")
        assert self.socket.remaining() == 0, "Data is pending to be read, but should be empty"
        assert info.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8", "protocol": 47},
        }
        assert info.latency >= 0

    def test_status_retry(self):
        with patch("mcstatus.server.TCPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerPinger") as pinger:
                pinger.side_effect = [Exception, Exception, Exception]
                with pytest.raises(Exception):
                    self.server.status()
                assert pinger.call_count == 3

    def test_query(self):
        self.socket.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.socket.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d6574797"
                "06500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d61700077"
                "6f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f737"
                "46970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053"
                "746576650000"
            )
        )

        with patch("mcstatus.protocol.connection.Connection.remaining") as mock_remaining:
            mock_remaining.side_effect = [15, 208]

            with patch("mcstatus.server.UDPSocketConnection") as connection, patch.object(
                self.server.address, "resolve_ip"
            ) as resolve_ip:
                connection.return_value = self.socket
                resolve_ip.return_value = "127.0.0.1"
                info = self.server.query()

            conn_bytes = self.socket.flush()
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
        with patch("mcstatus.server.UDPSocketConnection") as connection:
            connection.return_value = None
            with patch("mcstatus.server.ServerQuerier") as querier:
                querier.side_effect = [Exception, Exception, Exception]
                with pytest.raises(Exception), patch.object(self.server.address, "resolve_ip") as resolve_ip:
                    resolve_ip.return_value = "127.0.0.1"
                    self.server.query()
                assert querier.call_count == 3

    def test_lookup_constructor(self):
        s = JavaServer.lookup("example.org:4444")
        assert s.address.host == "example.org"
        assert s.address.port == 4444


class TestDeprecations:
    @pytest.mark.asyncio
    @pytest.mark.skipif(sys.version_info < (3, 8), reason="AsyncMock was introduced in Python 3.8")
    @pytest.mark.parametrize(
        "method,to_mock",
        [
            (JavaServer.async_lookup, "mcstatus.AsyncJavaServer.lookup"),
            (JavaServer.async_ping, "mcstatus.AsyncJavaServer.ping"),
            (JavaServer.async_status, "mcstatus.AsyncJavaServer.status"),
            (JavaServer.async_query, "mcstatus.AsyncJavaServer.query"),
        ],
    )
    async def test_deprecations_raise_warning(self, method, to_mock):
        server = JavaServer("my_server.net")
        with patch(to_mock), pytest.deprecated_call():
            await method(server)

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    @pytest.mark.skipif(sys.version_info < (3, 8), reason="AsyncMock was introduced in Python 3.8")
    @pytest.mark.parametrize(
        "method,expecting_to_call",
        [
            (JavaServer.async_lookup, "mcstatus.AsyncJavaServer.lookup"),
            (JavaServer.async_ping, "mcstatus.AsyncJavaServer.ping"),
            (JavaServer.async_status, "mcstatus.AsyncJavaServer.status"),
            (JavaServer.async_query, "mcstatus.AsyncJavaServer.query"),
        ],
    )
    async def test_deprecations_call_expected_methods(self, method, expecting_to_call):
        server = JavaServer("my_server.net")
        with patch(expecting_to_call) as mocked:
            await method(server)
        mocked.assert_called_once()
