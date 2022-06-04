from pytest import fixture, mark, raises

from mcstatus.status_response import JavaStatusPlayer, JavaStatusPlayers, JavaStatusResponse, JavaStatusVersion
from mcstatus.tests.status_response import does_not_raise


class TestJavaStatusResponse:
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

    @mark.parametrize("exclude_field", ["players", "version", "description"])
    def test_invalid_validating(self, exclude_field):
        raw = {
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "description": "A Minecraft Server",
        }
        raw.pop(exclude_field)
        with raises(ValueError):
            JavaStatusResponse.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            # players and version will be checked in their own tests
            ("description", str),
            ("favicon", str),
        ],
    )
    @mark.parametrize("field_value", ["foo", 123, 1.4, True, None, [], {}])
    def test_invalid_types(self, field, field_value, expected_type):
        raw = {
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "description": "A Minecraft Server",
            "favicon": "data:image/png;base64,foo",
            field: field_value,
        }

        if isinstance(field_value, expected_type) or field == "favicon":
            my_raises = does_not_raise()
        else:
            my_raises = raises(TypeError)

        with my_raises:
            JavaStatusResponse.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("players", JavaStatusPlayers),
            ("version", JavaStatusVersion),
            ("motd", str),
            ("icon", str),
        ],
    )
    def test_types(self, build, field, expected_type):
        assert isinstance(getattr(build, field), expected_type)

    @mark.parametrize(
        "field,value",
        [
            ("players", JavaStatusPlayers(0, 20, None)),
            ("version", JavaStatusVersion("1.8-pre1", 44)),
            ("motd", "A Minecraft Server"),
            ("latency", None),
            ("icon", "data:image/png;base64,foo"),
        ],
    )
    def test_fields(self, build, field, value):
        assert getattr(build, field) == value

    def test_parse_description_strips_html_color_codes(self):
        assert JavaStatusResponse._parse_description(
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
            " ===============§f §lC§lr§le§la§lt§li§lv§le§lF§lu§ln ===============§f \n"
            " §lThe server has been updated to §l1.17.1"
        )

    @mark.parametrize(
        "input_value,expected_output",
        [
            ("test §2description", "test §2description"),
            ("§8§lfoo", "§8§lfoo"),
        ],
    )
    def test_parse_description_full_match(self, input_value, expected_output):
        assert JavaStatusResponse._parse_description(input_value) == expected_output

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
                {
                    # We don't care in which order the style prefixes are, allow any
                    "§l§o§7foo§6bar.",
                    "§l§7§ofoo§6bar.",
                    "§o§l§7foo§6bar.",
                    "§o§7§lfoo§6bar.",
                    "§7§o§lfoo§6bar.",
                    "§7§l§ofoo§6bar.",
                },
            ),
            (
                [{"bold": True, "italic": True, "color": "gray", "text": "foo"}, {"color": "gold", "text": "bar"}],
                {
                    "§l§o§7foo§6bar",
                    "§l§7§ofoo§6bar",
                    "§o§l§7foo§6bar",
                    "§o§7§lfoo§6bar",
                    "§7§o§lfoo§6bar",
                    "§7§l§ofoo§6bar",
                },
            ),
        ],
    )
    def test_parse_description_in(self, input_value, expected_output):
        assert JavaStatusResponse._parse_description(input_value) in expected_output

    def test_icon_missing(self):
        response = JavaStatusResponse.build(
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
            }
        )

        assert response.icon is None


class TestJavaStatusPlayers:
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

    @mark.parametrize("exclude_field", ["max", "online"])
    def test_invalid_validating(self, exclude_field):
        with raises(ValueError):
            raw = {"max": 20, "online": 0}
            raw.pop(exclude_field)
            JavaStatusPlayers.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("max", int),
            ("online", int),
            ("sample", list),
        ],
    )
    @mark.parametrize("field_value", ["foo", 123, 1.4, True, None, [], {}])
    def test_invalid_types(self, field, field_value, expected_type):
        raw = {
            "max": 20,
            "online": 0,
            "sample": [
                {"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"},
                {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"},
                {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4"},
            ],
            field: field_value,
        }

        if isinstance(field_value, expected_type):
            my_raises = does_not_raise()
        else:
            my_raises = raises(TypeError)

        with my_raises:
            JavaStatusPlayers.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("max", int),
            ("online", int),
            ("sample", list),
        ],
    )
    def test_types(self, build, field, expected_type):
        assert isinstance(getattr(build, field), expected_type)

    @mark.parametrize(
        "field,value",
        [
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
        ],
    )
    def test_fields(self, build, field, value):
        assert getattr(build, field) == value

    def test_no_sample(self):
        response = JavaStatusPlayers.build({"max": 20, "online": 0})
        assert response.sample is None

    def test_empty_sample(self):
        response = JavaStatusPlayers.build({"max": 20, "online": 0, "sample": []})
        assert response.sample is None


class TestJavaStatusPlayer:
    @fixture(scope="class")
    def build(self):
        return JavaStatusPlayer.build({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})

    @mark.parametrize("exclude_field", ["name", "id"])
    def test_invalid_validating(self, exclude_field):
        raw = {"name": "bar", "id": "61699b2e-d327-4a01-9f1e-0ea8c3f06bc6"}
        raw.pop(exclude_field)
        with raises(ValueError):
            JavaStatusPlayer.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("name", str),
            ("id", str),
        ],
    )
    @mark.parametrize("field_value", ["foo", 123, 1.4, True, None, [], {}])
    def test_invalid_types(self, field, field_value, expected_type):
        raw = {"name": "baz", "id": "40e8d003-8872-412d-b09a-4431a5afcbd4", field: field_value}

        if isinstance(field_value, expected_type):
            my_raises = does_not_raise()
        else:
            my_raises = raises(TypeError)

        with my_raises:
            JavaStatusPlayer.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("name", str),
            ("uuid", str),
        ],
    )
    def test_types(self, build, field, expected_type):
        assert isinstance(getattr(build, field), expected_type)

    @mark.parametrize(
        "field,value",
        [("name", "foo"), ("uuid", "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")],
    )
    def test_fields(self, build, field, value):
        assert getattr(build, field) == value


class TestJavaStatusVersion:
    @fixture(scope="class")
    def build(self):
        return JavaStatusVersion.build({"name": "1.8-pre1", "protocol": 44})

    @mark.parametrize("exclude_field", ["name", "protocol"])
    def test_invalid_validating(self, exclude_field):
        raw = {"name": "1.8-pre1", "protocol": 44}
        raw.pop(exclude_field)
        with raises(ValueError):
            JavaStatusVersion.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("name", str),
            ("protocol", int),
        ],
    )
    @mark.parametrize("field_value", ["foo", 123, 1.4, True, None, [], {}])
    def test_invalid_types(self, field, field_value, expected_type):
        raw = {"name": "1.8-pre1", "protocol": 44, field: field_value}

        if isinstance(field_value, expected_type):
            my_raises = does_not_raise()
        else:
            my_raises = raises(TypeError)

        with my_raises:
            JavaStatusVersion.build(raw)

    @mark.parametrize(
        "field,expected_type",
        [
            ("name", str),
            ("protocol", int),
        ],
    )
    def test_types(self, build, field, expected_type):
        assert isinstance(getattr(build, field), expected_type)

    @mark.parametrize(
        "field,value",
        [("name", "1.8-pre1"), ("protocol", 44)],
    )
    def test_fields(self, build, field, value):
        assert getattr(build, field) == value
