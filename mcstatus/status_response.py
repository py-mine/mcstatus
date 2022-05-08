from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

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


@dataclass
class AbstractDataclass(ABC):
    """Abstract base class for all dataclasses.

    We can't use just `ABC` because we need raise TypeError if we try to
    instantiate an abstract dataclass. Class which inherit from `ABC` raises
    it only if it has abstract methods.
    """

    def __new__(cls, *args, **kwargs):
        if cls == AbstractDataclass or cls.__bases__[0] == AbstractDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)


@dataclass
class MCServerResponse(AbstractDataclass):
    """Dataclass for storing cross-platform status answer object."""

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
        :return: `JavaServerResponse` object.
        """
        cls._validate(raw)
        return cls(
            players=JavaServerPlayers.build(raw["players"]),
            version=JavaServerVersion.build(raw["version"]),
            motd=cls._parse_description(raw["description"]),
            icon=raw.get("favicon"),
            # This will be set later.
            latency=None,  # type: ignore[assignment]
        )

    @staticmethod
    def _validate(raw: Dict[str, Any]) -> None:
        """Check is the status object valid.

        :param raw: Raw response dict.
        :raises ValueError: If there are not 'players', 'version' or 'description' value in raw.
        """
        if "players" not in raw:
            raise ValueError("Invalid status object (no 'players' value)")
        if "version" not in raw:
            raise ValueError("Invalid status object (no 'version' value)")
        if "description" not in raw:
            raise ValueError("Invalid status object (no 'description' value)")

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

    # List of players. Can be unset. In Java can be None even if online > 0.
    list: Optional[List[JavaServerPlayer]]

    @classmethod
    def build(cls, raw: Dict[str, Any]) -> JavaServerPlayers:
        """Build `JavaServerPlayers` from raw response dict."""
        cls._validate(raw)
        return cls(
            online=raw["online"],
            max=raw["max"],
            list=[JavaServerPlayer.build(player) for player in raw["sample"]] if "sample" in raw else None,
        )

    @staticmethod
    def _validate(raw: Dict[str, Any]) -> None:
        """Check is the status object valid.

        :param raw: Raw response dict.
        :raises ValueError: See source code for full list of possible reasons.
        """
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid players object (expected dict, found {type(raw)}")

        if "online" not in raw:
            raise ValueError("Invalid players object (no 'online' value)")
        if not isinstance(raw["online"], int):
            raise ValueError(f"Invalid players object (expected 'online' to be int, was {type(raw['online'])})")

        if "max" not in raw:
            raise ValueError("Invalid players object (no 'max' value)")
        if not isinstance(raw["max"], int):
            raise ValueError(f"Invalid players object (expected 'max' to be int, was {type(raw['max'])}")

        if "sample" in raw:
            if not isinstance(raw["sample"], list):
                raise ValueError(f"Invalid players object (expected 'sample' to be list, was {type(raw['max'])})")


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
        """Build `JavaServerPlayer` from raw response dict."""
        cls._validate(raw)
        return cls(name=raw["name"], uuid=raw["id"])

    @staticmethod
    def _validate(raw: Dict[str, Any]) -> None:
        """Check is the status object valid.

        :param raw: Raw response dict.
        :raises ValueError: See source code for full list of possible reasons.
        """
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid player object (expected dict, found {type(raw)}")

        if "name" not in raw:
            raise ValueError("Invalid player object (no 'name' value)")
        if not isinstance(raw["name"], str):
            raise ValueError(f"Invalid player object (expected 'name' to be str, was {type(raw['name'])}")

        if "id" not in raw:
            raise ValueError("Invalid player object (no 'id' value)")
        if not isinstance(raw["id"], str):
            raise ValueError(f"Invalid player object (expected 'id' to be str, was {type(raw['id'])}")


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
        """Build `JavaServerVersion` from raw response dict."""
        cls._validate(raw)
        return cls(name=raw["name"], protocol=raw["protocol"])

    @staticmethod
    def _validate(raw: Dict[str, Any]) -> None:
        """Check is the status object valid.

        :param raw: Raw response dict.
        :raises ValueError: See source code for full list of possible reasons.
        """
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid version object (expected dict, found {type(raw)})")

        if "name" not in raw:
            raise ValueError("Invalid version object (no 'name' value)")
        if not isinstance(raw["name"], str):
            raise ValueError(f"Invalid version object (expected 'name' to be str, was {type(raw['name'])})")

        if "protocol" not in raw:
            raise ValueError("Invalid version object (no 'protocol' value)")
        if not isinstance(raw["protocol"], int):
            raise ValueError(f"Invalid version object (expected 'protocol' to be int, was {type(raw['protocol'])})")


@dataclass
class BedrockServerVersion(ServerVersion):
    """Dataclass for storing version info for Bedrock."""

    # Like `MCPE` or another.
    brand: Optional[str]
