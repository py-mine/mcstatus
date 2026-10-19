from __future__ import annotations

import json
from time import perf_counter
from typing import ClassVar, TYPE_CHECKING, cast, final

import httpx2

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
    """

    MAX_RESPONSE_SIZE: ClassVar[int] = 64 * 1024
    GAMEMODES: ClassVar[dict[int, str]] = {0: "Survival", 1: "Creative", 2: "Adventure"}
    HEADERS: ClassVar[dict[str, str]] = {"User-Agent": "mcstatus", "Accept": "application/json"}

    def __init__(self, address: Address, timeout: float = 3) -> None:
        self.address = address
        self.timeout = timeout

    @property
    def url(self) -> str:
        host = f"[{self.address.host}]" if ":" in self.address.host else self.address.host
        return f"http://{host}:{self.address.port}/v1/join"

    @classmethod
    def _validate_response_headers(cls, response: httpx2.Response) -> None:
        if not 200 <= response.status_code < 300:
            raise OSError(f"Server returned HTTP {response.status_code}")

        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError as exc:
                raise OSError(f"Invalid Content-Length header: {content_length!r}") from exc
            if length < 0:
                raise OSError(f"Invalid Content-Length header: {content_length!r}")
            if length > cls.MAX_RESPONSE_SIZE:
                raise OSError(f"NetherNet signaling response exceeded {cls.MAX_RESPONSE_SIZE} bytes")

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
                brand=None,
            ),
            motd=Motd.parse(cls._require_str(raw, "name"), bedrock=True),
            latency=latency,
            map_name=level if isinstance(level, str) else None,
            gamemode=cls.GAMEMODES.get(game_type) if isinstance(game_type, int) else None,
        )

    def _consume_stream(self, response: httpx2.Response) -> bytes:
        self._validate_response_headers(response)
        raw = bytearray()
        for chunk in response.iter_bytes():
            raw.extend(chunk)
            if len(raw) > self.MAX_RESPONSE_SIZE:
                raise OSError(f"NetherNet signaling response exceeded {self.MAX_RESPONSE_SIZE} bytes")
        return bytes(raw)

    async def _async_consume_stream(self, response: httpx2.Response) -> bytes:
        self._validate_response_headers(response)
        raw = bytearray()
        async for chunk in response.aiter_bytes():
            raw.extend(chunk)
            if len(raw) > self.MAX_RESPONSE_SIZE:
                raise OSError(f"NetherNet signaling response exceeded {self.MAX_RESPONSE_SIZE} bytes")
        return bytes(raw)

    def read_status(self) -> BedrockStatusResponse:
        """Probe the NetherNet server synchronously."""
        start = perf_counter()
        try:
            with (
                httpx2.Client(timeout=self.timeout) as client,
                client.stream("GET", self.url, headers=self.HEADERS) as response,
            ):
                raw = self._consume_stream(response)
        except httpx2.TimeoutException as exc:
            raise TimeoutError("timed out") from exc
        except (httpx2.RequestError, httpx2.InvalidURL) as exc:
            raise OSError(f"Failed to connect to NetherNet signaling server: {exc}") from exc

        end = perf_counter()
        return self.parse_response(raw, (end - start) * 1000)

    async def read_status_async(self) -> BedrockStatusResponse:
        """Probe the NetherNet server asynchronously."""
        start = perf_counter()
        try:
            async with (
                httpx2.AsyncClient(timeout=self.timeout) as client,
                client.stream("GET", self.url, headers=self.HEADERS) as response,
            ):
                raw = await self._async_consume_stream(response)
        except httpx2.TimeoutException as exc:
            raise TimeoutError("timed out") from exc
        except (httpx2.RequestError, httpx2.InvalidURL) as exc:
            raise OSError(f"Failed to connect to NetherNet signaling server: {exc}") from exc

        end = perf_counter()
        return self.parse_response(raw, (end - start) * 1000)
