from __future__ import annotations

import contextlib
import json
import socket
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.bedrock_nethernet_client import BedrockNetherNetClient
from mcstatus.responses import BedrockStatusResponse

if TYPE_CHECKING:
    from collections.abc import Generator

    from typing_extensions import override
else:
    override = lambda f: f  # ruff: ignore[lambda-assignment]

VALID_BODY = (
    b'{"name": "NetherNet Live", "protocol": 100, "version": "1.26.0", '
    b'"players": 2, "maxPlayers": 10, "level": "world", "gameType": 1}'
)


class _NetherNetHandler(BaseHTTPRequestHandler):
    mode: str = "valid"
    status_to_send: int = 200

    def do_GET(self) -> None:
        if self.mode == "valid":
            assert self.path == "/v1/join"
            assert self.headers.get("User-Agent") == "mcstatus"
            assert self.headers.get("Accept") == "application/json"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(VALID_BODY)))
            self.end_headers()
            _ = self.wfile.write(VALID_BODY)
        elif self.mode == "status":
            self.send_error(self.status_to_send)
        elif self.mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/internal")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif self.mode == "oversized":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            _ = self.wfile.write(b"x" * 70000)

    @override
    def log_message(self, format: str, *args: object) -> None:  # ruff: ignore[builtin-argument-shadowing]
        pass


@pytest.fixture
def nethernet_server() -> Generator[tuple[Address, type[_NetherNetHandler]]]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _NetherNetHandler)
    server_thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.005},
        daemon=True,
    )
    server_thread.start()
    try:
        yield Address("127.0.0.1", server.server_port), _NetherNetHandler
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()


def test_url_ipv4():
    client_ipv4 = BedrockNetherNetClient(Address("127.0.0.1", 19132))
    assert client_ipv4.url == "http://127.0.0.1:19132/v1/join"


def test_url_ipv6():
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


@pytest.mark.parametrize(
    "payload",
    [
        b"not json payload",
        b"\xff\xfe\x80invalid utf-8",
        b"",
    ],
)
def test_nethernet_parse_response_invalid_json(payload: bytes):
    with pytest.raises(OSError, match="Invalid NetherNet status payload"):
        _ = BedrockNetherNetClient.parse_response(payload, 1.0)


@pytest.mark.parametrize(
    "payload",
    [
        b"[]",
        b"[1, 2, 3]",
        b'"foobar"',
        b"123",
    ],
)
def test_nethernet_parse_response_non_dict_json(payload: bytes):
    with pytest.raises(OSError, match="Expected JSON object"):
        _ = BedrockNetherNetClient.parse_response(payload, 1.0)


@pytest.mark.parametrize(
    "missing_key",
    ["name", "protocol", "version", "players", "maxPlayers"],
)
def test_nethernet_parse_response_missing_required_fields(missing_key: str):
    full: dict[str, object] = {
        "name": "Server",
        "protocol": 100,
        "version": "1.0",
        "players": 1,
        "maxPlayers": 10,
    }
    _ = full.pop(missing_key)
    with pytest.raises(OSError, match=f"NetherNet status field {missing_key!r}"):
        _ = BedrockNetherNetClient.parse_response(json.dumps(full).encode(), 1.0)


def test_nethernet_parse_response_rejects_string_int():
    body = b'{"name": "Server", "protocol": "2193", "version": "1.0", "players": "1", "maxPlayers": 10}'
    with pytest.raises(OSError, match="must be an integer"):
        _ = BedrockNetherNetClient.parse_response(body, 1.0)


def test_nethernet_parse_response_rejects_non_string():
    body = b'{"name": 12345, "protocol": 2193, "version": "1.0", "players": 1, "maxPlayers": 10}'
    with pytest.raises(OSError, match="must be a string"):
        _ = BedrockNetherNetClient.parse_response(body, 1.0)


@pytest.mark.parametrize(
    ("extra_fields", "expected_map_name", "expected_gamemode"),
    [
        ({}, None, None),
        ({"level": "survival_world"}, "survival_world", None),
        ({"gameType": 0}, None, "Survival"),
        ({"level": "survival_world", "gameType": 1}, "survival_world", "Creative"),
    ],
)
def test_nethernet_parse_response_optional_fields(
    extra_fields: dict[str, object],
    expected_map_name: str | None,
    expected_gamemode: str | None,
):
    payload: dict[str, object] = {
        "name": "Minimal Server",
        "protocol": 900,
        "version": "1.26.50",
        "players": 0,
        "maxPlayers": 5,
        **extra_fields,
    }
    parsed = BedrockNetherNetClient.parse_response(json.dumps(payload).encode(), 1.0)
    assert parsed.motd.to_plain() == "Minimal Server"
    assert parsed.version.protocol == 900
    assert parsed.version.name == "1.26.50"
    assert parsed.players.online == 0
    assert parsed.players.max == 5
    assert parsed.map_name == expected_map_name
    assert parsed.gamemode == expected_gamemode


