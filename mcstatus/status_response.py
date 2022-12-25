from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, TypeAlias, TypedDict

    class RawJavaResponsePlayer(TypedDict):
        name: str
        id: str

    class RawJavaResponsePlayers(TypedDict):
        online: int
        max: int
        sample: NotRequired[list[RawJavaResponsePlayer]]

    class RawJavaResponseVersion(TypedDict):
        name: str
        protocol: int

    class RawJavaResponseMotdWhenDict(TypedDict, total=False):
        text: str  # only present if translation is set
        translation: str  # same to the above field
        extra: list[RawJavaResponseMotdWhenDict]

        color: str
        bold: bool
        strikethrough: bool
        italic: bool
        underlined: bool
        obfuscated: bool

    RawJavaResponseMotd: TypeAlias = "RawJavaResponseMotdWhenDict | list[RawJavaResponseMotdWhenDict] | str"

    class RawJavaResponse(TypedDict):
        description: RawJavaResponseMotd
        players: RawJavaResponsePlayers
        version: RawJavaResponseVersion
        favicon: NotRequired[str]

else:
    RawJavaResponsePlayer = dict
    RawJavaResponsePlayers = dict
    RawJavaResponseVersion = dict
    RawJavaResponseMotdWhenDict = dict
    RawJavaResponse = dict

from mcstatus.utils import deprecated

__all__ = [
    "BaseStatusResponse",
    "JavaStatusResponse",
    "BedrockStatusResponse",
    "BaseStatusPlayers",
    "JavaStatusPlayers",
    "BedrockStatusPlayers",
    "JavaStatusPlayer",
    "BaseStatusVersion",
    "JavaStatusVersion",
    "BedrockStatusVersion",
]

STYLE_MAP = {
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
    "bold": "l",
    "strikethrough": "m",
    "italic": "o",
    "underlined": "n",
    "obfuscated": "k",
    "reset": "r",
}


def _validate_data(raw: Mapping[str, Any], who: str, required: Iterable[tuple[str, type]]) -> None:
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
class BaseStatusResponse(ABC):
    """Class for storing shared data from a status response.

    :param motd: Message Of The Day. Also known as `Description`.
    :param latency: Latency between a server and the client (you). In milliseconds.
    """

    players: BaseStatusPlayers
    version: BaseStatusVersion
    motd: str
    latency: float

    @property
    def description(self) -> str:
        """Alias to the `motd` field.

        :return: Description of the server.
        """
        return self.motd

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param args: Arguments in specific realisation.
        :param kwargs: Keyword arguments in specific realisation.
        :return: `BaseStatusResponse` object.
        """
        raise NotImplementedError("You can't use abstract methods.")


@dataclass
class JavaStatusResponse(BaseStatusResponse):
    """Class for storing JavaServer data from a status response.

    :param icon: Base64 encoded icon of the server.
    """

    raw: RawJavaResponse
    players: JavaStatusPlayers
    version: JavaStatusVersion
    icon: str | None

    @classmethod
    def build(cls, raw: RawJavaResponse, latency: float = 0) -> Self:
        """Build JavaStatusResponse and check is it valid.

        :param raw: Raw response dict.
        :param latency: Time that server took to response (in milliseconds).
        :raise ValueError: If the required keys (players, version, description) are not present.
        :raise TypeError: If the required keys (players - dict, version - dict, description - str)
            are not of the specified type.
        :return: `JavaStatusResponse` object.
        """
        _validate_data(raw, "status", [("players", dict), ("version", dict), ("description", str)])
        return cls(
            raw=raw,
            players=JavaStatusPlayers.build(raw["players"]),
            version=JavaStatusVersion.build(raw["version"]),
            motd=cls._parse_motd(raw["description"]),
            icon=raw.get("favicon"),
            latency=latency,
        )

    @staticmethod
    def _parse_motd(raw_motd: RawJavaResponseMotd) -> str:
        """Parse MOTD from raw response.

        :param raw_motd: Raw MOTD.
        :return: Parsed MOTD.
        """
        if isinstance(raw_motd, str):
            return raw_motd

        if isinstance(raw_motd, dict):
            entries = raw_motd.get("extra", [])
            end = raw_motd.get("text", "")
        else:
            entries = raw_motd
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
class BedrockStatusResponse(BaseStatusResponse):
    """Class for storing BedrockServer data from a status response.

    :param map_name: Name of the map.
    :param gamemode: Gamemode of the server. Can be hidden.
    """

    players: BedrockStatusPlayers
    version: BedrockStatusVersion
    map_name: str | None
    gamemode: str | None

    @classmethod
    def build(cls, decoded_data: list[Any], latency: float) -> Self:
        """Build BaseStatusResponse and check is it valid.

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

    @property
    @deprecated(replacement="players.online", date="DEPRECATION_DATE")
    def players_online(self) -> int:
        return self.players.online

    @property
    @deprecated(replacement="players.max", date="DEPRECATION_DATE")
    def players_max(self) -> int:
        return self.players.max

    @property
    @deprecated(replacement="map_name", date="DEPRECATION_DATE")
    def map(self) -> str | None:
        return self.map_name


