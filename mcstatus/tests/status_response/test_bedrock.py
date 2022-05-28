from pytest import fixture, mark

from mcstatus.status_response import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion


@fixture(scope="module")
def build():
    return BedrockStatusResponse.build(
        [
            "MCPE",
            "§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
            "422",
            "1.18.100500",
            "1",
            "69",
            "3767071975391053022",
            "map name here",
            "Default",
            "1",
            "19132",
            "-1",
            "3",
        ],
        123.0,
    )


class TestBedrockStatusResponse:
    @mark.parametrize("field", ["players", "version", "motd", "latency", "map_name", "gamemode"])
    def test_have_field(self, field, build):
        assert hasattr(build, field)

    @mark.parametrize(
        "field,type_",
        [
            ("players", BedrockStatusPlayers),
            ("version", BedrockStatusVersion),
            ("motd", str),
            ("latency", float),
            ("map_name", str),
            ("gamemode", str),
        ],
    )
    def test_types(self, build, field, type_):
        assert isinstance(getattr(build, field), type_)

    @mark.parametrize(
        "field,value",
        [
            ("motd", "§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r"),
            ("latency", 123.0),
            ("map_name", "map name here"),
            ("gamemode", "Default"),
        ],
    )
    def test_values(self, build, field, value):
        assert getattr(build, field) == value


class TestBedrockStatusPlayers:
    @mark.parametrize("field", ["online", "max"])
    def test_have_field(self, field, build):
        assert hasattr(build.players, field)

    @mark.parametrize("field,type_", [("online", int), ("max", int)])
    def test_types(self, build, field, type_):
        assert isinstance(getattr(build.players, field), type_)

    @mark.parametrize("field,value", [("online", 1), ("max", 69)])
    def test_values(self, build, field, value):
        assert getattr(build.players, field) == value


class TestBedrockStatusVersion:
    @mark.parametrize("field", ["name", "protocol", "brand"])
    def test_have_field(self, field, build):
        assert hasattr(build.version, field)

    @mark.parametrize("field,type_", [("name", str), ("protocol", int), ("brand", str)])
    def test_types(self, build, field, type_):
        assert isinstance(getattr(build.version, field), type_)

    @mark.parametrize("field,value", [("name", "1.18.100500"), ("protocol", 422), ("brand", "MCPE")])
    def test_values(self, build, field, value):
        assert getattr(build.version, field) == value
