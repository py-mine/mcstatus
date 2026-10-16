from __future__ import annotations

import asyncio
import contextlib
import json
import socket
from time import perf_counter
from typing import ClassVar, TYPE_CHECKING, cast, final

from mcstatus.motd import Motd
from mcstatus.responses import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion

if TYPE_CHECKING:
    from mcstatus._net.address import Address

__all__ = ["BedrockNetherNetClient"]


@final
class BedrockNetherNetClient:
    """Client for querying Minecraft Bedrock Edition servers that use the NetherNet transport.

    NetherNet servers expose an HTTP signaling endpoint on the server port (TCP). A ``GET /v1/join``
    capability check returns a JSON object describing the server, which this client maps onto
    :class:`~mcstatus.responses.BedrockStatusResponse`. See https://minecraft.wiki/w/NetherNet.

    Only plaintext HTTP signaling is supported (not HTTPS).

    .. note::
        The reported latency covers the TCP handshake and the HTTP round trip, so it is
        typically higher than the single UDP round trip measured over RakNet.
    """

    MAX_RESPONSE_SIZE: ClassVar[int] = 64 * 1024
    GAMEMODES: ClassVar[dict[int, str]] = {0: "Survival", 1: "Creative", 2: "Adventure"}

    def __init__(self, address: Address, timeout: float = 3) -> None:
        self.address = address
        self.timeout = timeout

    def _build_request(self) -> bytes:
        host = f"[{self.address.host}]" if ":" in self.address.host else self.address.host
        return (
            "GET /v1/join HTTP/1.0\r\n"
            f"Host: {host}:{self.address.port}\r\n"
            "User-Agent: mcstatus\r\n"
            "Accept: application/json\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("ascii")

    @staticmethod
    def _parse_content_length(head: bytes | bytearray) -> int | None:
        for line in head.split(b"\r\n")[1:]:
            if line.lower().startswith(b"content-length:"):
                with contextlib.suppress(ValueError):
                    return int(line.split(b":", 1)[1].strip())
        return None

    @classmethod
    def _feed(cls, raw: bytearray, chunk: bytes) -> bool:
        """Append ``chunk`` to ``raw``; return True once the full response has arrived."""
        raw.extend(chunk)
        if len(raw) > cls.MAX_RESPONSE_SIZE:
            raise OSError(f"NetherNet signaling response exceeded {cls.MAX_RESPONSE_SIZE} bytes")
        head, sep, body = raw.partition(b"\r\n\r\n")
        if not sep:
            return False
        content_length = cls._parse_content_length(head)
        return content_length is not None and len(body) >= content_length

    @classmethod
    def _extract_body(cls, raw: bytes) -> bytes:
        """Validate the HTTP status line of a raw response and return its body."""
        if not raw:
            raise OSError("Server closed connection without responding to HTTP signaling probe.")

        head, _, body = raw.partition(b"\r\n\r\n")
        status_line = head.split(b"\r\n", 1)[0]
        status_parts = status_line.split(b" ", 2)
        if len(status_parts) < 2 or not status_parts[0].startswith(b"HTTP/") or not status_parts[1].isdigit():
            raise OSError(f"Received malformed HTTP response: {head[:64]!r}")

        status = int(status_parts[1])
        if not 200 <= status < 300:
            raise OSError(f"Server returned HTTP {status}")

        content_length = cls._parse_content_length(head)
        if content_length is not None and len(body) > content_length:
            body = body[:content_length]

        return body

    @staticmethod
    def _require_int(raw: dict[str, object], key: str) -> int:
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise OSError(f"NetherNet status field {key!r} must be an integer, got {value!r}")
        return value

    @staticmethod
    def _require_str(raw: dict[str, object], key: str) -> str:
        value = raw.get(key)
        if not isinstance(value, str):
            raise OSError(f"NetherNet status field {key!r} must be a string, got {value!r}")
        return value

    @classmethod
    def parse_response(cls, body: bytes, latency: float) -> BedrockStatusResponse:
        """Parse a NetherNet ``GET /v1/join`` JSON payload into a :class:`BedrockStatusResponse`.

        :param body: Response payload bytes from the server.
        :param latency: Latency of the request in milliseconds.
        :return: Parsed :class:`~mcstatus.responses.BedrockStatusResponse` instance.
        :raises OSError: If the payload isn't a JSON object with the expected fields.
        """
        try:
            raw_data: object = json.loads(body)
        except ValueError as exc:
            raise OSError(f"Invalid NetherNet status payload: {body[:128]!r}") from exc

        if not isinstance(raw_data, dict):
            raise OSError(f"Expected JSON object in NetherNet status response, got {type(raw_data).__name__}")
        raw = cast("dict[str, object]", raw_data)

        level = raw.get("level")
        game_type = raw.get("gameType")

        return BedrockStatusResponse(
            players=BedrockStatusPlayers(
                online=cls._require_int(raw, "players"),
                max=cls._require_int(raw, "maxPlayers"),
            ),
            version=BedrockStatusVersion(
                name=cls._require_str(raw, "version"),
                protocol=cls._require_int(raw, "protocol"),
                brand="MCPE",  # /v1/join doesn't report an edition brand; RakNet would say MCPE or MCEE
            ),
            motd=Motd.parse(cls._require_str(raw, "name"), bedrock=True),
            latency=latency,
            map_name=level if isinstance(level, str) else None,
            gamemode=cls.GAMEMODES.get(game_type) if isinstance(game_type, int) else None,
        )

    def read_status(self) -> BedrockStatusResponse:
        """Probe the NetherNet server over TCP synchronously."""
        start = perf_counter()
        body = self._extract_body(self._read_status())
        end = perf_counter()
        return self.parse_response(body, (end - start) * 1000)

    def _read_status(self) -> bytes:
        deadline = perf_counter() + self.timeout

        def remaining() -> float:
            left = deadline - perf_counter()
            if left <= 0:
                raise TimeoutError("timed out")
            return left

        with socket.create_connection((self.address.host, self.address.port), timeout=remaining()) as sock:
            sock.sendall(self._build_request())
            raw = bytearray()
            while True:
                sock.settimeout(remaining())
                chunk = sock.recv(4096)
                if not chunk or self._feed(raw, chunk):
                    return bytes(raw)

    async def read_status_async(self) -> BedrockStatusResponse:
        """Probe the NetherNet server over TCP asynchronously."""
        start = perf_counter()
        body = self._extract_body(await asyncio.wait_for(self._read_status_async(), timeout=self.timeout))
        end = perf_counter()
        return self.parse_response(body, (end - start) * 1000)

    async def _read_status_async(self) -> bytes:
        reader, writer = await asyncio.open_connection(self.address.host, self.address.port)
        try:
            writer.write(self._build_request())
            await writer.drain()
            raw = bytearray()
            while True:
                chunk = await reader.read(4096)
                if not chunk or self._feed(raw, chunk):
                    return bytes(raw)
        finally:
            writer.close()
            with contextlib.suppress(OSError):
                await writer.wait_closed()
