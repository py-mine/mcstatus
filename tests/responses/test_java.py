import pytest

from mcstatus.motd import Motd
from mcstatus.responses import JavaStatusPlayer, JavaStatusPlayers, JavaStatusResponse, JavaStatusVersion
from tests.responses import BaseResponseTest


@BaseResponseTest.construct
class TestJavaStatusResponse(BaseResponseTest):
    RAW = {
        "players": {"max": 20, "online": 0},
        "version": {"name": "1.8-pre1", "protocol": 44},
        "description": "A Minecraft Server",
        "enforcesSecureChat": True,
        "favicon": "data:image/png;base64,foo",
    }

    EXPECTED_VALUES = [
        ("players", JavaStatusPlayers(0, 20, None)),
        ("version", JavaStatusVersion("1.8-pre1", 44)),
        ("motd", Motd.parse("A Minecraft Server", bedrock=False)),
        ("latency", 0),
        ("enforces_secure_chat", True),
        ("icon", "data:image/png;base64,foo"),
        ("raw", RAW),
        ("forge_data", None),
    ]
    OPTIONAL_FIELDS = (
        [("favicon", "icon"), ("enforcesSecureChat", "enforces_secure_chat")],
        {
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "description": "A Minecraft Server",
            "enforcesSecureChat": True,
            "favicon": "data:image/png;base64,foo",
        },
    )

    @pytest.fixture(scope="class")
    def build(self) -> JavaStatusResponse:
        return JavaStatusResponse.build(self.RAW)  # type: ignore # dict[str, Unknown] cannot be assigned to TypedDict

    def test_as_dict(self, build: JavaStatusResponse):
        assert build.as_dict() == {
            "enforces_secure_chat": True,
            "forge_data": None,
            "icon": "data:image/png;base64,foo",
            "latency": 0,
            "motd": "A Minecraft Server",
            "players": {"max": 20, "online": 0, "sample": None},
            "raw": {
                "description": "A Minecraft Server",
                "enforcesSecureChat": True,
                "favicon": "data:image/png;base64,foo",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
            },
            "version": {"name": "1.8-pre1", "protocol": 44},
        }


@BaseResponseTest.construct
class TestJavaStatusPlayers(BaseResponseTest):
    EXPECTED_VALUES = [
        ("max", 20),
        ("online", 0),
        (
            "sample",
            [
                JavaStatusPlayer("foo", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"),
                JavaStatusPlayer("bar", "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"),
                JavaStatusPlayer("baz", "40e8d003-8872-412d-b09a-4431a5afcbd4"),
            ],
        ),
    ]
    OPTIONAL_FIELDS = (
        [("sample", "sample")],
        {
            "max": 20,
            "online": 0,
            "sample": [
                {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},
                {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"},
                {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4"},
            ],
        },
    )

    @pytest.fixture(scope="class")
    def build(self) -> JavaStatusPlayers:
        return JavaStatusPlayers.build(
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

    def test_empty_sample_turns_into_empty_list(self) -> None:
        assert JavaStatusPlayers.build({"max": 20, "online": 0, "sample": []}).sample == []


@BaseResponseTest.construct
class TestJavaStatusPlayer(BaseResponseTest):
    EXPECTED_VALUES = [("name", "foo"), ("id", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")]

    @pytest.fixture(scope="class")
    def build(self) -> JavaStatusPlayer:
        return JavaStatusPlayer.build({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})

    def test_id_field_the_same_as_uuid(self) -> None:
        unique = object()
        build = JavaStatusPlayer.build({"name": "foo", "id": unique})  # type: ignore[assignment]
        assert build.id is build.uuid
        assert build.uuid is unique


@BaseResponseTest.construct
class TestJavaStatusVersion(BaseResponseTest):
    EXPECTED_VALUES = [("name", "1.8-pre1"), ("protocol", 44)]

    @pytest.fixture(scope="class")
    def build(self) -> JavaStatusVersion:
        return JavaStatusVersion.build({"name": "1.8-pre1", "protocol": 44})
