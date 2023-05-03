from pytest import fixture, mark

from mcstatus.motd import Motd
from mcstatus.status_response import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion
from tests.status_response import BaseStatusResponseTest


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


@BaseStatusResponseTest.construct
class TestBedrockStatusResponse(BaseStatusResponseTest):
    EXPECTED_VALUES = [
        ("motd", Motd.parse("§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r", bedrock=True)),
        ("latency", 123.0),
        ("map_name", "map name here"),
        ("gamemode", "Default"),
    ]
    EXPECTED_TYPES = [
        ("players", BedrockStatusPlayers),
        ("version", BedrockStatusVersion),
    ]

    @fixture(scope="class")
    def build(self, build):
        return build

    @mark.parametrize("field,pop_index", [("map_name", 7), ("gamemode", 7), ("gamemode", 8)])
    def test_optional_parameters_is_none(self, field, pop_index):
        parameters = [
            "MCPE",
            "§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
            "422",
            "1.18.100500",
            "1",
            "69",
            "3767071975391053022",
            "map name here",
            "Default",
        ]
        parameters.pop(pop_index)
        # remove all variables after `pop_index`
        if len(parameters) - 1 == pop_index:
            parameters.pop(pop_index)

        build = BedrockStatusResponse.build(parameters, 123.0)
        assert getattr(build, field) is None


@BaseStatusResponseTest.construct
class TestBedrockStatusPlayers(BaseStatusResponseTest):
    EXPECTED_VALUES = [("online", 1), ("max", 69)]

    @fixture(scope="class")
    def build(self, build):
        return build.players


@BaseStatusResponseTest.construct
class TestBedrockStatusVersion(BaseStatusResponseTest):
    EXPECTED_VALUES = [("name", "1.18.100500"), ("protocol", 422), ("brand", "MCPE")]

    @fixture(scope="class")
    def build(self, build):
        return build.version