@dataclass
class BaseStatusPlayers(ABC):
    """Class for storing players info, like current online."""

    online: int
    max: int


@dataclass
class JavaStatusPlayers(BaseStatusPlayers):
    """Class which extends a `BaseStatusPlayers` class with sample of players.

    :param sample: list of players or `None` if the sample is missing in the response.
    """

    sample: list[JavaStatusPlayer] | None

    @classmethod
    def build(cls, raw: RawJavaResponsePlayers) -> Self:
        """Build `JavaStatusPlayers` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (online, max) are not present.
        :raise TypeError: If the required keys (online - int, max - int, sample - list) are not of the specified type.
        :return: `JavaStatusPlayers` object.
        """
        _validate_data(raw, "players", [("online", int), ("max", int)])
        sample = None
        if "sample" in raw:
            _validate_data(raw, "players", [("sample", list)])
            sample = [JavaStatusPlayer.build(player) for player in raw["sample"]]
        return cls(
            online=raw["online"],
            max=raw["max"],
            sample=sample,
        )


@dataclass
class BedrockStatusPlayers(BaseStatusPlayers):
    """Class which represents `BedrockStatusResponse` players field."""


@dataclass
class JavaStatusPlayer:
    """Class for storing player info. Only for Java."""

    name: str
    id: str

    @property
    def uuid(self) -> str:
        """Alias to the `id` field.

        :return: UUID of the player.
        """
        return self.id

    @classmethod
    def build(cls, raw: RawJavaResponsePlayer) -> Self:
        """Build `JavaStatusPlayer` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (name, id) are not present.
        :raise TypeError: If the required keys (name - str, id - str) are not of the specified type.
        :return: `JavaStatusPlayer` object.
        """
        _validate_data(raw, "player", [("name", str), ("id", str)])
        return cls(name=raw["name"], id=raw["id"])


@dataclass
class BaseStatusVersion(ABC):
    """Class for storing version info.

    :param name: Version name. Example `1.18.0`.
    :param protocol: Version protocol. See https://minecraft.fandom.com/wiki/Protocol_version.
    """

    name: str
    protocol: int


@dataclass
class JavaStatusVersion(BaseStatusVersion):
    """Class for storing Java version info."""

    @classmethod
    def build(cls, raw: RawJavaResponseVersion) -> Self:
        """Build `JavaStatusVersion` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (name, protocol) are not present.
        :raise TypeError: If the required keys (name - str, protocol - int) are not of the specified type.
        :return: `JavaStatusVersion` object.
        """
        _validate_data(raw, "version", [("name", str), ("protocol", int)])
        return cls(name=raw["name"], protocol=raw["protocol"])


@dataclass
class BedrockStatusVersion(BaseStatusVersion):
    """Class for storing Bedrock version info.

    :param brand: Like `MCPE` or another.
    """

    brand: str

    @property
    @deprecated(replacement="name", date="DEPRECATION_DATE")
    def version(self) -> str:
        return self.name
