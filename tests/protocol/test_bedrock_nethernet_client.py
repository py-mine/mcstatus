from __future__ import annotations

import http.server
import socket
import threading
from typing import TYPE_CHECKING, cast

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.bedrock_nethernet_client import BedrockNetherNetClient
from mcstatus.responses import BedrockStatusResponse

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from typing_extensions import override
else:
    override = lambda f: f  # ruff: ignore[lambda-assignment]


class NetherNetMockServer(http.server.ThreadingHTTPServer):
    custom_handler: Callable[[http.server.BaseHTTPRequestHandler], None] | None = None


class NetherNetHTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        server = cast("NetherNetMockServer", self.server)
        if server.custom_handler is not None:
            server.custom_handler(self)
            return

        body = (
            b'{"motd": "NetherNet Live", "version": {"name": "1.26.0", "protocol": 100}, "players": {"online": 2, "max": 10}}'
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        _ = self.wfile.write(body)

    @override
    def log_message(self, format: str, *args: object) -> None:  # ruff: ignore[builtin-argument-shadowing]
        pass


@pytest.fixture
def nethernet_server() -> Generator[NetherNetMockServer]:
    server = NetherNetMockServer(("127.0.0.1", 0), NetherNetHTTPHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def test_nethernet_parse_response_with_json_body():
    body = (
        b'{"motd": "NetherNet Survival Server", "version": {"name": "1.26.52", "protocol": 2193}, '
        b'"players": {"online": 3, "max": 20}}'
    )
    parsed = BedrockNetherNetClient.parse_response(body, 5.0)

    assert isinstance(parsed, BedrockStatusResponse)
    assert parsed.version.name == "1.26.52"
    assert parsed.version.protocol == 2193
    assert parsed.version.brand == "MCPE"
    assert parsed.players.online == 3
    assert parsed.players.max == 20
    assert parsed.motd.to_plain() == "NetherNet Survival Server"
    assert parsed.latency == pytest.approx(5.0)


def test_nethernet_parse_response_with_semicolon_body():
    body = b"MCPE;\xc2\xa7rServer Name;422;1.18.10;1;10;12345;World;Default;1;19132;-1;"
    parsed = BedrockNetherNetClient.parse_response(body, 2.5)

    assert isinstance(parsed, BedrockStatusResponse)
    assert parsed.version.name == "1.18.10"
    assert parsed.version.protocol == 422
    assert parsed.players.online == 1
    assert parsed.players.max == 10
    assert parsed.latency == pytest.approx(2.5)


def test_nethernet_parse_response_empty_body():
    with pytest.raises(OSError, match="Received empty response"):
        _ = BedrockNetherNetClient.parse_response(b"", 1.0)


def test_nethernet_parse_response_invalid_json():
    with pytest.raises(ValueError, match="Invalid NetherNet status payload"):
        _ = BedrockNetherNetClient.parse_response(b"not json payload", 1.0)


def test_nethernet_parse_response_non_dict_json():
    with pytest.raises(TypeError, match="Expected JSON object"):
        _ = BedrockNetherNetClient.parse_response(b"[1, 2, 3]", 1.0)


def test_nethernet_parse_response_defaults():
    body = b"{}"
    parsed = BedrockNetherNetClient.parse_response(body, 1.0)

    assert parsed.version.name == "NetherNet"
    assert parsed.version.protocol == -1
    assert parsed.players.online == -1
    assert parsed.players.max == -1
    assert parsed.motd.to_plain() == "NetherNet Bedrock Server"


def test_nethernet_parse_response_partial_fields():
    body = b'{"motd": "Custom", "version": {"name": "1.0"}, "players": {"online": 5}}'
    parsed = BedrockNetherNetClient.parse_response(body, 1.0)

    assert parsed.motd.to_plain() == "Custom"
    assert parsed.version.name == "1.0"
    assert parsed.version.protocol == -1
    assert parsed.players.online == 5
    assert parsed.players.max == -1


def test_read_status_sync_success(nethernet_server: NetherNetMockServer):
    client = BedrockNetherNetClient(Address("127.0.0.1", nethernet_server.server_address[1]))
    res = client.read_status()

    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"
    assert res.version.protocol == 100
    assert res.players.online == 2
    assert res.players.max == 10
    assert res.latency > 0


def test_read_status_sync_http_error(nethernet_server: NetherNetMockServer):
    def error_handler(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(500)
        h.end_headers()

    nethernet_server.custom_handler = error_handler
    client = BedrockNetherNetClient(Address("127.0.0.1", nethernet_server.server_address[1]))

    with pytest.raises(OSError, match="Server returned HTTP 500"):
        _ = client.read_status()


async def test_read_status_async_success(nethernet_server: NetherNetMockServer):
    client = BedrockNetherNetClient(Address("127.0.0.1", nethernet_server.server_address[1]))
    res = await client.read_status_async()

    assert res.motd.to_plain() == "NetherNet Live"
    assert res.version.name == "1.26.0"
    assert res.version.protocol == 100
    assert res.players.online == 2
    assert res.players.max == 10
    assert res.latency > 0


async def test_read_status_async_no_content_length(nethernet_server: NetherNetMockServer):
    def chunk_handler(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(200)
        h.send_header("Connection", "close")
        h.end_headers()
        _ = h.wfile.write(b'{"motd": "No Content Length"}')

    nethernet_server.custom_handler = chunk_handler
    client = BedrockNetherNetClient(Address("127.0.0.1", nethernet_server.server_address[1]))
    res = await client.read_status_async()

    assert res.motd.to_plain() == "No Content Length"


async def test_read_status_async_http_error(nethernet_server: NetherNetMockServer):
    def error_handler(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(404)
        h.end_headers()

    nethernet_server.custom_handler = error_handler
    client = BedrockNetherNetClient(Address("127.0.0.1", nethernet_server.server_address[1]))

    with pytest.raises(OSError, match="Server returned HTTP 404"):
        _ = await client.read_status_async()


async def test_read_status_async_closed_prematurely():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    def accept_and_close() -> None:
        client_s, _ = server_sock.accept()
        _ = client_s.recv(1024)
        client_s.close()

    thread = threading.Thread(target=accept_and_close, daemon=True)
    thread.start()

    client = BedrockNetherNetClient(Address("127.0.0.1", port))
    with pytest.raises(OSError, match="Server closed connection"):
        _ = await client.read_status_async()

    server_sock.close()


async def test_read_status_async_malformed_status():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    def send_malformed() -> None:
        client_s, _ = server_sock.accept()
        _ = client_s.sendall(b"NOT_HTTP\r\n\r\n")
        client_s.close()

    thread = threading.Thread(target=send_malformed, daemon=True)
    thread.start()

    client = BedrockNetherNetClient(Address("127.0.0.1", port))
    with pytest.raises(OSError, match="Server returned HTTP Unknown"):
        _ = await client.read_status_async()

    server_sock.close()


async def test_read_status_async_invalid_content_length(nethernet_server: NetherNetMockServer):
    def invalid_cl_handler(h: http.server.BaseHTTPRequestHandler) -> None:
        h.send_response(200)
        h.send_header("Content-Length", "invalid")
        h.send_header("Connection", "close")
        h.end_headers()
        _ = h.wfile.write(b'{"motd": "Fallback"}')

    nethernet_server.custom_handler = invalid_cl_handler
    client = BedrockNetherNetClient(Address("127.0.0.1", nethernet_server.server_address[1]))
    res = await client.read_status_async()

    assert res.motd.to_plain() == "Fallback"
