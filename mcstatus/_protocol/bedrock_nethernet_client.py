from __future__ import annotations

import asyncio
import json
import socket
from time import perf_counter
from typing import TYPE_CHECKING, TypedDict, final

from mcstatus.motd import Motd
from mcstatus.responses import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion

if TYPE_CHECKING:
    from mcstatus._net.address import Address

__all__ = ["BedrockNetherNetClient"]


class _RawNetherNetVersion(TypedDict, total=False):
    name: str
    protocol: int


class _RawNetherNetPlayers(TypedDict, total=False):
    online: int
    max: int


class _RawNetherNetBody(TypedDict, total=False):
    motd: str
    version: _RawNetherNetVersion
    players: _RawNetherNetPlayers


def _parse_headers(header_part: bytes) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in header_part.decode("iso-8859-1", errors="replace").split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return headers


def _parse_json_or_semicolon_body(
    body_part: bytes,
    latency: float,
    default_server_name: str,
) -> BedrockStatusResponse | None:
    try:
        decoded_str = body_part.decode("utf-8", errors="replace")
        raw_json: _RawNetherNetBody = json.loads(decoded_str)
    except (json.JSONDecodeError, ValueError, TypeError):
        decoded_body = body_part.decode("utf-8", errors="replace").strip()
        if decoded_body.startswith("MCPE;") or ";" in decoded_body:
            return BedrockStatusResponse.build(decoded_body.split(";"), latency)
        return None

    motd_text = raw_json.get("motd", "NetherNet Bedrock Server")
    version_data = raw_json.get("version", {})
    server_name = version_data.get("name", default_server_name)
    protocol = version_data.get("protocol", -1)
    players_data = raw_json.get("players", {})
    online_players = players_data.get("online", -1)
    max_players = players_data.get("max", -1)

    return BedrockStatusResponse(
        players=BedrockStatusPlayers(online=online_players, max=max_players),
        version=BedrockStatusVersion(name=server_name, protocol=protocol, brand="MCPE"),
        motd=Motd.parse(motd_text, bedrock=True),
        latency=latency,
        map_name=None,
        gamemode=None,
    )


@final
class BedrockNetherNetClient:
    """Client for querying Minecraft Bedrock Edition servers running NetherNet (WebRTC/TCP signaling)."""

    def __init__(self, address: Address, timeout: float = 3) -> None:
        self.address = address
        self.timeout = timeout

    @staticmethod
    def parse_response(data: bytes, latency: float) -> BedrockStatusResponse:
        """Parse HTTP/signaling response data into BedrockStatusResponse.

        :param data: Raw response bytes from the server.
        :param latency: Latency of the request in milliseconds.
        :return: Parsed BedrockStatusResponse instance.
        """
        header_part, _, body_part = data.partition(b"\r\n\r\n")
        headers = _parse_headers(header_part)
        server_name = headers.get("server") or "NetherNet"

        if body_part:
            parsed = _parse_json_or_semicolon_body(body_part, latency, server_name)
            if parsed is not None:
                return parsed

        return BedrockStatusResponse(
            players=BedrockStatusPlayers(online=-1, max=-1),
            version=BedrockStatusVersion(name=server_name, protocol=-1, brand="MCPE"),
            motd=Motd.parse("NetherNet Bedrock Server", bedrock=True),
            latency=latency,
            map_name=None,
            gamemode=None,
        )

    def read_status(self) -> BedrockStatusResponse:
        """Probe the NetherNet server over TCP synchronously."""
        start = perf_counter()
        data = self._read_status()
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)

    def _read_status(self) -> bytes:
        with socket.create_connection(self.address, timeout=self.timeout) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.address.host}:{self.address.port}\r\n"
                f"User-Agent: mcstatus\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("ascii")
            s.sendall(request)
            response = bytearray()
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response.extend(chunk)
                if b"\r\n\r\n" in response and len(response) > 512:
                    break
            if not response:
                raise OSError("Server closed connection without responding to HTTP signaling probe.")
            return bytes(response)

    async def read_status_async(self) -> BedrockStatusResponse:
        """Probe the NetherNet server over TCP asynchronously."""
        start = perf_counter()
        data = await self._read_status_async()
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)

    async def _read_status_async(self) -> bytes:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.address.host, self.address.port),
            timeout=self.timeout,
        )
        try:
            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.address.host}:{self.address.port}\r\n"
                f"User-Agent: mcstatus\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("ascii")
            writer.write(request)
            await asyncio.wait_for(writer.drain(), timeout=self.timeout)
            response = bytearray()
            while True:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=self.timeout)
                if not chunk:
                    break
                response.extend(chunk)
                if b"\r\n\r\n" in response and len(response) > 512:
                    break
            if not response:
                raise OSError("Server closed connection without responding to HTTP signaling probe.")
            return bytes(response)
        finally:
            writer.close()
            await writer.wait_closed()
