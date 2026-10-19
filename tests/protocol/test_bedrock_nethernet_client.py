from __future__ import annotations

import contextlib
import functools
from typing import TYPE_CHECKING, final
from unittest.mock import patch

import httpx2
import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.bedrock_nethernet_client import BedrockNetherNetClient
from mcstatus.responses import BedrockStatusResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Generator

    from typing_extensions import override
else:
    override = lambda f: f  # ruff: ignore[lambda-assignment]

VALID_BODY = (
    b'{"name": "NetherNet Live", "protocol": 100, "version": "1.26.0", '
    b'"players": 2, "maxPlayers": 10, "level": "world", "gameType": 1}'
)


@final
class IterableStream(httpx2.SyncByteStream, httpx2.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    @override
    def __iter__(self) -> Generator[bytes]:
        yield from self.chunks

    @override
    async def __aiter__(self) -> AsyncGenerator[bytes]:
        for chunk in self.chunks:
            yield chunk


@contextlib.contextmanager
def mock_nethernet_transport(
    handler: Callable[[httpx2.Request], httpx2.Response],
) -> Generator[BedrockNetherNetClient]:
    transport = httpx2.MockTransport(handler)
    with (
        patch(
            "mcstatus._protocol.bedrock_nethernet_client.httpx2.Client",
            side_effect=functools.partial(httpx2.Client, transport=transport),
        ),
        patch(
            "mcstatus._protocol.bedrock_nethernet_client.httpx2.AsyncClient",
            side_effect=functools.partial(httpx2.AsyncClient, transport=transport),
        ),
    ):
        yield BedrockNetherNetClient(Address("127.0.0.1", 19132))


def test_url_ipv4_and_ipv6():
    client_ipv4 = BedrockNetherNetClient(Address("127.0.0.1", 19132))
    assert client_ipv4.url == "http://127.0.0.1:19132/v1/join"

    client_ipv6 = BedrockNetherNetClient(Address("::1", 19132))
    assert client_ipv6.url == "http://[::1]:19132/v1/join"


def test_nethernet_parse_response_with_json_body():
    body = (
        b'{"name": "NetherNet Survival Server", "protocol": 2193, "version": "1.26.52", '
        b'"players": 3, "maxPlayers": 20, "level": "survival_world", "gameType": 0}'
    )
    parsed = BedrockNetherNetClient.parse_response(body, 5.0)

    assert isinstance(parsed, BedrockStatusResponse)
    assert parsed.version.name == "1.26.52"
    assert parsed.version.protocol == 2193
    assert parsed.version.brand is None
    assert parsed.players.online == 3
    assert parsed.players.max == 20
    assert parsed.motd.to_plain() == "NetherNet Survival Server"
    assert parsed.map_name == "survival_world"
    assert parsed.gamemode == "Survival"
    assert parsed.latency == pytest.approx(5.0)


def test_nethernet_parse_response_empty_body():
    with pytest.raises(OSError, match="Invalid NetherNet status payload"):
        _ = BedrockNetherNetClient.parse_response(b"", 1.0)


def test_nethernet_parse_response_invalid_json():
    with pytest.raises(OSError, match="Invalid NetherNet status payload"):
        _ = BedrockNetherNetClient.parse_response(b"not json payload", 1.0)


def test_nethernet_parse_response_non_dict_json():
    with pytest.raises(OSError, match="Expected JSON object"):
        _ = BedrockNetherNetClient.parse_response(b"[1, 2, 3]", 1.0)


def test_nethernet_parse_response_missing_required_fields():
    body = b'{"name": "Server", "players": 1}'
    with pytest.raises(OSError, match="NetherNet status field"):
        _ = BedrockNetherNetClient.parse_response(body, 1.0)


def test_nethernet_parse_response_rejects_string_int():
    body = b'{"name": "Server", "protocol": "2193", "version": "1.0", "players": "1", "maxPlayers": 10}'
    with pytest.raises(OSError, match="must be an integer"):
        _ = BedrockNetherNetClient.parse_response(body, 1.0)


def test_nethernet_parse_response_optional_fields():
    body = b'{"name": "Minimal Server", "protocol": 900, "version": "1.26.50", "players": 0, "maxPlayers": 5}'
    parsed = BedrockNetherNetClient.parse_response(body, 1.0)
    assert parsed.motd.to_plain() == "Minimal Server"
    assert parsed.version.protocol == 900
    assert parsed.version.name == "1.26.50"
    assert parsed.players.online == 0
    assert parsed.players.max == 5
    assert parsed.map_name is None
    assert parsed.gamemode is None


def test_read_status_sync_success():
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.headers["User-Agent"] == "mcstatus"
        assert request.headers["Accept"] == "application/json"
        return httpx2.Response(200, content=VALID_BODY)

    with mock_nethernet_transport(handler) as client:
        res = client.read_status()

    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"
    assert res.version.protocol == 100
    assert res.version.brand is None
    assert res.players.online == 2
    assert res.players.max == 10
    assert res.gamemode == "Creative"
    assert res.map_name == "world"
    assert res.latency >= 0


async def test_read_status_async_success():
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.headers["User-Agent"] == "mcstatus"
        assert request.headers["Accept"] == "application/json"
        return httpx2.Response(200, content=VALID_BODY)

    with mock_nethernet_transport(handler) as client:
        res = await client.read_status_async()

    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"
    assert res.version.protocol == 100
    assert res.version.brand is None
    assert res.players.online == 2
    assert res.players.max == 10
    assert res.gamemode == "Creative"
    assert res.map_name == "world"
    assert res.latency >= 0


def test_read_status_sync_no_content_length():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, stream=IterableStream([VALID_BODY]))

    with mock_nethernet_transport(handler) as client:
        res = client.read_status()

    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"


