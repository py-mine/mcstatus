from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple, Union

if TYPE_CHECKING:
    from typing_extensions import Self

from mcstatus.utils import deprecated

__all__ = [
    "STYLE_MAP",
    "AbstractDataclass",
    "MCStatusResponse",
    "JavaStatusResponse",
    "BedrockStatusResponse",
    "StatusPlayers",
    "JavaStatusPlayers",
    "BedrockStatusPlayers",
    "JavaStatusPlayer",
    "StatusVersion",
    "JavaStatusVersion",
    "BedrockStatusVersion",
]

STYLE_MAP = {
    "bold": "l",
    "italic": "o",
    "underlined": "n",
    "obfuscated": "k",
    "color": {
        "dark_red": "4",
        "red": "c",
        "gold": "6",
        "yellow": "e",
        "dark_green": "2",
        "green": "a",
        "aqua": "b",
        "dark_aqua": "3",
        "dark_blue": "1",
        "blue": "9",
        "light_purple": "d",
        "dark_purple": "5",
        "white": "f",
        "gray": "7",
        "dark_gray": "8",
        "black": "0",
    },
}


def _validate_data(raw: Dict[str, Any], who: str, required: Iterable[Tuple[str, type]]) -> None:
    """Ensure that all required keys are present, and have the specified type.

    :param raw: The raw dict answer to check.
    :param who: The name of the object that is checking the data. Example `status`, `player` etc.
    :param required: An iterable of string and type. The string is the required key which must be in `raw`, and
        the `type` is the type that the key must be. If you want to ignore check of the type, set the type to `object`.
    :raises ValueError: If the required keys are not present.
    :raises TypeError: If the required keys are not of the specified type.
    """
    for required_key, required_type in required:
        if required_key not in raw:
            raise ValueError(f"Invalid {who} object (no '{required_key}' value)")
        if not isinstance(raw[required_key], required_type):
            raise TypeError(
                f"Invalid {who} object (expected '{required_key}' to be {required_type}, was {type(raw[required_key])})"
            )


@dataclass
class AbstractDataclass(ABC):
    """Abstract base class for all dataclasses.

    We can't use just `ABC` because we need raise TypeError if we try to
    instantiate an abstract dataclass. Class which inherit from `ABC` raises
    it only if it has abstract methods.
    """

    def __new__(cls, *args, **kwargs):
        """Check if someone tries to instantiate an abstract class.

        :raises NotImplementedError: If someone tries to instantiate an abstract class.
        :return: The new instance of child abstract class.
        """
        if cls is AbstractDataclass or cls.__bases__[0] is AbstractDataclass:
            raise NotImplementedError("Cannot instantiate abstract class.")
        return super().__new__(cls)


@dataclass
class MCStatusResponse(AbstractDataclass):
    """Class for storing shared data from a status response.

    :param motd: Message Of The Day. Also known as `Description`.
    :param latency: Latency between a server and the client (you). In milliseconds.
    """

    players: StatusPlayers
    version: StatusVersion
    motd: str
    latency: float

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs) -> Self:
        """Build MCStatusResponse and check is it valid.

        :param args: Arguments in specific realisation.
        :param kwargs: Keyword arguments in specific realisation.
        :return: `MCStatusResponse` object.
        """
        raise NotImplementedError("You can't use abstract methods.")


@dataclass
class NewJavaStatusResponse(MCStatusResponse):
    """Class for storing JavaServer data from a status response.

    :param icon: Base64 encoded icon of the server. Can be unset.
    """

    players: JavaStatusPlayers
    version: JavaStatusVersion
    icon: Optional[str]

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> Self:
        """Build JavaStatusResponse and check is it valid.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (players, version, description) are not present.
        :raise TypeError: If the required keys (players - dict, version - dict, description - str)
            are not of the specified type.
        :return: `JavaStatusResponse` object.
        """
        _validate_data(raw, "status", [("players", dict), ("version", dict), ("description", str)])
        return cls(
            players=JavaStatusPlayers.build(raw["players"]),
            version=JavaStatusVersion.build(raw["version"]),
            motd=cls._parse_description(raw["description"]),
            icon=raw.get("favicon"),
            # This will be set later.
            latency=None,  # type: ignore[assignment]
        )

    @staticmethod
    def _parse_description(raw_description: Union[dict, list, str]) -> str:
        """Parse description from raw response.

        :param raw_description: Raw description.
        :return: Parsed description.
        """
        if isinstance(raw_description, str):
            return raw_description

        if isinstance(raw_description, dict):
            entries = raw_description.get("extra", [])
            end = raw_description["text"]
        else:
            entries = raw_description
            end = ""

        description = ""

        for entry in entries:
            for style_key, style_val in STYLE_MAP.items():
                if entry.get(style_key):
                    try:
                        if isinstance(style_val, dict):
                            style_val = style_val[entry[style_key]]

                        description += f"§{style_val}"
                    except KeyError:
                        pass  # ignoring these key errors strips out html color codes
            description += entry.get("text", "")

        return description + end


