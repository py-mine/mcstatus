import typing as t

import pytest

from mcstatus.motd import Motd
from mcstatus.responses import LegacyStatusPlayers, LegacyStatusResponse, LegacyStatusVersion
from tests.responses import BaseResponseTest


@pytest.fixture(scope="module")
def build():
    return LegacyStatusResponse.build(
        [
            "47",
            "1.4.2",
            "A Minecraft Server",
            "0",
            "20",
        ],
        123.0,
    )


@t.final
@BaseResponseTest.construct
class TestLegacyStatusResponse(BaseResponseTest):
    EXPECTED_VALUES: t.ClassVar = [
        ("motd", Motd.parse("A Minecraft Server")),
        ("latency", 123.0),
    ]
    EXPECTED_TYPES: t.ClassVar = [
        ("players", LegacyStatusPlayers),
        ("version", LegacyStatusVersion),
    ]

    @pytest.fixture(scope="class")
    def build(self, build: LegacyStatusResponse) -> LegacyStatusResponse:
        return build

    def test_as_dict(self, build: LegacyStatusResponse):
        assert build.as_dict() == {
            "latency": 123.0,
            "motd": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.4.2", "protocol": 47},
        }


@t.final
@BaseResponseTest.construct
class TestLegacyStatusPlayers(BaseResponseTest):
    EXPECTED_VALUES: t.ClassVar = [("online", 0), ("max", 20)]

    @pytest.fixture(scope="class")
    def build(self, build: LegacyStatusResponse) -> LegacyStatusPlayers:
        return build.players


@t.final
@BaseResponseTest.construct
class TestLegacyStatusVersion(BaseResponseTest):
    EXPECTED_VALUES: t.ClassVar = [("name", "1.4.2"), ("protocol", 47)]

    @pytest.fixture(scope="class")
    def build(self, build: LegacyStatusResponse) -> LegacyStatusVersion:
        return build.version
