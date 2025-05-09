from pytest import fixture

from mcstatus.motd import Motd
from mcstatus.responses import QueryPlayers, QueryResponse, QuerySoftware, RawQueryResponse
from tests.responses import BaseResponseTest


@BaseResponseTest.construct
class TestQueryResponse(BaseResponseTest):
    RAW: RawQueryResponse = RawQueryResponse(
        **{  # type: ignore # str cannot be assigned to Literal
            "hostname": "A Minecraft Server",
            "gametype": "GAME TYPE",
            "game_id": "GAME ID",
            "version": "1.8",
            "plugins": "",
            "map": "world",
            "numplayers": "3",
            "maxplayers": "20",
            "hostport": "9999",
            "hostip": "192.168.56.1",
        }
    )
    RAW_PLAYERS = ["Dinnerbone", "Djinnibone", "Steve"]

    EXPECTED_VALUES = [
        ("raw", RAW),
        ("motd", Motd.parse("A Minecraft Server")),
        ("map_name", "world"),
        ("players", QueryPlayers(online=3, max=20, list=["Dinnerbone", "Djinnibone", "Steve"])),
        ("software", QuerySoftware(version="1.8", brand="vanilla", plugins=[])),
        ("ip", "192.168.56.1"),
        ("port", 9999),
        ("game_type", "GAME TYPE"),
        ("game_id", "GAME ID"),
    ]

    @fixture(scope="class")
    def build(self):
        return QueryResponse.build(raw=self.RAW, players_list=self.RAW_PLAYERS)

    def test_as_dict(self, build: QueryResponse):
        assert build.as_dict() == {
            "game_id": "GAME ID",
            "game_type": "GAME TYPE",
            "ip": "192.168.56.1",
            "map_name": "world",
            "motd": "A Minecraft Server",
            "players": {
                "list": [
                    "Dinnerbone",
                    "Djinnibone",
                    "Steve",
                ],
                "max": 20,
                "online": 3,
            },
            "port": 9999,
            "raw": {
                "game_id": "GAME ID",
                "gametype": "GAME TYPE",
                "hostip": "192.168.56.1",
                "hostname": "A Minecraft Server",
                "hostport": "9999",
                "map": "world",
                "maxplayers": "20",
                "numplayers": "3",
                "plugins": "",
                "version": "1.8",
            },
            "software": {
                "brand": "vanilla",
                "plugins": [],
                "version": "1.8",
            },
        }


@BaseResponseTest.construct
class TestQueryPlayers(BaseResponseTest):
    EXPECTED_VALUES = [
        ("online", 3),
        ("max", 20),
        ("list", ["Dinnerbone", "Djinnibone", "Steve"]),
    ]

    @fixture(scope="class")
    def build(self):
        return QueryPlayers.build(
            raw={
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
            },
            players_list=["Dinnerbone", "Djinnibone", "Steve"],
        )


class TestQuerySoftware:
    def test_vanilla(self):
        software = QuerySoftware.build("1.8", "")
        assert software.brand == "vanilla"
        assert software.version == "1.8"
        assert software.plugins == []

    def test_modded(self):
        software = QuerySoftware.build("1.8", "A modded server: Foo 1.0; Bar 2.0; Baz 3.0")
        assert software.brand == "A modded server"
        assert software.plugins == ["Foo 1.0", "Bar 2.0", "Baz 3.0"]

    def test_modded_no_plugins(self):
        software = QuerySoftware.build("1.8", "A modded server")
        assert software.brand == "A modded server"
        assert software.plugins == []