@dataclass
class NewBedrockStatusResponse(MCStatusResponse):
    """Class for storing BedrockServer data from a status response.

    :param map_name: Name of the map. Can be unset.
    :param gamemode: Gamemode of the server. Can be hidden.
    """

    players: BedrockStatusPlayers
    version: BedrockStatusVersion
    map_name: Optional[str]
    gamemode: Optional[str]

    @classmethod
    def build(cls, decoded_data: List[Any], latency: float) -> Self:
        """Build MCStatusResponse and check is it valid.

        :param decoded_data: Raw decoded response object.
        :param latency: Latency of the request.
        :return: `BedrockStatusResponse` object.
        """

        try:
            map_name = decoded_data[7]
        except IndexError:
            map_name = None
        try:
            gamemode = decoded_data[8]
        except IndexError:
            gamemode = None

        return cls(
            players=BedrockStatusPlayers(
                online=int(decoded_data[4]),
                max=int(decoded_data[5]),
            ),
            version=BedrockStatusVersion(
                name=decoded_data[3],
                protocol=int(decoded_data[2]),
                brand=decoded_data[0],
            ),
            motd=decoded_data[1],
            latency=latency,
            map_name=map_name,
            gamemode=gamemode,
        )


@dataclass
class StatusPlayers(AbstractDataclass):
    """Class for storing players info, like current online."""

    online: int
    max: int


@dataclass
class JavaStatusPlayers(StatusPlayers):
    """Class which extends a `StatusPlayers` class with list of players.

    :param players: List of players. Can be empty even if online > 0.
    """

    list: List[JavaStatusPlayer]

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> Self:
        """Build `JavaStatusPlayers` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (online, max) are not present.
        :raise TypeError: If the required keys (online - int, max - int, sample - list) are not of the specified type.
        :return: `JavaStatusPlayers` object.
        """
        _validate_data(raw, "players", [("online", int), ("max", int)])
        if "sample" in raw:
            _validate_data(raw, "players", [("sample", list)])
        return cls(
            online=raw["online"],
            max=raw["max"],
            list=[JavaStatusPlayer.build(player) for player in raw["sample"]] if "sample" in raw else [],
        )


@dataclass
class BedrockStatusPlayers(StatusPlayers):
    """Class which represents `BedrockStatusResponse` players field."""


@dataclass
class JavaStatusPlayer:
    """Class for storing player info. Only for Java."""

    name: str
    uuid: str

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> Self:
        """Build `JavaStatusPlayer` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (name, uuid) are not present.
        :raise TypeError: If the required keys (name - str, uuid - str) are not of the specified type.
        :return: `JavaStatusPlayer` object.
        """
        _validate_data(raw, "player", [("name", str), ("id", str)])
        return cls(name=raw["name"], uuid=raw["id"])


@dataclass
class StatusVersion(AbstractDataclass):
    """Class for storing version info.

    :param name: Version name. Example `1.18.0`.
    :param protocol: Version protocol. See https://minecraft.fandom.com/wiki/Protocol_version.
    """

    name: str
    protocol: int


@dataclass
class JavaStatusVersion(StatusVersion):
    """Class for storing Java version info."""

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> Self:
        """Build `JavaStatusVersion` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (name, protocol) are not present.
        :raise TypeError: If the required keys (name - str, protocol - int) are not of the specified type.
        :return: `JavaStatusVersion` object.
        """
        _validate_data(raw, "version", [("name", str), ("protocol", int)])
        return cls(name=raw["name"], protocol=raw["protocol"])


@dataclass
class BedrockStatusVersion(StatusVersion):
    """Class for storing Bedrock version info.

    :param brand: Like `MCPE` or another.
    """

    brand: Optional[str]


class JavaStatusResponse(NewJavaStatusResponse):
    """Class for storing JavaServer data from a status response.

    :param icon: Icon of the server. Can be unset. BASE64 encoded.
    """

    class Players(JavaStatusPlayers):
        """Deprecated class for `players` field.

        Use `JavaStatusPlayers` instead.
        """

        class Player(JavaStatusPlayer):
            """Deprecated class for player in `list` field.

            Use `JavaStatusPlayer` instead.
            """

            @property
            @deprecated(replacement="uuid", date="2022-08")
            def id(self):
                return self.uuid

            @deprecated(replacement="build", date="2022-08")
            def __init__(self, raw):
                return self.build(raw)

        @property
        @deprecated(replacement="list", date="2022-08")
        def sample(self):
            return self.list

    @deprecated(replacement="build", date="2022-08")
    def __init__(self, raw):
        return self.build(raw)


class BedrockStatusResponse(NewBedrockStatusResponse):
    class Version(BedrockStatusVersion):
        """Deprecated class for `version` field.

        Use `BedrockStatusVersion` instead.
        """

        @property
        @deprecated(replacement="name", date="2022-08")
        def version(self):
            return self.name

    @property
    @deprecated(replacement="players.online", date="2022-08")
    def players_online(self):
        return self.players.online

    @property
    @deprecated(replacement="players.max", date="2022-08")
    def players_max(self):
        return self.players.max

    @property
    @deprecated(replacement="map_name", date="2022-08")
    def map(self):
        return self.map_name

    @deprecated(replacement="build", date="2022-08")
    def __init__(
        self,
        protocol: int,
        brand: str,
        version: str,
        latency: float,
        players_online: int,
        players_max: int,
        motd: str,
        map_: Optional[str],
        gamemode: Optional[str],
    ) -> None:
        self.players = BedrockStatusPlayers(
            online=players_online,
            max=players_max,
        )
        self.version = self.Version(
            name=version,
            protocol=protocol,
            brand=brand,
        )
        self.motd = motd
        self.latency = latency
        self.map_name = map_
        self.gamemode = gamemode
