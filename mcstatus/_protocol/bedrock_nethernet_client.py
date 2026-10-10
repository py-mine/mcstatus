from __future__ import annotations

import asyncio
import contextlib
import http.client
import json
from time import perf_counter
from typing import TYPE_CHECKING, cast, final

from mcstatus.motd import Motd
from mcstatus.responses import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion

if TYPE_CHECKING:
    from mcstatus._net.address import Address

__all__ = ["BedrockNetherNetClient"]


@final
class BedrockNetherNetClient:
    """Client for querying Minecraft Bedrock Edition servers running NetherNet (WebRTC/TCP signaling)."""

    def __init__(self, address: Address, timeout: float = 3) -> None:
        self.address = address
        self.timeout = timeout

    @staticmethod
    def _parse_motd(raw_dict: dict[str, object]) -> str:
        motd_val = raw_dict.get("motd")
        if isinstance(motd_val, str) and motd_val:
            return motd_val
        return "NetherNet Bedrock Server"

    @staticmethod
    def _parse_version(raw_dict: dict[str, object]) -> BedrockStatusVersion:
        server_name = "NetherNet"
        protocol = -1
        version_val = raw_dict.get("version")
        if isinstance(version_val, dict):
            version_dict = cast("dict[str, object]", version_val)
            name_val = version_dict.get("name")
            if isinstance(name_val, str):
                server_name = name_val
            proto_val = version_dict.get("protocol")
            if isinstance(proto_val, int):
                protocol = proto_val
        return BedrockStatusVersion(name=server_name, protocol=protocol, brand="MCPE")

    @staticmethod
    def _parse_players(raw_dict: dict[str, object]) -> BedrockStatusPlayers:
        online_players = -1
        max_players = -1
        players_val = raw_dict.get("players")
        if isinstance(players_val, dict):
            players_dict = cast("dict[str, object]", players_val)
            online_val = players_dict.get("online")
            if isinstance(online_val, int):
                online_players = online_val
            max_val = players_dict.get("max")
            if isinstance(max_val, int):
                max_players = max_val
        return BedrockStatusPlayers(online=online_players, max=max_players)

    @classmethod
    def parse_response(cls, body: bytes, latency: float) -> BedrockStatusResponse:
        """Parse NetherNet HTTP response payload into BedrockStatusResponse.

        :param body: Response payload bytes from the server.
        :param latency: Latency of the request in milliseconds.
        :return: Parsed BedrockStatusResponse instance.
        """
        if not body:
            raise OSError("Received empty response from NetherNet server")

        decoded = body.decode("utf-8", errors="replace").strip()

        # Support traditional semicolon-delimited payload if returned
        if decoded.startswith("MCPE;") or (decoded.count(";") >= 5):
            parts = decoded.split(";")
            if len(parts) >= 6:
                return BedrockStatusResponse.build(parts, latency)

        try:
            raw_data: object = json.loads(decoded)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"Invalid NetherNet status payload: {decoded!r}") from exc

        if not isinstance(raw_data, dict):
            raise TypeError(f"Expected JSON object in NetherNet status response, got {type(raw_data).__name__}")

        raw_dict = cast("dict[str, object]", raw_data)

        return BedrockStatusResponse(
            players=cls._parse_players(raw_dict),
            version=cls._parse_version(raw_dict),
            motd=Motd.parse(cls._parse_motd(raw_dict), bedrock=True),
            latency=latency,
            map_name=None,
            gamemode=None,
        )

    def read_status(self) -> BedrockStatusResponse:
        """Probe the NetherNet server over TCP synchronously."""
        start = perf_counter()
        body = self._read_status()
        end = perf_counter()
        return self.parse_response(body, (end - start) * 1000)

    def _read_status(self) -> bytes:
        conn = http.client.HTTPConnection(self.address.host, self.address.port, timeout=self.timeout)
        try:
            conn.request(
                "GET",
                "/v1/join",
                headers={
                    "User-Agent": "mcstatus",
                    "Accept": "application/json",
                },
            )
            res = conn.getresponse()
            if res.status != 200:
                raise OSError(f"Server returned HTTP {res.status} ({res.reason})")
            return res.read()
        finally:
            conn.close()

    async def read_status_async(self) -> BedrockStatusResponse:
        """Probe the NetherNet server over TCP asynchronously."""
        start = perf_counter()
        body = await self._read_status_async()
        end = perf_counter()
        return self.parse_response(body, (end - start) * 1000)

    async def _read_status_async(self) -> bytes:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.address.host, self.address.port),
            timeout=self.timeout,
        )
        try:
            request = (
                f"GET /v1/join HTTP/1.1\r\n"
                f"Host: {self.address.host}:{self.address.port}\r\n"
                f"User-Agent: mcstatus\r\n"
                f"Accept: application/json\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("ascii")
            writer.write(request)
            await asyncio.wait_for(writer.drain(), timeout=self.timeout)

            status_line = await asyncio.wait_for(reader.readline(), timeout=self.timeout)
            if not status_line:
                raise OSError("Server closed connection without responding to HTTP signaling probe.")

            status_parts = status_line.decode("iso-8859-1", errors="replace").split(" ", 2)
            if len(status_parts) < 2 or not status_parts[1].isdigit() or int(status_parts[1]) != 200:
                status_code = status_parts[1] if len(status_parts) > 1 else "Unknown"
                raise OSError(f"Server returned HTTP {status_code}")

            content_length: int | None = None
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=self.timeout)
                if not line or line in {b"\r\n", b"\n"}:
                    break
                header_str = line.decode("iso-8859-1", errors="replace")
                if ":" in header_str:
                    name, val = header_str.split(":", 1)
                    if name.strip().lower() == "content-length":
                        with contextlib.suppress(ValueError):
                            content_length = int(val.strip())

            if content_length is not None:
                body = await asyncio.wait_for(reader.readexactly(content_length), timeout=self.timeout)
            else:
                body = await asyncio.wait_for(reader.read(), timeout=self.timeout)

            return body
        finally:
            writer.close()
            await writer.wait_closed()
