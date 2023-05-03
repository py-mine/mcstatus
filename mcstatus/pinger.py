from __future__ import annotations

import json
import random
from time import perf_counter
from typing import TYPE_CHECKING

from mcstatus.address import Address
from mcstatus.protocol.connection import Connection, TCPAsyncSocketConnection, TCPSocketConnection
from mcstatus.status_response import JavaStatusResponse

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


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

    def read_status(self) -> JavaStatusResponse:
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
            return JavaStatusResponse.build(raw, latency=(received - start) * 1000)
        except KeyError as e:
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

    async def read_status(self) -> JavaStatusResponse:
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
            return JavaStatusResponse.build(raw, latency=(received - start) * 1000)
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


# TODO Remove this deprecation after 2023-12
PingResponse: TypeAlias = JavaStatusResponse