async def test_read_status_async_no_content_length():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, stream=IterableStream([VALID_BODY]))

    with mock_nethernet_transport(handler) as client:
        res = await client.read_status_async()

    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"


@pytest.mark.parametrize("status_code", [404, 500])
def test_read_status_sync_http_error(status_code: int):
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status_code)

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match=f"Server returned HTTP {status_code}"):
        _ = client.read_status()


@pytest.mark.parametrize("status_code", [404, 500])
async def test_read_status_async_http_error(status_code: int):
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status_code)

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match=f"Server returned HTTP {status_code}"):
        _ = await client.read_status_async()


@pytest.mark.parametrize("bad_header", ["invalid", "-1"])
def test_read_status_sync_invalid_content_length(bad_header: str):
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, headers={"Content-Length": bad_header}, stream=IterableStream([VALID_BODY]))

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match="Invalid Content-Length header"):
        _ = client.read_status()


@pytest.mark.parametrize("bad_header", ["invalid", "-1"])
async def test_read_status_async_invalid_content_length(bad_header: str):
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, headers={"Content-Length": bad_header}, stream=IterableStream([VALID_BODY]))

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match="Invalid Content-Length header"):
        _ = await client.read_status_async()


def test_read_status_sync_content_length_exceeded():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, headers={"Content-Length": str(100 * 1024)}, stream=IterableStream([VALID_BODY]))

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match="exceeded 65536 bytes"):
        _ = client.read_status()


async def test_read_status_async_content_length_exceeded():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, headers={"Content-Length": str(100 * 1024)}, stream=IterableStream([VALID_BODY]))

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match="exceeded 65536 bytes"):
        _ = await client.read_status_async()


def test_read_status_sync_stream_size_cap():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, stream=IterableStream([b"x" * 40000, b"x" * 40000]))

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match="exceeded 65536 bytes"):
        _ = client.read_status()


async def test_read_status_async_stream_size_cap():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, stream=IterableStream([b"x" * 40000, b"x" * 40000]))

    with mock_nethernet_transport(handler) as client, pytest.raises(OSError, match="exceeded 65536 bytes"):
        _ = await client.read_status_async()


def test_read_status_sync_timeout():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("timed out")

    with mock_nethernet_transport(handler) as client, pytest.raises(TimeoutError, match="timed out"):
        _ = client.read_status()


async def test_read_status_async_timeout():
    def handler(_request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("timed out")

    with mock_nethernet_transport(handler) as client, pytest.raises(TimeoutError, match="timed out"):
        _ = await client.read_status_async()


@pytest.mark.parametrize("exc_to_raise", [httpx2.RemoteProtocolError("malformed"), httpx2.ConnectError("closed")])
def test_read_status_sync_network_error(exc_to_raise: Exception):
    def handler(_request: httpx2.Request) -> httpx2.Response:
        raise exc_to_raise

    with (
        mock_nethernet_transport(handler) as client,
        pytest.raises(OSError, match="Failed to connect to NetherNet signaling server"),
    ):
        _ = client.read_status()


@pytest.mark.parametrize("exc_to_raise", [httpx2.RemoteProtocolError("malformed"), httpx2.ConnectError("closed")])
async def test_read_status_async_network_error(exc_to_raise: Exception):
    def handler(_request: httpx2.Request) -> httpx2.Response:
        raise exc_to_raise

    with (
        mock_nethernet_transport(handler) as client,
        pytest.raises(OSError, match="Failed to connect to NetherNet signaling server"),
    ):
        _ = await client.read_status_async()
