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
    "BaseStatusPlayers",
    "BaseStatusResponse",
    "BaseStatusVersion",
    "BedrockStatusPlayers",
    "BedrockStatusResponse",
    "BedrockStatusVersion",
    "JavaStatusPlayer",
    "JavaStatusPlayers",
    "JavaStatusResponse",
    "JavaStatusVersion",
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

    :param raw: The raw :class:`dict` answer to check.
    :param who: The name of the object that is checking the data. Example ``status``, ``player`` etc.
    :param required: An iterable of string and type. The string is the required key which must be in ``raw``, and the
        ``type`` is the type that the key must be. If you want to ignore check of the type, set the type to ``object``.
    :raises ValueError: If the required keys are not present.
    :raises TypeError: If the required keys are not of the expected type.
    """
    for required_key, required_type in required:
        if required_key not in raw:
            raise ValueError(f"Invalid {who} object (no {required_key!r} value)")
        if not isinstance(raw[required_key], required_type):
            raise TypeError(
                f"Invalid {who} object (expected {required_key!r} to be {required_type}, was {type(raw[required_key])})"
            )


@dataclass
class BaseStatusResponse(ABC):
    """Class for storing shared data from a status response."""

    players: BaseStatusPlayers
    version: BaseStatusVersion
    motd: str
    """Message Of The Day. Also known as description."""
    latency: float
    """Latency between a server and the client (you). In milliseconds."""

    @property
    def description(self) -> str:
        """Alias to the :attr:`.motd` field.

        :return: Description of the server.
        """
        return self.motd

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param args: Arguments in specific realisation.
        :param kwargs: Keyword arguments in specific realisation.
        :return: :class:`BaseStatusResponse` object.
        """
        raise NotImplementedError("You can't use abstract methods.")


@dataclass
class JavaStatusResponse(BaseStatusResponse):
    """Class for storing JavaServer data from a status response."""

    raw: RawJavaResponse
    players: JavaStatusPlayers
    version: JavaStatusVersion
    icon: str | None
    """Base64 encoded icon of the server."""

    @classmethod
    def build(cls, raw: RawJavaResponse, latency: float = 0) -> Self:
        """Build JavaStatusResponse and check is it valid.

        :param raw: Raw response :class:`dict`.
        :param latency: Time that server took to response (in milliseconds).
        :raise ValueError: If the required keys (``players``, ``version``, ``description``) are not present.
        :raise TypeError:
            If the required keys (``players`` - :class:`dict`, ``version`` - :class:`dict`,
            ``description`` - :class:`str`) are not of the expected type.
        :return: :class:`JavaStatusResponse` object.
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
    """Class for storing BedrockServer data from a status response."""

    players: BedrockStatusPlayers
    version: BedrockStatusVersion
    map_name: str | None
    """Name of the map."""
    gamemode: str | None
    """Gamemode of the server. Can be hidden."""

    @classmethod
    def build(cls, decoded_data: list[Any], latency: float) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param decoded_data: Raw decoded response object.
        :param latency: Latency of the request.
        :return: :class:`BedrockStatusResponse` object.
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
    """Class which extends a :class:`BaseStatusPlayers` class with sample of players."""

    sample: list[JavaStatusPlayer] | None
    """:class:`list` of players or :obj:`None` if the sample is missing in the response."""

    @classmethod
    def build(cls, raw: RawJavaResponsePlayers) -> Self:
        """Build :class:`JavaStatusPlayers` from raw response :class:`dict`.

        :param raw: Raw response :class:`dict`.
        :raise ValueError: If the required keys (``online``, ``max``) are not present.
        :raise TypeError:
            If the required keys (``online`` - :class:`int`, ``max`` - :class:`int`,
            ``sample`` - :class:`list`) are not of the expected type.
        :return: :class:`JavaStatusPlayers` object.
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
    """Class which represents :attr`BedrockStatusResponse.players` attribute."""


@dataclass
class JavaStatusPlayer:
    """Class for storing player info. Only for Java."""

    name: str
    id: str

    @property
    def uuid(self) -> str:
        """Alias to the :attr:`.id` field.

        :return: UUID of the player.
        """
        return self.id

    @classmethod
    def build(cls, raw: RawJavaResponsePlayer) -> Self:
        """Build :class:`JavaStatusPlayer` from raw response :class:`dict`.

        :param raw: Raw response :class:`dict`.
        :raise ValueError: If the required keys (``name``, ``id``) are not present.
        :raise TypeError: If the required keys (``name`` - :class:`str`, ``id`` - :class:`str`)
            are not of the expected type.
        :return: :class:`JavaStatusPlayer` object.
        """
        _validate_data(raw, "player", [("name", str), ("id", str)])
        return cls(name=raw["name"], id=raw["id"])


@dataclass
class BaseStatusVersion(ABC):
    """Class for storing version info."""

    name: str
    """Version name. Example ``1.19.3``."""
    protocol: int
    """Version protocol. See https://minecraft.fandom.com/wiki/Protocol_version."""


@dataclass
class JavaStatusVersion(BaseStatusVersion):
    """Class for storing Java version info."""

    @classmethod
    def build(cls, raw: RawJavaResponseVersion) -> Self:
        """Build :class:`JavaStatusVersion` from raw response dict.

        :param raw: Raw response :class:`dict`.
        :raise ValueError: If the required keys (``name``, ``protocol``) are not present.
        :raise TypeError: If the required keys (``name`` - :class:`str`, ``protocol`` - :class:`int`)
            are not of the expected type.
        :return: :class:`JavaStatusVersion` object.
        """
        _validate_data(raw, "version", [("name", str), ("protocol", int)])
        return cls(name=raw["name"], protocol=raw["protocol"])


@dataclass
class BedrockStatusVersion(BaseStatusVersion):
    """Class for storing Bedrock version info."""

    brand: str
    """Like ``MCPE`` or something another."""

    @property
    @deprecated(replacement="name", date="DEPRECATION_DATE")
    def version(self) -> str:
        return self.name
