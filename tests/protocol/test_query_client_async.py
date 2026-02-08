from mcstatus._protocol.connection import Connection
from mcstatus._protocol.query_client import AsyncQueryClient
from tests.protocol.test_java_client_async import async_decorator


class FakeUDPAsyncConnection(Connection):
    async def read(self, length):  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().read(length)

    async def write(self, data):  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().write(data)


class TestAsyncQueryClient:
    def setup_method(self):
        self.query_client = AsyncQueryClient(FakeUDPAsyncConnection())  # pyright: ignore[reportArgumentType]

    def test_handshake(self):
        self.query_client.connection.receive(bytearray.fromhex("090000000035373033353037373800"))
        async_decorator(self.query_client.handshake)()
        conn_bytes = self.query_client.connection.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD09")
        assert self.query_client.challenge == 570350778

    def test_query(self):
        self.query_client.connection.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d6574797"
                "06500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d61700077"
                "6f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f737"
                "46970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053"
                "746576650000"
            )
        )
        response = async_decorator(self.query_client.read_query)()
        conn_bytes = self.query_client.connection.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD00")
        assert conn_bytes[7:] == bytearray.fromhex("0000000000000000")
        assert response.raw == {
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
        assert response.players.list == ["Dinnerbone", "Djinnibone", "Steve"]
