# TODO: Delete this file, after 2022-08

from warnings import catch_warnings

from _pytest.fixtures import SubRequest
from pytest import fixture, mark

from mcstatus.status_response import (
    BedrockStatusPlayers,
    BedrockStatusResponse,
    BedrockStatusVersion,
    JavaStatusPlayer,
    JavaStatusPlayers,
    JavaStatusResponse,
    JavaStatusVersion,
)
from tests.status_response import BaseStatusResponseTest


@BaseStatusResponseTest.construct
class TestDeprecatedJavaStatusResponse(BaseStatusResponseTest):
    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [
        ("description", "A Minecraft Server"),
        (
            "raw",
            {
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
                "description": "A Minecraft Server",
                "favicon": "data:image/png;base64,foo",
            },
        ),
    ]
    DEPRECATED_FIELDS = ["description", "raw"]
    DEPRECATED_OLD_INIT_PASSED_ARGS = (
        {
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "description": "A Minecraft Server",
            "favicon": "data:image/png;base64,foo",
        },
    )
    DEPRECATED_NEW_INIT_PASSED_ARGS = {
        "players": JavaStatusPlayers(max=20, online=0, sample=[]),
        "version": JavaStatusVersion(name="1.8-pre1", protocol=44),
        "motd": "A Minecraft Server",
        "latency": 123.0,
        "icon": "data:image/png;base64,foo",
    }
    DEPRECATED_NESTED_CLASSES_USED = [("players", JavaStatusResponse.Players), ("version", JavaStatusResponse.Version)]

    @fixture(scope="class")
    def build(self) -> JavaStatusResponse:
        with catch_warnings(record=True):
            return JavaStatusResponse(
                {
                    "players": {"max": 20, "online": 0},
                    "version": {"name": "1.8-pre1", "protocol": 44},
                    "description": "A Minecraft Server",
                    "favicon": "data:image/png;base64,foo",
                }
            )

    def test_raw_field_give_correct_value_with_new_signature(self):
        assert JavaStatusResponse(
            players=JavaStatusPlayers(max=20, online=0, sample=[]),
            version=JavaStatusVersion(name="1.8-pre1", protocol=44),
            motd="A Minecraft Server",
            latency=123.0,
            icon="data:image/png;base64,foo",
        ).raw == {
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "description": "A Minecraft Server",
            "favicon": "data:image/png;base64,foo",
        }

    def test_raw_field_doesnt_give_favicon_if_is_none(self):
        assert (
            "favicon"
            not in JavaStatusResponse(
                players=JavaStatusPlayers(max=20, online=0, sample=[]),
                version=JavaStatusVersion(name="1.8-pre1", protocol=44),
                motd="A Minecraft Server",
                latency=123.0,
                icon=None,
            ).raw
        )


