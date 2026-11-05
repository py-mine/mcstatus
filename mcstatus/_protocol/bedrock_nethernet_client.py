from __future__ import annotations

import asyncio
import http.client
import json
import urllib.error
import urllib.request
from time import perf_counter
from typing import ClassVar, TYPE_CHECKING, cast, final

from mcstatus.motd import Motd
from mcstatus.responses import BedrockStatusPlayers, BedrockStatusResponse, BedrockStatusVersion

if TYPE_CHECKING:
    from typing_extensions import override

    from mcstatus._net.address import Address
else:
    override = lambda f: f  # ruff: ignore[lambda-assignment]


__all__ = ["BedrockNetherNetClient"]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so a queried server cannot point mcstatus at an arbitrary URL."""

    @override
    def redirect_request(self, *args: object, **kwargs: object) -> None:  # ruff: ignore[unused-method-argument]
        return None


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
    _OPENER: ClassVar[urllib.request.OpenerDirector] = urllib.request.build_opener(_NoRedirectHandler)

    def __init__(self, address: Address, timeout: float = 3) -> None:
        self.address = address
        self.timeout = timeout

    @property
    def url(self) -> str:
        host = f"[{self.address.host}]" if ":" in self.address.host else self.address.host
        return f"http://{host}:{self.address.port}/v1/join"

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

    def read_status(self) -> BedrockStatusResponse:
        """Probe the NetherNet server synchronously."""
        request = urllib.request.Request(self.url, headers=self.HEADERS)  # ruff: ignore[suspicious-url-open-usage] # always http://
        start = perf_counter()
        try:
            with self._OPENER.open(request, timeout=self.timeout) as response:
                body: bytes = response.read(self.MAX_RESPONSE_SIZE + 1)
        except urllib.error.HTTPError as exc:
            raise OSError(f"Server returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, OSError):
                raise exc.reason from None
            raise OSError(f"Failed to connect to NetherNet signaling server: {exc.reason}") from exc
        except http.client.HTTPException as exc:
            raise OSError(f"Invalid HTTP response from NetherNet signaling server: {exc!r}") from exc
        latency = (perf_counter() - start) * 1000

        if len(body) > self.MAX_RESPONSE_SIZE:
            raise OSError(f"NetherNet signaling response exceeded {self.MAX_RESPONSE_SIZE} bytes")
        return self.parse_response(body, latency)

    async def read_status_async(self) -> BedrockStatusResponse:
        """Probe the NetherNet server asynchronously.

        .. note::
            Delegates to :meth:`read_status` via :func:`asyncio.to_thread`.
            If the probe task is cancelled while blocked on a network socket,
            the underlying thread continues running until the socket timeout expires.
        """
        return await asyncio.to_thread(self.read_status)
