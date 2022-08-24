# TODO: Delete this file, after 2022-08

from warnings import catch_warnings

from _pytest.fixtures import SubRequest
from pytest import deprecated_call, fixture, mark

from mcstatus.status_response import (
    BedrockStatusPlayers,
    BedrockStatusResponse,
    BedrockStatusVersion,
    JavaStatusPlayer,
    JavaStatusPlayers,
    JavaStatusResponse,
    JavaStatusVersion,
)


class TestDeprecatedJavaStatusResponse:
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

    def test_description_field_raise_warning(self, build):
        with deprecated_call():
            build.description

    def test_init_old_signature_raise_warning(self):
        with deprecated_call():
            JavaStatusResponse(
                {
                    "players": {"max": 20, "online": 0},
                    "version": {"name": "1.8-pre1", "protocol": 44},
                    "description": "A Minecraft Server",
                    "favicon": "data:image/png;base64,foo",
                }
            )

    @mark.filterwarnings("error")
    def test_init_new_signature_not_raise_warning(self):
        JavaStatusResponse(
            players=JavaStatusPlayers(max=20, online=0, sample=[]),
            version=JavaStatusVersion(name="1.8-pre1", protocol=44),
            motd="A Minecraft Server",
            latency=123.0,
            icon="data:image/png;base64,foo",
        )

    def test_deprecated_description_field_in(self):
        assert hasattr(JavaStatusResponse, "description")

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_description_field_have_correct_value(self, build):
        assert build.description == "A Minecraft Server"

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_description_have_correct_type(self, build):
        assert isinstance(build.description, str)

    @mark.parametrize("field,type_class", [("players", JavaStatusResponse.Players), ("version", JavaStatusResponse.Version)])
    def test_deprecated_fields_have_correct_class(self, build, field, type_class):
        assert type(getattr(build, field)) is type_class


class TestDeprecatedJavaStatusResponsePlayers:
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

    def test_init_old_signature_raise_warning(self):
        with deprecated_call():
            JavaStatusResponse.Players({"max": 20, "online": 0})

    @mark.filterwarnings("error")
    def test_init_new_signature_not_raise_warning(self):
        JavaStatusResponse.Players(max=20, online=0, sample=[])

    def test_deprecated_object_same_as_new(self):
        """If we forgot overwrite `__eq__` method in child class, it will fail."""
        assert JavaStatusResponse.Players(max=20, online=0, sample=[]) == JavaStatusPlayers(max=20, online=0, sample=[])

    def test_repr_return_correct_class(self, build):
        """If we forgot overwrite `__repr__` method in child class,

        it will output `JavaStatusResponse.Players(...)` instead of `JavaStatusPlayers(...)`.
        """
        assert repr(build).startswith("JavaStatusPlayers")

    def test_deprecated_player_class_in(self):
        assert hasattr(JavaStatusResponse.Players, "Player")

    def test_sample_have_correct_class(self, build):
        assert type(build.sample[0]) is JavaStatusResponse.Players.Player


class TestDeprecatedJavaStatusResponsePlayer:
    @fixture(scope="class")
    def build(self) -> JavaStatusResponse.Players.Player:
        with catch_warnings(record=True):
            return JavaStatusResponse.Players.Player({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})

    def test_init_old_signature_raise_warning(self):
        with deprecated_call():
            JavaStatusResponse.Players.Player({"name": "foo", "id": "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"})

    @mark.filterwarnings("error")
    def test_init_new_signature_not_raise_warning(self):
        JavaStatusResponse.Players.Player(name="foo", id="0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")

    def test_deprecated_object_same_as_new(self, build):
        """If we forgot overwrite `__eq__` method in child class, it will fail."""
        assert build == JavaStatusPlayer(name="foo", id="0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89")

    def test_repr_return_correct_class(self, build):
        """If we forgot overwrite `__repr__` method in child class,

        it will output `JavaStatusResponse.Players.Player(...)` instead of `JavaStatusPlayer(...)`.
        """
        assert repr(build).startswith("JavaStatusPlayer")

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_fields_values(self, build):
        assert build.id == "0b3717c4-f45d-47c8-b8e2-3d9ff6f93a89"


