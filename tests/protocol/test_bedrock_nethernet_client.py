from __future__ import annotations

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
            if self.headers.get("User-Agent") != "mcstatus" or self.headers.get("Accept") != "application/json":
                self.send_error(400, "Bad headers")
                return
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


def test_nethernet_parse_response_rejects_non_string():
    body = b'{"name": 12345, "protocol": 2193, "version": "1.0", "players": 1, "maxPlayers": 10}'
    with pytest.raises(OSError, match="must be a string"):
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
    client = BedrockNetherNetClient(Address("127.0.0.1", 19132))
    with (
        patch.object(client._OPENER, "open", side_effect=urllib.error.URLError(TimeoutError("timed out"))),
        pytest.raises(TimeoutError, match="timed out"),
    ):
        _ = client.read_status()


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
