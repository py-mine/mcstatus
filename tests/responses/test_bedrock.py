import typing as t

import pytest

from mcstatus.motd import Motd
from mcstatus.responses import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion
from tests.responses import BaseResponseTest


@pytest.fixture(scope="module")
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


@BaseResponseTest.construct
class TestBedrockStatusResponse(BaseResponseTest):
    EXPECTED_VALUES: t.ClassVar = [
        ("motd", Motd.parse("§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r", bedrock=True)),
        ("latency", 123.0),
        ("map_name", "map name here"),
        ("gamemode", "Default"),
    ]
    EXPECTED_TYPES: t.ClassVar = [
        ("players", BedrockStatusPlayers),
        ("version", BedrockStatusVersion),
    ]

    @pytest.fixture(scope="class")
    def build(self, build):  # pyright: ignore[reportIncompatibleMethodOverride]
        return build

    @pytest.mark.parametrize(("field", "pop_index"), [("map_name", 7), ("gamemode", 7), ("gamemode", 8)])
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

    def test_as_dict(self, build: BedrockStatusResponse):
        assert build.as_dict() == {
            "gamemode": "Default",
            "latency": 123.0,
            "map_name": "map name here",
            "motd": "§4G§6a§ey§2B§1o§9w§ds§4e§6r",
            "players": {"max": 69, "online": 1},
            "version": {"brand": "MCPE", "name": "1.18.100500", "protocol": 422},
        }


@BaseResponseTest.construct
class TestBedrockStatusPlayers(BaseResponseTest):
    EXPECTED_VALUES: t.ClassVar = [("online", 1), ("max", 69)]

    @pytest.fixture(scope="class")
    def build(self, build):  # pyright: ignore[reportIncompatibleMethodOverride]
        return build.players


@BaseResponseTest.construct
class TestBedrockStatusVersion(BaseResponseTest):
    EXPECTED_VALUES: t.ClassVar = [("name", "1.18.100500"), ("protocol", 422), ("brand", "MCPE")]

    @pytest.fixture(scope="class")
    def build(self, build):  # pyright: ignore[reportIncompatibleMethodOverride]
        return build.version
