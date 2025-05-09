from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from dataclasses import dataclass, field
import json
import random
from time import perf_counter
from typing import final

from mcstatus.address import Address
from mcstatus.protocol.connection import Connection, TCPAsyncSocketConnection, TCPSocketConnection
from mcstatus.responses import JavaStatusResponse, RawJavaResponse


@dataclass
class _BaseServerPinger(ABC):
    connection: TCPSocketConnection | TCPAsyncSocketConnection
    address: Address
    version: int = 47
    ping_token: int = field(default_factory=lambda: random.randint(0, (1 << 63) - 1))

    def handshake(self) -> None:
        """Writes the initial handshake packet to the connection."""
        packet = Connection()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.address.host)
        packet.write_ushort(self.address.port)
        packet.write_varint(1)  # Intention to query status

        self.connection.write_buffer(packet)

    @abstractmethod
    def read_status(self) -> JavaStatusResponse | Awaitable[JavaStatusResponse]:
        """Make a status request and parse the response."""
        raise NotImplementedError

    @abstractmethod
    def test_ping(self) -> float | Awaitable[float]:
        """Send a ping token and measure the latency."""
        raise NotImplementedError

    def _handle_status_response(self, response: Connection, start: float, end: float) -> JavaStatusResponse:
        """Given a response buffer (already read from connection), parse and build the JavaStatusResponse."""
        if response.read_varint() != 0:
            raise IOError("Received invalid status response packet.")
        try:
            raw: RawJavaResponse = json.loads(response.read_utf())
        except ValueError:
            raise IOError("Received invalid JSON")

        try:
            latency_ms = (end - start) * 1000
            return JavaStatusResponse.build(raw, latency=latency_ms)
        except KeyError as e:
            raise IOError(f"Received invalid status response: {e!r}")

    def _handle_ping_response(self, response: Connection, start: float, end: float) -> float:
        """Given a ping response buffer, validate token and compute latency."""
        if response.read_varint() != 1:
            raise IOError("Received invalid ping response packet.")
        received_token = response.read_long()
        if received_token != self.ping_token:
            raise IOError(f"Received mangled ping response (expected token {self.ping_token}, got {received_token})")
        return (end - start) * 1000


@final
@dataclass
class ServerPinger(_BaseServerPinger):
    connection: TCPSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    def read_status(self) -> JavaStatusResponse:
        """Send the status request and read the response."""
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        start = perf_counter()
        response = self.connection.read_buffer()
        end = perf_counter()
        return self._handle_status_response(response, start, end)

    def test_ping(self) -> float:
        """Send a ping token and measure the latency."""
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        start = perf_counter()
        self.connection.write_buffer(request)

        response = self.connection.read_buffer()
        end = perf_counter()
        return self._handle_ping_response(response, start, end)


@final
@dataclass
class AsyncServerPinger(_BaseServerPinger):
    connection: TCPAsyncSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    async def read_status(self) -> JavaStatusResponse:
        """Send the status request and read the response."""
        request = Connection()
        request.write_varint(0)  # Request status
        self.connection.write_buffer(request)

        start = perf_counter()
        response = await self.connection.read_buffer()
        end = perf_counter()
        return self._handle_status_response(response, start, end)

    async def test_ping(self) -> float:
        """Send a ping token and measure the latency."""
        request = Connection()
        request.write_varint(1)  # Test ping
        request.write_long(self.ping_token)
        start = perf_counter()
        self.connection.write_buffer(request)

        response = await self.connection.read_buffer()
        end = perf_counter()
        return self._handle_ping_response(response, start, end)
