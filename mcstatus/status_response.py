from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

__all__ = [
    "STYLE_MAP",
    "AbstractDataclass",
    "MCServerResponse",
    "JavaServerResponse",
    "BedrockServerResponse",
    "ServerPlayers",
    "JavaServerPlayers",
    "BedrockServerPlayers",
    "JavaServerPlayer",
    "ServerVersion",
    "JavaServerVersion",
    "BedrockServerVersion",
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
    """This function ensures that all required keys are present, and are of specified type.

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
        if cls is AbstractDataclass or cls.__bases__[0] is AbstractDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)


@dataclass
class MCServerResponse(AbstractDataclass):
    """Class for storing shared data from a status response."""

    players: ServerPlayers
    version: ServerVersion
    # Message Of The Day. Also known as `Description`.
    motd: str
    # Latency between a server and the client (you). In milliseconds.
    latency: float

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs) -> MCServerResponse:
        """Build MCServerResponse and check is it valid.

        :param args: Arguments in specific realisation.
        :param kwargs: Keyword arguments in specific realisation.
        :return: `MCServerResponse` object.
        """
        raise NotImplementedError("You can't use abstract methods.")


@dataclass
class JavaServerResponse(MCServerResponse):
    """Dataclass for storing Java status answer object."""

    players: JavaServerPlayers
    version: JavaServerVersion
    # Icon of the server. Can be unset. BASE64 encoded.
    icon: Optional[str]

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> JavaServerResponse:
        """Build JavaServerResponse and check is it valid.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (players, version, description) are not present.
        :raise TypeError: If the required keys (players - dict, version - dict, description - str)
            are not of the specified type.
        :return: `JavaServerResponse` object.
        """
        _validate_data(raw, "status", [("players", dict), ("version", dict), ("description", str)])
        return cls(
            players=JavaServerPlayers.build(raw["players"]),
            version=JavaServerVersion.build(raw["version"]),
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
class BedrockServerResponse(MCServerResponse):
    """Dataclass for storing Java status answer object."""

    players: BedrockServerPlayers
    version: BedrockServerVersion
    # Can be unset.
    map_name: Optional[str]
    # Can be hidden.
    gamemode: Optional[str]

    @classmethod
    def build(cls, decoded_data: List[Any], latency: float) -> BedrockServerResponse:
        """Build MCServerResponse and check is it valid.

        :param decoded_data: Raw decoded response object.
        :param latency: Latency of the request.
        :return: `BedrockServerResponse` object.
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
            players=BedrockServerPlayers(
                online=int(decoded_data[4]),
                max=int(decoded_data[5]),
            ),
            version=BedrockServerVersion(
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
class ServerPlayers(AbstractDataclass):
    """Dataclass for storing players list and some global info about players, like current online."""

    online: int
    max: int


@dataclass
class JavaServerPlayers(ServerPlayers):
    """Dataclass for storing players list and some global info about players, like current online."""

    # List of players. Can be unset. In Java can be empty even if online > 0.
    list: List[JavaServerPlayer]

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> JavaServerPlayers:
        """Build `JavaServerPlayers` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (online, max, sample) are not present.
        :raise TypeError: If the required keys (online - int, max - int, sample - list) are not of the specified type.
        :return: `JavaServerPlayers` object.
        """
        _validate_data(raw, "players", [("online", int), ("max", int)])
        if "sample" in raw:
            _validate_data(raw, "players", [("sample", list)])
        return cls(
            online=raw["online"],
            max=raw["max"],
            list=[JavaServerPlayer.build(player) for player in raw["sample"]] if "sample" in raw else [],
        )


@dataclass
class BedrockServerPlayers(ServerPlayers):
    """Dataclass for storing players list and some global info about players, like current online."""


@dataclass
class JavaServerPlayer:
    """Dataclass for storing player info. Only for Java."""

    name: str
    uuid: str

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> JavaServerPlayer:
        """Build `JavaServerPlayer` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (name, uuid) are not present.
        :raise TypeError: If the required keys (name - str, uuid - str) are not of the specified type.
        :return: `JavaServerPlayer` object.
        """
        _validate_data(raw, "player", [("name", str), ("id", str)])
        return cls(name=raw["name"], uuid=raw["id"])


@dataclass
class ServerVersion(AbstractDataclass):
    """Dataclass for storing version info."""

    # Version name. Example `1.18.0`.
    name: str
    # Version protocol. See https://minecraft.fandom.com/wiki/Protocol_version.
    protocol: int


@dataclass
class JavaServerVersion(ServerVersion):
    """Dataclass for storing version info for Java."""

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> JavaServerVersion:
        """Build `JavaServerVersion` from raw response dict.

        :param raw: Raw response dict.
        :raise ValueError: If the required keys (name, protocol) are not present.
        :raise TypeError: If the required keys (name - str, protocol - int) are not of the specified type.
        :return: `JavaServerVersion` object.
        """
        _validate_data(raw, "version", [("name", str), ("protocol", int)])
        return cls(name=raw["name"], protocol=raw["protocol"])


@dataclass
class BedrockServerVersion(ServerVersion):
    """Dataclass for storing version info for Bedrock."""

    # Like `MCPE` or another.
    brand: Optional[str]
