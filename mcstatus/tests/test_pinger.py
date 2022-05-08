import pytest

from mcstatus.address import Address
from mcstatus.pinger import ServerPinger
from mcstatus.protocol.connection import Connection
from mcstatus.status_response import JavaServerPlayer, JavaServerPlayers, JavaServerResponse, JavaServerVersion


class TestServerPinger:
    def setup_method(self):
        self.pinger = ServerPinger(
            Connection(),  # type: ignore[arg-type]
            address=Address("localhost", 25565),
            version=44,
        )

    def test_handshake(self):
        self.pinger.handshake()

        assert self.pinger.connection.flush() == bytearray.fromhex("0F002C096C6F63616C686F737463DD01")

    def test_read_status(self):
        self.pinger.connection.receive(
            bytearray.fromhex(
                "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C22"
                "70726F746F636F6C223A34347D7D"
            )
        )
        status = self.pinger.read_status()

        assert status == JavaServerResponse(
            players=JavaServerPlayers(max=20, online=0, list=None),
            version=JavaServerVersion(name="1.8-pre1", protocol=44),
            motd="A Minecraft Server",
            latency=status.latency,
            icon=None,
        )
        assert self.pinger.connection.flush() == bytearray.fromhex("0100")

    def test_read_status_invalid_json(self):
        self.pinger.connection.receive(bytearray.fromhex("0300017B"))
        with pytest.raises(IOError):
            self.pinger.read_status()

    def test_read_status_invalid_reply(self):
        self.pinger.connection.receive(
            bytearray.fromhex(
                "4F004D7B22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616"
                "D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"
            )
        )

        with pytest.raises(IOError):
            self.pinger.read_status()

    def test_read_status_invalid_status(self):
        self.pinger.connection.receive(bytearray.fromhex("0105"))

        with pytest.raises(IOError):
            self.pinger.read_status()

    def test_test_ping(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 14515484

        assert self.pinger.test_ping() >= 0
        assert self.pinger.connection.flush() == bytearray.fromhex("09010000000000DD7D1C")

    def test_test_ping_invalid(self):
        self.pinger.connection.receive(bytearray.fromhex("011F"))
        self.pinger.ping_token = 14515484

        with pytest.raises(IOError):
            self.pinger.test_ping()

    def test_test_ping_wrong_token(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 12345

        with pytest.raises(IOError):
            self.pinger.test_ping()


class TestPingResponse:
    def test_motd(self):
        response = JavaServerResponse.build(
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
            }
        )

        assert response.motd == "A Minecraft Server"

    def test_description_missing(self):
        with pytest.raises(ValueError):
            JavaServerResponse.build(
                {
                    "players": {"max": 20, "online": 0},
                    "version": {"name": "1.8-pre1", "protocol": 44},
                }
            )

    def test_parse_description_strips_html_color_codes(self):
        out = JavaServerResponse._parse_description(
            {
                "extra": [
                    {"text": " "},
                    {"strikethrough": True, "color": "#b3eeff", "text": "="},
                    {"strikethrough": True, "color": "#b9ecff", "text": "="},
                    {"strikethrough": True, "color": "#c0eaff", "text": "="},
                    {"strikethrough": True, "color": "#c7e8ff", "text": "="},
                    {"strikethrough": True, "color": "#cee6ff", "text": "="},
                    {"strikethrough": True, "color": "#d5e4ff", "text": "="},
                    {"strikethrough": True, "color": "#dce2ff", "text": "="},
                    {"strikethrough": True, "color": "#e3e0ff", "text": "="},
                    {"strikethrough": True, "color": "#eadeff", "text": "="},
                    {"strikethrough": True, "color": "#f1dcff", "text": "="},
                    {"strikethrough": True, "color": "#f8daff", "text": "="},
                    {"strikethrough": True, "color": "#ffd9ff", "text": "="},
                    {"strikethrough": True, "color": "#f4dcff", "text": "="},
                    {"strikethrough": True, "color": "#f9daff", "text": "="},
                    {"strikethrough": True, "color": "#ffd9ff", "text": "="},
                    {"color": "white", "text": " "},
                    {"bold": True, "color": "#66ff99", "text": "C"},
                    {"bold": True, "color": "#75f5a2", "text": "r"},
                    {"bold": True, "color": "#84ebab", "text": "e"},
                    {"bold": True, "color": "#93e2b4", "text": "a"},
                    {"bold": True, "color": "#a3d8bd", "text": "t"},
                    {"bold": True, "color": "#b2cfc6", "text": "i"},
                    {"bold": True, "color": "#c1c5cf", "text": "v"},
                    {"bold": True, "color": "#d1bbd8", "text": "e"},
                    {"bold": True, "color": "#e0b2e1", "text": "F"},
                    {"bold": True, "color": "#efa8ea", "text": "u"},
                    {"bold": True, "color": "#ff9ff4", "text": "n "},
                    {"strikethrough": True, "color": "#b3eeff", "text": "="},
                    {"strikethrough": True, "color": "#b9ecff", "text": "="},
                    {"strikethrough": True, "color": "#c0eaff", "text": "="},
                    {"strikethrough": True, "color": "#c7e8ff", "text": "="},
                    {"strikethrough": True, "color": "#cee6ff", "text": "="},
                    {"strikethrough": True, "color": "#d5e4ff", "text": "="},
                    {"strikethrough": True, "color": "#dce2ff", "text": "="},
                    {"strikethrough": True, "color": "#e3e0ff", "text": "="},
                    {"strikethrough": True, "color": "#eadeff", "text": "="},
                    {"strikethrough": True, "color": "#f1dcff", "text": "="},
                    {"strikethrough": True, "color": "#f8daff", "text": "="},
                    {"strikethrough": True, "color": "#ffd9ff", "text": "="},
                    {"strikethrough": True, "color": "#f4dcff", "text": "="},
                    {"strikethrough": True, "color": "#f9daff", "text": "="},
                    {"strikethrough": True, "color": "#ffd9ff", "text": "="},
                    {"color": "white", "text": " \n "},
                    {"bold": True, "color": "#E5E5E5", "text": "The server has been updated to "},
                    {"bold": True, "color": "#97ABFF", "text": "1.17.1"},
                ],
                "text": "",
            }
        )
        assert out == (
            " ===============§f §lC§lr§le§la§lt§li§lv§le§lF§lu§ln ===============§f \n"
            " §lThe server has been updated to §l1.17.1"
        )

    def test_parse_description(self):
        out = JavaServerResponse._parse_description("test §2description")
        assert out == "test §2description"

        out = JavaServerResponse._parse_description({"text": "§8§lfoo"})
        assert out == "§8§lfoo"

        out = JavaServerResponse._parse_description(
            {
                "extra": [{"bold": True, "italic": True, "color": "gray", "text": "foo"}, {"color": "gold", "text": "bar"}],
                "text": ".",
            }
        )
        # We don't care in which order the style prefixes are, allow any
        assert out in {
            "§l§o§7foo§6bar.",
            "§l§7§ofoo§6bar.",
            "§o§l§7foo§6bar.",
            "§o§7§lfoo§6bar.",
            "§7§o§lfoo§6bar.",
            "§7§l§ofoo§6bar.",
        }

        out = JavaServerResponse._parse_description(
            [{"bold": True, "italic": True, "color": "gray", "text": "foo"}, {"color": "gold", "text": "bar"}]
        )
        assert out in {
            "§l§o§7foo§6bar",
            "§l§7§ofoo§6bar",
            "§o§l§7foo§6bar",
            "§o§7§lfoo§6bar",
            "§7§o§lfoo§6bar",
            "§7§l§ofoo§6bar",
        }

    def test_version(self):
        response = JavaServerResponse.build(
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
            }
        )

        assert response.version is not None
        assert response.version.name == "1.8-pre1"
        assert response.version.protocol == 44

    def test_version_missing(self):
        with pytest.raises(ValueError):
            JavaServerResponse.build(
                {
                    "description": "A Minecraft Server",
                    "players": {"max": 20, "online": 0},
                }
            )

    def test_version_invalid(self):
        with pytest.raises(TypeError):
            JavaServerResponse.build(
                {
                    "description": "A Minecraft Server",
                    "players": {"max": 20, "online": 0},
                    "version": "foo",
                }
            )

    def test_players(self):
        response = JavaServerResponse.build(
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 5},
                "version": {"name": "1.8-pre1", "protocol": 44},
            }
        )

        assert response.players is not None
        assert response.players.max == 20
        assert response.players.online == 5

    def test_players_missing(self):
        with pytest.raises(ValueError):
            JavaServerResponse.build(
                {
                    "description": "A Minecraft Server",
                    "version": {"name": "1.8-pre1", "protocol": 44},
                }
            )

    def test_favicon(self):
        response = JavaServerResponse.build(
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
                "favicon": "data:image/png;base64,foo",
            }
        )

        assert response.icon == "data:image/png;base64,foo"

    def test_favicon_missing(self):
        response = JavaServerResponse.build(
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
            }
        )

        assert response.icon is None


