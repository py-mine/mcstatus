from __future__ import annotations

import json
import random
from time import perf_counter
from typing import TYPE_CHECKING

from mcstatus.address import Address
from mcstatus.protocol.connection import Connection, TCPAsyncSocketConnection, TCPSocketConnection

if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypeAlias, TypedDict

    class RawResponsePlayer(TypedDict):
        name: str
        id: str

    class RawResponsePlayers(TypedDict):
        online: int
        max: int
        sample: NotRequired[list[RawResponsePlayer]]

    class RawResponseVersion(TypedDict):
        name: str
        protocol: int

    class RawResponseDescriptionWhenDict(TypedDict, total=False):
        text: str  # only present if translation is set
        translation: str  # same to the above field
        extra: list[RawResponseDescriptionWhenDict]

        color: str
        bold: bool
        strikethrough: bool
        italic: bool
        underlined: bool
        obfuscated: bool

    RawResponseDescription: TypeAlias = "RawResponseDescriptionWhenDict | list[RawResponseDescriptionWhenDict] | str"

    class RawResponse(TypedDict):
        description: RawResponseDescription
        players: RawResponsePlayers
        version: RawResponseVersion
        favicon: NotRequired[str]

else:
    RawResponsePlayer = dict
    RawResponsePlayers = dict
    RawResponseVersion = dict
    RawResponseDescriptionWhenDict = dict
    RawResponse = dict


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


class ServerPinger:
    def __init__(
        self,
        connection: TCPSocketConnection,
        address: Address,
        version: int = 47,
        ping_token: int | None = None,
    ):
        if ping_token is None:
            ping_token = random.randint(0, (1 << 63) - 1)
        self.version = version
        self.connection = connection
        self.address = address
        self.ping_token = ping_token

    def handshake(self) -> None:
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.address.host)
        packet.write_ushort(self.address.port)
        packet.write_varint(1)  # Intention to query status

        self.connection.write_buffer(packet)

    def read_status(self) -> "PingResponse":
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        start = perf_counter()
        response = self.connection.read_buffer()
        received = perf_counter()
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")
        try:
            return PingResponse(raw, latency=(received - start) * 1000)
        except ValueError as e:
            raise IOError(f"Received invalid status response: {e}")

    def test_ping(self) -> float:
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = perf_counter()
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        received = perf_counter()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError(
                f"Received mangled ping response packet (expected token {self.ping_token}, received {received_token})"
            )

        return (received - sent) * 1000


class AsyncServerPinger(ServerPinger):
    def __init__(
        self,
        connection: TCPAsyncSocketConnection,
        address: Address,
        version: int = 47,
        ping_token: int | None = None,
    ):
        # We do this to inform python about self.connection type (it's async)
        super().__init__(connection, address=address, version=version, ping_token=ping_token)  # type: ignore[arg-type]
        self.connection: TCPAsyncSocketConnection

    async def read_status(self) -> "PingResponse":
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        start = perf_counter()
        response = await self.connection.read_buffer()
        received = perf_counter()
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")
        try:
            return PingResponse(raw, latency=(received - start) * 1000)
        except ValueError as e:
            raise IOError(f"Received invalid status response: {e}")

    async def test_ping(self) -> float:
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = perf_counter()
        self.connection.write_buffer(request)

        response = await self.connection.read_buffer()
        received = perf_counter()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError(
                f"Received mangled ping response packet (expected token {self.ping_token}, received {received_token})"
            )

        return (received - sent) * 1000


class PingResponse:
    # THIS IS SO UNPYTHONIC
    # it's staying just because the tests depend on this structure
    class Players:
        class Player:
            name: str
            id: str

            def __init__(self, raw: RawResponsePlayer):
                if not isinstance(raw, dict):
                    raise ValueError(f"Invalid player object (expected dict, found {type(raw)}")

                if "name" not in raw:
                    raise ValueError("Invalid player object (no 'name' value)")
                if not isinstance(raw["name"], str):
                    raise ValueError(f"Invalid player object (expected 'name' to be str, was {type(raw['name'])}")
                self.name = raw["name"]

                if "id" not in raw:
                    raise ValueError("Invalid player object (no 'id' value)")
                if not isinstance(raw["id"], str):
                    raise ValueError(f"Invalid player object (expected 'id' to be str, was {type(raw['id'])}")
                self.id = raw["id"]

        online: int
        max: int
        sample: list["PingResponse.Players.Player"] | None

        def __init__(self, raw: RawResponsePlayers):
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid players object (expected dict, found {type(raw)}")

            if "online" not in raw:
                raise ValueError("Invalid players object (no 'online' value)")
            if not isinstance(raw["online"], int):
                raise ValueError(f"Invalid players object (expected 'online' to be int, was {type(raw['online'])})")
            self.online = raw["online"]

            if "max" not in raw:
                raise ValueError("Invalid players object (no 'max' value)")
            if not isinstance(raw["max"], int):
                raise ValueError(f"Invalid players object (expected 'max' to be int, was {type(raw['max'])}")
            self.max = raw["max"]

            if "sample" in raw:
                if not isinstance(raw["sample"], list):
                    raise ValueError(f"Invalid players object (expected 'sample' to be list, was {type(raw['max'])})")
                self.sample = [PingResponse.Players.Player(p) for p in raw["sample"]]
            else:
                self.sample = None

    class Version:
        name: str
        protocol: int

        def __init__(self, raw: RawResponseVersion):
            if not isinstance(raw, dict):
                raise ValueError(f"Invalid version object (expected dict, found {type(raw)})")

            if "name" not in raw:
                raise ValueError("Invalid version object (no 'name' value)")
            if not isinstance(raw["name"], str):
                raise ValueError(f"Invalid version object (expected 'name' to be str, was {type(raw['name'])})")
            self.name = raw["name"]

            if "protocol" not in raw:
                raise ValueError("Invalid version object (no 'protocol' value)")
            if not isinstance(raw["protocol"], int):
                raise ValueError(f"Invalid version object (expected 'protocol' to be int, was {type(raw['protocol'])})")
            self.protocol = raw["protocol"]

    players: Players
    version: Version
    description: str
    favicon: str | None
    latency: float

    def __init__(self, raw: RawResponse, latency: float = 0):
        self.raw = raw
        self.latency = latency

        if "players" not in raw:
            raise ValueError("Invalid status object (no 'players' value)")
        self.players = PingResponse.Players(raw["players"])

        if "version" not in raw:
            raise ValueError("Invalid status object (no 'version' value)")
        self.version = PingResponse.Version(raw["version"])

        if "description" not in raw:
            raise ValueError("Invalid status object (no 'description' value)")
        self.description = self._parse_description(raw["description"])

        self.favicon = raw.get("favicon")

    @staticmethod
    def _parse_description(raw_description: RawResponseDescription) -> str:
        if isinstance(raw_description, str):
            return raw_description

        if isinstance(raw_description, dict):
            entries = raw_description.get("extra", [])
            end = raw_description.get("text", "")
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