class TestDeprecatedJavaStatusResponseVersion:
    @fixture(scope="class")
    def build(self) -> JavaStatusResponse.Version:
        with catch_warnings(record=True):
            return JavaStatusResponse.Version({"name": "1.8-pre1", "protocol": 44})

    def test_init_old_signature_raise_warning(self):
        with deprecated_call():
            JavaStatusResponse.Version({"name": "1.8-pre1", "protocol": 44})

    @mark.filterwarnings("error")
    def test_init_new_signature_not_raise_warning(self):
        JavaStatusResponse.Version(name="1.8-pre1", protocol=44)

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_object_same_as_new(self, build):
        """If we forgot overwrite `__eq__` method in child class, it will fail."""
        assert build == JavaStatusVersion(name="1.8-pre1", protocol=44)

    def test_repr_return_correct_class(self, build):
        """If we forgot overwrite `__repr__` method in child class,

        it will output `JavaStatusResponse.Version(...)` instead of `JavaStatusVersion(...)`.
        """
        assert repr(build).startswith("JavaStatusVersion")


# bedrock time


class TestDeprecatedBedrockStatusResponse:
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

    @mark.parametrize("field", ["players_online", "players_max", "map"])
    def test_deprecated_fields_raise_warning(self, build, field):
        with deprecated_call():
            getattr(build, field)

    def test_init_old_signature_raise_warning(self):
        with deprecated_call():
            BedrockStatusResponse(
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

    @mark.filterwarnings("error")
    def test_init_new_signature_not_raise_warning(self):
        BedrockStatusResponse(
            players=BedrockStatusPlayers(max=20, online=0),
            version=BedrockStatusVersion(name="1.18.100500", protocol=422, brand="MCPE"),
            motd="§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
            latency=123.0,
            map_name="map name here",
            gamemode="Default",
        )

    @mark.parametrize("field", ["players_online", "players_max", "map"])
    def test_deprecated_fields_in(self, field):
        assert hasattr(BedrockStatusResponse, field)

    @mark.filterwarnings("ignore::DeprecationWarning")
    @mark.parametrize("field,value", [("players_online", 1), ("players_max", 69), ("map", "map name here")])
    def test_deprecated_fields_have_correct_value(self, build, field, value):
        assert getattr(build, field) == value

    @mark.filterwarnings("ignore::DeprecationWarning")
    @mark.parametrize("field,value", [("players_online", int), ("players_max", int), ("map", str)])
    def test_deprecated_fields_have_correct_type(self, build, field, value):
        assert isinstance(getattr(build, field), value)

    def test_version_field_have_correct_class(self, build):
        assert type(build.version) is BedrockStatusResponse.Version


class TestDeprecatedBedrockStatusResponseVersion:
    @fixture(scope="class")
    def build(self) -> BedrockStatusResponse.Version:
        with catch_warnings(record=True):
            return BedrockStatusResponse.Version(protocol=422, brand="MCPE", version="1.18.100500")

    def test_version_field_raise_warning(self, build):
        with deprecated_call():
            build.version

    def test_init_old_signature_raise_warning(self):
        with deprecated_call():
            BedrockStatusResponse.Version(protocol=422, brand="MCPE", version="1.18.100500")

    @mark.filterwarnings("error")
    def test_init_new_signature_not_raise_warning(self):
        BedrockStatusResponse.Version(name="1.18.100500", protocol=422, brand="MCPE")

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_version_field_in(self, build):
        assert hasattr(build, "version")

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_version_field_have_correct_value(self, build):
        assert build.version == "1.18.100500"

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_version_field_have_correct_type(self, build):
        assert isinstance(build.version, str)

    @mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_object_same_as_new(self, build):
        """If we forgot overwrite `__eq__` method in child class, it will fail."""
        assert build == BedrockStatusVersion(name="1.18.100500", protocol=422, brand="MCPE")

    def test_repr_return_correct_class(self, build):
        """If we forgot overwrite `__repr__` method in child class,

        it will output `BedrockStatusResponse.Version(...)` instead of `BedrockStatusVersion(...)`.
        """
        assert repr(build).startswith("BedrockStatusVersion")


class TestDeprecatedBedrockStatusResponseVersionPositionalArguments:
    """As you noticed, the old signature have different positional arguments, so `__init__` should also check types."""

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

    @mark.filterwarnings("ignore::DeprecationWarning")
    @mark.parametrize("field,expected", [("version", "1.18.100500"), ("protocol", 422), ("brand", "MCPE")])
    def test_old_expected_in_fields(self, build, field, expected):
        assert getattr(build, field) == expected
