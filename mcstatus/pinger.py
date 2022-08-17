from __future__ import annotations

import datetime
import json
import random
import re
from typing import List, Optional, Union, cast

from mcstatus.address import Address
from mcstatus.protocol.connection import Connection, TCPAsyncSocketConnection, TCPSocketConnection

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

DESCRIPTION_COLORS_RE = re.compile(r"[\xA7|&][0-9A-FK-OR]", re.IGNORECASE)


class ServerPinger:
    def __init__(
        self,
        connection: TCPSocketConnection,
        address: Address,
        version: int = 47,
        ping_token: Optional[int] = None,
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

        response = self.connection.read_buffer()
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")
        try:
            return PingResponse(raw)
        except ValueError as e:
            raise IOError(f"Received invalid status response: {e}")

    def test_ping(self) -> float:
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        received = datetime.datetime.now()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError(
                f"Received mangled ping response packet (expected token {self.ping_token}, received {received_token})"
            )

        delta = received - sent
        return delta.total_seconds() * 1000


class AsyncServerPinger(ServerPinger):
    def __init__(
        self,
        connection: TCPAsyncSocketConnection,
        address: Address,
        version: int = 47,
        ping_token: Optional[int] = None,
    ):
        # We do this to inform python about self.connection type (it's async)
        super().__init__(connection, address=address, version=version, ping_token=ping_token)  # type: ignore[arg-type]
        self.connection: TCPAsyncSocketConnection

    async def read_status(self) -> "PingResponse":
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        response = await self.connection.read_buffer()
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")
        try:
            return PingResponse(raw)
        except ValueError as e:
            raise IOError(f"Received invalid status response: {e}")

    async def test_ping(self) -> float:
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        sent = datetime.datetime.now()
        self.connection.write_buffer(request)

        response = await self.connection.read_buffer()
        received = datetime.datetime.now()
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError(
                f"Received mangled ping response packet (expected token {self.ping_token}, received {received_token})"
            )

        delta = received - sent
        return delta.total_seconds() * 1000


class PingResponse:
    # THIS IS SO UNPYTHONIC
    # it's staying just because the tests depend on this structure
    class Players:
        class Player:
            name: str
            id: str

            def __init__(self, raw: dict[str, object]):
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
        sample: Optional[List["PingResponse.Players.Player"]]

        def __init__(self, raw: dict[str, object]):
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

        def __init__(self, raw: dict[str, object]):
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

    class Description(str):
        """Extension of string class with support for obtaining server's description in different ways."""

        def clean(self) -> str:
            """Get description without color markers (&7, &a, §1 etc.).

            :return: Clean description, without colors.
            """
            return DESCRIPTION_COLORS_RE.sub("", self)

    players: Players
    version: Version
    description: Description
    favicon: Optional[str]
    latency: float = 0

    def __init__(self, raw: dict[str, object]):
        self.raw = raw

        # TODO: Consider using a TypedDict here, to avoid all of the type casts
        if "players" not in raw:
            raise ValueError("Invalid status object (no 'players' value)")
        self.players = PingResponse.Players(cast("dict[str, object]", raw["players"]))

        if "version" not in raw:
            raise ValueError("Invalid status object (no 'version' value)")
        self.version = PingResponse.Version(cast("dict[str, object]", raw["version"]))

        if "description" not in raw:
            raise ValueError("Invalid status object (no 'description' value)")
        self.description = self._parse_description(cast("dict[str, object]", raw["description"]))

        self.favicon = cast(Optional[str], raw.get("favicon"))

    @staticmethod
    def _parse_description(raw_description: Union[dict, list, str]) -> Description:
        if isinstance(raw_description, str):
            return PingResponse.Description(raw_description)

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

        return PingResponse.Description(description + end)
