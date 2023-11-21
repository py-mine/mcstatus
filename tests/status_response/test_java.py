import pytest

from mcstatus.motd import Motd
from mcstatus.status_response import JavaStatusPlayer, JavaStatusPlayers, JavaStatusResponse, JavaStatusVersion
from tests.status_response import BaseStatusResponseTest


@BaseStatusResponseTest.construct
class TestJavaStatusResponse(BaseStatusResponseTest):
    RAW = {
        "players": {"max": 20, "online": 0},
        "version": {"name": "1.8-pre1", "protocol": 44},
        "description": "A Minecraft Server",
        "favicon": "data:image/png;base64,foo",
    }

    EXPECTED_VALUES = [
        ("players", JavaStatusPlayers(0, 20, None)),
        ("version", JavaStatusVersion("1.8-pre1", 44)),
        ("motd", Motd.parse("A Minecraft Server", bedrock=False)),
        ("latency", 0),
        ("icon", "data:image/png;base64,foo"),
        ("raw", RAW),
    ]
    OPTIONAL_FIELDS = [("favicon", "icon")], {
        "players": {"max": 20, "online": 0},
        "version": {"name": "1.8-pre1", "protocol": 44},
        "description": "A Minecraft Server",
        "favicon": "data:image/png;base64,foo",
    }

    @pytest.fixture(scope="class")
    def build(self):
        return JavaStatusResponse.build(self.RAW)  # type: ignore # dict[str, Unknown] cannot be assigned to TypedDict

    @pytest.mark.parametrize("value", (True, False, object()))
    def test_enforces_secure_chat(self, value):
        raw = self.RAW.copy()
        raw["enforcesSecureChat"] = value
        assert JavaStatusResponse.build(raw, 0).enforces_secure_chat is value  # type: ignore # dict[str, Unknown] cannot be assigned to TypedDict


@BaseStatusResponseTest.construct
class TestJavaStatusPlayers(BaseStatusResponseTest):
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
    OPTIONAL_FIELDS = [("sample", "sample")], {
        "max": 20,
        "online": 0,
        "sample": [
            {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},
            {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"},
            {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4"},
        ],
    }

    @pytest.fixture(scope="class")
    def build(self):
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

    def test_empty_sample_turns_into_empty_list(self):
        assert JavaStatusPlayers.build({"max": 20, "online": 0, "sample": []}).sample == []


@BaseStatusResponseTest.construct
class TestJavaStatusPlayer(BaseStatusResponseTest):
    EXPECTED_VALUES = [("name", "foo"), ("id", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")]

    @pytest.fixture(scope="class")
    def build(self):
        return JavaStatusPlayer.build({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})

    def test_id_field_the_same_as_uuid(self):
        build = JavaStatusPlayer.build({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})
        assert build.id is build.uuid

        build.id = unique = object()  # type: ignore[assignment]
        assert unique is build.uuid


@BaseStatusResponseTest.construct
class TestJavaStatusVersion(BaseStatusResponseTest):
    EXPECTED_VALUES = [("name", "1.8-pre1"), ("protocol", 44)]

    @pytest.fixture(scope="class")
    def build(self):
        return JavaStatusVersion.build({"name": "1.8-pre1", "protocol": 44})
