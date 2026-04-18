from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, final

from mcstatus._protocol.io.base_io import StructFormat
from mcstatus._protocol.io.buffer import Buffer
from mcstatus.responses import JavaStatusResponse

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from typing_extensions import override

    from mcstatus._net.address import Address
    from mcstatus._protocol.io.connection import TCPAsyncSocketConnection, TCPSocketConnection
    from mcstatus.responses._raw import RawJavaResponse
else:
    override = lambda f: f  # noqa: E731

__all__ = ["AsyncJavaClient", "JavaClient"]


@dataclass
class _BaseJavaClient(ABC):
    connection: TCPSocketConnection | TCPAsyncSocketConnection
    address: Address
    version: int
    """Version of the client."""
    ping_token: int = None  # pyright: ignore[reportAssignmentType]
    """Token that is used for the request, default is random number."""

    def __post_init__(self) -> None:
        if self.ping_token is None:  # pyright: ignore[reportUnnecessaryComparison]
            self.ping_token = random.randint(0, (1 << 63) - 1)

    def _build_handshake_packet(self) -> Buffer:
        """Build the initial handshake packet."""
        packet = Buffer()
        packet.write_varint(0)
        packet.write_varint(self.version)
        packet.write_utf(self.address.host)
        packet.write_value(StructFormat.USHORT, self.address.port)
        packet.write_varint(1)  # Intention to query status
        return packet

    @abstractmethod
    def read_status(self) -> JavaStatusResponse | Awaitable[JavaStatusResponse]:
        """Make a status request and parse the response."""
        raise NotImplementedError

    @abstractmethod
    def test_ping(self) -> float | Awaitable[float]:
        """Send a ping token and measure the latency."""
        raise NotImplementedError

    def _handle_status_response(self, response: Buffer, start: float, end: float) -> JavaStatusResponse:
        """Given a response buffer (already read from connection), parse and build the JavaStatusResponse."""
        if response.read_varint() != 0:
            raise OSError("Received invalid status response packet.")
        try:
            raw: RawJavaResponse = json.loads(response.read_utf())
        except ValueError as e:
            raise OSError("Received invalid JSON") from e

        try:
            latency_ms = (end - start) * 1000
            return JavaStatusResponse.build(raw, latency=latency_ms)
        except KeyError as e:
            raise OSError("Received invalid status response") from e

    def _handle_ping_response(self, response: Buffer, start: float, end: float) -> float:
        """Given a ping response buffer, validate token and compute latency."""
        if response.read_varint() != 1:
            raise OSError("Received invalid ping response packet.")
        received_token = response.read_value(StructFormat.LONGLONG)
        if received_token != self.ping_token:
            raise OSError(f"Received mangled ping response (expected token {self.ping_token}, got {received_token})")
        return (end - start) * 1000


@final
@dataclass
class JavaClient(_BaseJavaClient):
    connection: TCPSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    def handshake(self) -> None:
        """Write the initial handshake packet to the connection."""
        self.connection.write_bytearray(self._build_handshake_packet())

    @override
    def read_status(self) -> JavaStatusResponse:
        """Send the status request and read the response."""
        request = Buffer()
        request.write_varint(0)  # Request status
        self.connection.write_bytearray(request)

        start = perf_counter()
        response = Buffer(self.connection.read_bytearray())
        end = perf_counter()
        return self._handle_status_response(response, start, end)

    @override
    def test_ping(self) -> float:
        """Send a ping token and measure the latency."""
        request = Buffer()
        request.write_varint(1)  # Test ping
        request.write_value(StructFormat.LONGLONG, self.ping_token)
        start = perf_counter()
        self.connection.write_bytearray(request)

        response = Buffer(self.connection.read_bytearray())
        end = perf_counter()
        return self._handle_ping_response(response, start, end)


@final
@dataclass
class AsyncJavaClient(_BaseJavaClient):
    connection: TCPAsyncSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    async def handshake(self) -> None:
        """Write the initial handshake packet to the connection."""
        await self.connection.write_bytearray(self._build_handshake_packet())

    @override
    async def read_status(self) -> JavaStatusResponse:
        """Send the status request and read the response."""
        request = Buffer()
        request.write_varint(0)  # Request status
        await self.connection.write_bytearray(request)

        start = perf_counter()
        response = Buffer(await self.connection.read_bytearray())
        end = perf_counter()
        return self._handle_status_response(response, start, end)

    @override
    async def test_ping(self) -> float:
        """Send a ping token and measure the latency."""
        request = Buffer()
        request.write_varint(1)  # Test ping
        request.write_value(StructFormat.LONGLONG, self.ping_token)
        start = perf_counter()
        await self.connection.write_bytearray(request)

        response = Buffer(await self.connection.read_bytearray())
        end = perf_counter()
        return self._handle_ping_response(response, start, end)