@pytest.mark.parametrize(
    ("extra_fields", "error_match"),
    [
        ({"gameType": -5}, "Unknown NetherNet gameType -5"),
        ({"gameType": 99}, "Unknown NetherNet gameType 99"),
        ({"gameType": "Survival"}, "must be an integer"),
        ({"level": 123}, "must be a string"),
        ({"level": {"nested": "dict"}}, "must be a string"),
    ],
)
def test_nethernet_parse_response_invalid_optional_fields(
    extra_fields: dict[str, object],
    error_match: str,
):
    payload: dict[str, object] = {
        "name": "Server",
        "protocol": 100,
        "version": "1.0",
        "players": 1,
        "maxPlayers": 10,
        **extra_fields,
    }
    with pytest.raises(OSError, match=error_match):
        _ = BedrockNetherNetClient.parse_response(json.dumps(payload).encode(), 1.0)


def test_read_status_sync_success(nethernet_server: tuple[Address, type[_NetherNetHandler]]):
    addr, handler = nethernet_server
    handler.mode = "valid"
    client = BedrockNetherNetClient(addr)
    res = client.read_status()

    assert isinstance(res, BedrockStatusResponse)
    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"
    assert res.version.protocol == 100
    assert res.version.brand is None
    assert res.players.online == 2
    assert res.players.max == 10
    assert res.gamemode == "Creative"
    assert res.map_name == "world"
    assert res.latency >= 0


async def test_read_status_async_success(nethernet_server: tuple[Address, type[_NetherNetHandler]]):
    addr, handler = nethernet_server
    handler.mode = "valid"
    client = BedrockNetherNetClient(addr)
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


@pytest.mark.parametrize("status_code", [404, 500])
def test_read_status_http_error(
    nethernet_server: tuple[Address, type[_NetherNetHandler]],
    status_code: int,
):
    addr, handler = nethernet_server
    handler.mode = "status"
    handler.status_to_send = status_code
    client = BedrockNetherNetClient(addr)

    with pytest.raises(OSError, match=f"Server returned HTTP {status_code}"):
        _ = client.read_status()


def test_read_status_refuses_redirect(nethernet_server: tuple[Address, type[_NetherNetHandler]]):
    addr, handler = nethernet_server
    handler.mode = "redirect"
    client = BedrockNetherNetClient(addr)

    with pytest.raises(OSError, match="Server returned HTTP 302"):
        _ = client.read_status()


def test_read_status_stream_size_cap(nethernet_server: tuple[Address, type[_NetherNetHandler]]):
    addr, handler = nethernet_server
    handler.mode = "oversized"
    client = BedrockNetherNetClient(addr)

    with pytest.raises(OSError, match=r"^NetherNet signaling response exceeded 65536 bytes$"):
        _ = client.read_status()


def test_read_status_malformed_response():
    raw = socket.socket()
    raw.bind(("127.0.0.1", 0))
    raw.listen(1)
    port = raw.getsockname()[1]

    def send_garbage() -> None:
        conn, _ = raw.accept()
        _ = conn.recv(1024)
        conn.sendall(b"NOT HTTP AT ALL\r\n\r\n")
        conn.close()
        raw.close()

    threading.Thread(target=send_garbage, daemon=True).start()
    client = BedrockNetherNetClient(Address("127.0.0.1", port))

    with pytest.raises(OSError, match="Invalid HTTP response from NetherNet signaling server"):
        _ = client.read_status()


def test_read_status_connection_refused():
    raw = socket.socket()
    raw.bind(("127.0.0.1", 0))
    port = raw.getsockname()[1]
    raw.close()

    client = BedrockNetherNetClient(Address("127.0.0.1", port))
    with pytest.raises(ConnectionRefusedError):
        _ = client.read_status()


def test_read_status_dns_failure():
    client = BedrockNetherNetClient(Address("127.0.0.1", 19132))
    gai_err = socket.gaierror(-2, "Name or service not known")
    with (
        patch.object(client._OPENER, "open", side_effect=urllib.error.URLError(gai_err)),
        pytest.raises(socket.gaierror, match="Name or service not known"),
    ):
        _ = client.read_status()


def test_read_status_timeout():
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw.bind(("127.0.0.1", 0))
    raw.listen(1)
    port = raw.getsockname()[1]
    unresponsive_event = threading.Event()

    def unresponsive_worker() -> None:
        with contextlib.suppress(OSError):
            conn, _ = raw.accept()
            _ = unresponsive_event.wait(timeout=2)
            conn.close()

    server_thread = threading.Thread(target=unresponsive_worker, daemon=True)
    server_thread.start()
    try:
        client = BedrockNetherNetClient(Address("127.0.0.1", port), timeout=0.05)
        with pytest.raises(TimeoutError):
            _ = client.read_status()
    finally:
        unresponsive_event.set()
        raw.close()
        server_thread.join()


def test_read_status_non_oserror_urlerror():
    client = BedrockNetherNetClient(Address("127.0.0.1", 19132))
    with (
        patch.object(client._OPENER, "open", side_effect=urllib.error.URLError("ssl certificate verify failed")),
        pytest.raises(OSError, match="Failed to connect to NetherNet signaling server: ssl certificate verify failed"),
    ):
        _ = client.read_status()


async def test_read_status_async_error_propagation():
    client = BedrockNetherNetClient(Address("127.0.0.1", 19132))
    with (
        patch.object(client._OPENER, "open", side_effect=urllib.error.URLError(TimeoutError("timed out"))),
        pytest.raises(TimeoutError, match="timed out"),
    ):
        _ = await client.read_status_async()