class TestPingResponsePlayers:
    def test_invalid(self):
        with pytest.raises(ValueError):
            JavaServerPlayers.build("foo")  # type: ignore[arg-type]

    def test_max_missing(self):
        with pytest.raises(ValueError):
            JavaServerPlayers.build({"online": 5})

    def test_max_invalid(self):
        with pytest.raises(TypeError):
            JavaServerPlayers.build({"max": "foo", "online": 5})

    def test_online_missing(self):
        with pytest.raises(ValueError):
            JavaServerPlayers.build({"max": 20})

    def test_online_invalid(self):
        with pytest.raises(TypeError):
            JavaServerPlayers.build({"max": 20, "online": "foo"})

    def test_valid(self):
        players = JavaServerPlayers.build({"max": 20, "online": 5})

        assert players.max == 20
        assert players.online == 5

    def test_sample(self):
        players = JavaServerPlayers.build(
            {
                "max": 20,
                "online": 1,
                "sample": [{"name": "Dinnerbone", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"}],
            }
        )

        assert players.list is not None
        assert players.list[0].name == "Dinnerbone"

    def test_sample_invalid(self):
        with pytest.raises(TypeError):
            JavaServerPlayers.build({"max": 20, "online": 1, "sample": "foo"})

    def test_sample_missing(self):
        players = JavaServerPlayers.build({"max": 20, "online": 1})
        assert players.list is None


class TestPingResponsePlayersPlayer:
    def test_invalid(self):
        with pytest.raises(ValueError):
            JavaServerPlayer.build("foo")  # type: ignore[arg-type]

    def test_name_missing(self):
        with pytest.raises(ValueError):
            JavaServerPlayer.build({"id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"})

    def test_name_invalid(self):
        with pytest.raises(TypeError):
            JavaServerPlayer.build({"name": {}, "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"})

    def test_id_missing(self):
        with pytest.raises(ValueError):
            JavaServerPlayer.build({"name": "Dinnerbone"})

    def test_id_invalid(self):
        with pytest.raises(TypeError):
            JavaServerPlayer.build({"name": "Dinnerbone", "id": {}})

    def test_valid(self):
        player = JavaServerPlayer.build({"name": "Dinnerbone", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"})

        assert player.name == "Dinnerbone"
        assert player.uuid == "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"


class TestPingResponseVersion:
    def test_invalid(self):
        with pytest.raises(ValueError):
            JavaServerVersion.build("foo")  # type: ignore[arg-type]

    def test_protocol_missing(self):
        with pytest.raises(ValueError):
            JavaServerVersion.build({"name": "foo"})

    def test_protocol_invalid(self):
        with pytest.raises(TypeError):
            JavaServerVersion.build({"name": "foo", "protocol": "bar"})

    def test_name_missing(self):
        with pytest.raises(ValueError):
            JavaServerVersion.build({"protocol": 5})

    def test_name_invalid(self):
        with pytest.raises(TypeError):
            JavaServerVersion.build({"name": {}, "protocol": 5})

    def test_valid(self):
        players = JavaServerVersion.build({"name": "foo", "protocol": 5})

        assert players.name == "foo"
        assert players.protocol == 5