@BaseStatusResponseTest.construct
class TestDeprecatedJavaStatusResponsePlayers(BaseStatusResponseTest):
    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [
        ("max", 20),
        ("online", 0),
        (
            "sample",
            [
                JavaStatusPlayer(name="foo", id="0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"),
                JavaStatusPlayer(name="bar", id="61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"),
                JavaStatusPlayer(name="baz", id="40e8d003-8872-412d-b09a-4431a5afcbd4"),
            ],
        ),
    ]
    DEPRECATED_OLD_INIT_PASSED_ARGS = ({"max": 20, "online": 0},)
    DEPRECATED_NEW_INIT_PASSED_ARGS = {"max": 20, "online": 0, "sample": []}
    # `DEPRECATED_NEW_INIT_PASSED_ARGS` has the same value, as we need. so why not reuse it?
    DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE = JavaStatusPlayers, {
        "max": 20,
        "online": 0,
        "sample": [
            JavaStatusPlayer(name="foo", id="0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"),
            JavaStatusPlayer(name="bar", id="61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"),
            JavaStatusPlayer(name="baz", id="40e8d003-8872-412d-b09a-4431a5afcbd4"),
        ],
    }
    DEPRECATED_CLASS_REPR_MUST_START_WITH = "JavaStatusPlayers"

    @fixture(scope="class")
    def build(self) -> JavaStatusResponse.Players:
        with catch_warnings(record=True):
            return JavaStatusResponse.Players(
                {
                    "max": 20,
                    "online": 0,
                    "sample": [
                        {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},
                        {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"},
                        {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4"},
                    ],
                }
            )

    def test_sample_have_correct_class(self, build):
        assert type(build.sample[0]) is JavaStatusResponse.Players.Player


@BaseStatusResponseTest.construct
class TestDeprecatedJavaStatusResponsePlayer(BaseStatusResponseTest):
    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [("name", "foo"), ("id", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")]
    DEPRECATED_OLD_INIT_PASSED_ARGS = ({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},)
    DEPRECATED_NEW_INIT_PASSED_ARGS = {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"}
    # `DEPRECATED_NEW_INIT_PASSED_ARGS` has the same value, as we need. so why not reuse it?
    DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE = JavaStatusPlayer, DEPRECATED_NEW_INIT_PASSED_ARGS
    DEPRECATED_CLASS_REPR_MUST_START_WITH = "JavaStatusPlayer"

    @fixture(scope="class")
    def build(self) -> JavaStatusResponse.Players.Player:
        with catch_warnings(record=True):
            return JavaStatusResponse.Players.Player({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})


@BaseStatusResponseTest.construct
class TestDeprecatedJavaStatusResponseVersion(BaseStatusResponseTest):
    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [("name", "1.8-pre1"), ("protocol", 44)]
    DEPRECATED_OLD_INIT_PASSED_ARGS = ({"name": "1.8-pre1", "protocol": 44},)
    DEPRECATED_NEW_INIT_PASSED_ARGS = {"name": "1.8-pre1", "protocol": 44}
    # `DEPRECATED_NEW_INIT_PASSED_ARGS` has the same value, as we need. so why not reuse it?
    DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE = JavaStatusVersion, DEPRECATED_NEW_INIT_PASSED_ARGS
    DEPRECATED_CLASS_REPR_MUST_START_WITH = "JavaStatusVersion"

    @fixture(scope="class")
    def build(self) -> JavaStatusResponse.Version:
        with catch_warnings(record=True):
            return JavaStatusResponse.Version({"name": "1.8-pre1", "protocol": 44})


# bedrock time


@BaseStatusResponseTest.construct
class TestDeprecatedBedrockStatusResponse(BaseStatusResponseTest):
    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [("players_online", 1), ("players_max", 69), ("map", "map name here")]
    DEPRECATED_FIELDS = ["players_online", "players_max", "map"]
    DEPRECATED_OLD_INIT_PASSED_ARGS = {
        "protocol": 422,
        "brand": "MCPE",
        "version": "1.18.100500",
        "latency": 123.0,
        "players_online": 1,
        "players_max": 69,
        "motd": "§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
        "map_": "map name here",
        "gamemode": "Default",
    }
    DEPRECATED_NEW_INIT_PASSED_ARGS = {
        "players": BedrockStatusPlayers(max=20, online=0),
        "version": BedrockStatusVersion(name="1.18.100500", protocol=422, brand="MCPE"),
        "motd": "§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
        "latency": 123.0,
        "map_name": "map name here",
        "gamemode": "Default",
    }
    DEPRECATED_NESTED_CLASSES_USED = [("version", BedrockStatusResponse.Version)]

    @fixture(scope="class")
    def build(self) -> BedrockStatusResponse:
        with catch_warnings(record=True):
            return BedrockStatusResponse(
                protocol=422,
                brand="MCPE",
                version="1.18.100500",
                latency=123.0,
                players_online=1,
                players_max=69,
                motd="§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
                map_="map name here",
                gamemode="Default",
            )


@BaseStatusResponseTest.construct
class TestDeprecatedBedrockStatusResponseVersion(BaseStatusResponseTest):
    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [("version", "1.18.100500"), ("protocol", 422), ("brand", "MCPE")]
    DEPRECATED_FIELDS = ["version"]
    DEPRECATED_OLD_INIT_PASSED_ARGS = {"protocol": 422, "brand": "MCPE", "version": "1.18.100500"}
    DEPRECATED_NEW_INIT_PASSED_ARGS = {"name": "1.18.100500", "protocol": 422, "brand": "MCPE"}
    # `DEPRECATED_NEW_INIT_PASSED_ARGS` has the same value, as we need. so why not reuse it?
    DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE = (BedrockStatusVersion, DEPRECATED_NEW_INIT_PASSED_ARGS)
    DEPRECATED_CLASS_REPR_MUST_START_WITH = "BedrockStatusVersion"

    @fixture(scope="class")
    def build(self) -> BedrockStatusResponse.Version:
        with catch_warnings(record=True):
            return BedrockStatusResponse.Version(protocol=422, brand="MCPE", version="1.18.100500")


@BaseStatusResponseTest.construct
class TestDeprecatedBedrockStatusResponseVersionPositionalArguments(BaseStatusResponseTest):
    """As you noticed, the old signature have different positional arguments, so `__init__` should also check types."""

    pytestmark = mark.filterwarnings("ignore::DeprecationWarning")

    EXPECTED_VALUES = [("version", "1.18.100500"), ("protocol", 422), ("brand", "MCPE")]

    @fixture(scope="class", params=[True, False])
    def build(self, request: SubRequest) -> BedrockStatusResponse.Version:
        """Build `BedrockStatusResponse.Version` and cache it.

        :param request: If True, build with new signature. Else - old.
        """
        if request.param:
            return BedrockStatusResponse.Version("1.18.100500", 422, "MCPE")
        else:
            with catch_warnings(record=True):
                return BedrockStatusResponse.Version(422, "MCPE", "1.18.100500")
