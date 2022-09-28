from pytest import fixture, mark

from mcstatus.status_response import JavaStatusPlayer, JavaStatusPlayers, JavaStatusResponse, JavaStatusVersion
from tests.status_response import BaseStatusResponseTest


@BaseStatusResponseTest.construct
class TestJavaStatusResponse(BaseStatusResponseTest):
    EXPECTED_VALUES = [
        ("players", JavaStatusPlayers(0, 20, None)),
        ("version", JavaStatusVersion("1.8-pre1", 44)),
        ("motd", "A Minecraft Server"),
        ("latency", None),
        ("icon", "data:image/png;base64,foo"),
    ]
    BUILD_METHOD_VALIDATION = (
        ["players", "version", "description"],
        [],
        {
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "description": "A Minecraft Server",
            "favicon": "data:image/png;base64,foo",
        },
    )
    # `BUILD_METHOD_VALIDATION[2]` has the same value, as we need. so why not reuse it?
    OPTIONAL_FIELDS = [("favicon", "icon")], BUILD_METHOD_VALIDATION[2]

    @fixture(scope="class")
    def build(self):
        return JavaStatusResponse.build(
            {
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
                "description": "A Minecraft Server",
                "favicon": "data:image/png;base64,foo",
            }
        )

    def test_parse_description_strips_html_color_codes(self):
        assert JavaStatusResponse._parse_motd(
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
        ) == (
            " §m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§f §lC§lr§le§la§lt§li§lv§le§lF§lu§ln"
            " §m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§m=§f \n"
            " §lThe server has been updated to §l1.17.1"
        )

    def test_parse_description_with_string(self):
        assert JavaStatusResponse._parse_motd("test §2description") == "test §2description"

    @mark.parametrize(
        "input_value,expected_output",
        [
            (
                {
                    "extra": [
                        {"bold": True, "italic": True, "color": "gray", "text": "foo"},
                        {"color": "gold", "text": "bar"},
                    ],
                    "text": ".",
                },
                "§7§l§ofoo§6bar.",
            ),
            (
                [{"bold": True, "italic": True, "color": "gray", "text": "foo"}, {"color": "gold", "text": "bar"}],
                "§7§l§ofoo§6bar",
            ),
        ],
    )
    def test_parse_description_with_dict_and_list(self, input_value, expected_output):
        assert JavaStatusResponse._parse_motd(input_value) == expected_output


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
    BUILD_METHOD_VALIDATION = (
        ["max", "online"],
        ["sample"],
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
    # `BUILD_METHOD_VALIDATION[2]` has the same value, as we need. so why not reuse it?
    OPTIONAL_FIELDS = [("sample", "sample")], BUILD_METHOD_VALIDATION[2]

    @fixture(scope="class")
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
    BUILD_METHOD_VALIDATION = ["name", "id"], [], {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"}

    @fixture(scope="class")
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
    BUILD_METHOD_VALIDATION = ["name", "protocol"], [], {"name": "1.8-pre1", "protocol": 44}

    @fixture(scope="class")
    def build(self):
        return JavaStatusVersion.build({"name": "1.8-pre1", "protocol": 44})
