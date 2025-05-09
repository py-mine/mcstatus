from mcstatus.motd import Motd
from mcstatus.protocol.connection import Connection
from mcstatus.querier import ServerQuerier


class TestMinecraftQuerier:
    def setup_method(self):
        self.querier = ServerQuerier(Connection())  # type: ignore[arg-type]

    def test_handshake(self):
        self.querier.connection.receive(bytearray.fromhex("090000000035373033353037373800"))
        self.querier.handshake()

        conn_bytes = self.querier.connection.flush()
        assert conn_bytes[:3] == bytearray.fromhex("FEFD09")
        assert self.querier.challenge == 570350778

    def test_query(self):
        self.querier.connection.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d650041204d696e656372616674205365727665720067616d6574797"
                "06500534d500067616d655f6964004d494e4543524146540076657273696f6e00312e3800706c7567696e7300006d61700077"
                "6f726c64006e756d706c61796572730033006d6178706c617965727300323000686f7374706f727400323535363500686f737"
                "46970003139322e3136382e35362e31000001706c617965725f000044696e6e6572626f6e6500446a696e6e69626f6e650053"
                "746576650000"
            )
        )
        response = self.querier.read_query()
        conn_bytes = self.querier.connection.flush()
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

    def test_query_handles_unorderd_map_response(self):
        self.querier.connection.receive(
            bytearray(
                b"\x00\x00\x00\x00\x00GeyserMC\x00\x80\x00hostname\x00Geyser\x00hostip\x001.1.1.1\x00plugins\x00\x00numplayers"
                b"\x001\x00gametype\x00SMP\x00maxplayers\x00100\x00hostport\x0019132\x00version\x00Geyser"
                b" (git-master-0fd903e) 1.18.10\x00map\x00Geyser\x00game_id\x00MINECRAFT\x00\x00\x01player_\x00\x00\x00"
            )
        )
        response = self.querier.read_query()
        self.querier.connection.flush()

        assert response.raw["game_id"] == "MINECRAFT"
        assert response.motd == Motd.parse("Geyser")
        assert response.software.version == "Geyser (git-master-0fd903e) 1.18.10"

    def test_query_handles_unicode_motd_with_nulls(self):
        self.querier.connection.receive(
            bytearray(
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00hostname\x00\x00*K\xd5\x00gametype\x00SMP"
                b"\x00game_id\x00MINECRAFT\x00version\x001.16.5\x00plugins\x00Paper on 1.16.5-R0.1-SNAPSHOT\x00map\x00world"
                b"\x00numplayers\x000\x00maxplayers\x0020\x00hostport\x0025565\x00hostip\x00127.0.1.1\x00\x00\x01player_\x00"
                b"\x00\x00"
            )
        )
        response = self.querier.read_query()
        self.querier.connection.flush()

        assert response.raw["game_id"] == "MINECRAFT"
        assert response.motd == Motd.parse("\x00*KÕ")

    def test_query_handles_unicode_motd_with_2a00_at_the_start(self):
        self.querier.connection.receive(
            bytearray.fromhex(
                "00000000000000000000000000000000686f73746e616d6500006f746865720067616d657479706500534d500067616d655f6964004d"
                "494e4543524146540076657273696f6e00312e31382e3100706c7567696e7300006d617000776f726c64006e756d706c617965727300"
                "30006d6178706c617965727300323000686f7374706f727400323535363500686f73746970003137322e31372e302e32000001706c61"
                "7965725f000000"
            )
        )
        response = self.querier.read_query()
        self.querier.connection.flush()

        assert response.raw["game_id"] == "MINECRAFT"
        assert response.motd == Motd.parse("\x00other")  # "\u2a00other" is actually what is expected,
        # but the query protocol for vanilla has a bug when it comes to unicode handling.
        # The status protocol correctly shows "⨀other".
