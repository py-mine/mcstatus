import sys
import time
from unittest import mock

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.bedrock_nethernet_client import BedrockNetherNetClient
from mcstatus.responses import BedrockStatusResponse


def test_nethernet_parse_response_with_json_body():
    http_data = (
        b"HTTP/1.1 200 OK\r\n"
        b"Server: NetherNet/1.0\r\n"
        b"Content-Type: application/json\r\n"
        b"\r\n"
        b'{"motd": "NetherNet Survival Server", "version": {"name": "1.26.52", "protocol": 2193}, '
        b'"players": {"online": 3, "max": 20}}'
    )
    parsed = BedrockNetherNetClient.parse_response(http_data, 5.0)

    assert isinstance(parsed, BedrockStatusResponse)
    assert parsed.version.name == "1.26.52"
    assert parsed.version.protocol == 2193
    assert parsed.version.brand == "MCPE"
    assert parsed.players.online == 3
    assert parsed.players.max == 20
    assert parsed.motd.to_plain() == "NetherNet Survival Server"
    assert parsed.latency == pytest.approx(5.0)


def test_nethernet_parse_response_with_semicolon_body():
    http_data = b"HTTP/1.1 200 OK\r\n\r\nMCPE;\xc2\xa7rServer Name;422;1.18.10;1;10;12345;World;Default;1;19132;-1;"
    parsed = BedrockNetherNetClient.parse_response(http_data, 2.5)

    assert isinstance(parsed, BedrockStatusResponse)
    assert parsed.version.name == "1.18.10"
    assert parsed.version.protocol == 422
    assert parsed.players.online == 1
    assert parsed.players.max == 10
    assert parsed.latency == pytest.approx(2.5)


def test_nethernet_parse_response_headers_only():
    http_data = b"HTTP/1.1 500 Internal Server Error\r\nServer: BDS-NetherNet\r\nContent-Length: 0\r\n\r\n"
    parsed = BedrockNetherNetClient.parse_response(http_data, 1.2)

    assert isinstance(parsed, BedrockStatusResponse)
    assert parsed.version.name == "BDS-NetherNet"
    assert parsed.version.protocol == -1
    assert parsed.players.online == -1
    assert parsed.players.max == -1
    assert parsed.latency == pytest.approx(1.2)


@pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
def test_nethernet_latency_is_real_number():
    def mocked_read_status():
        time.sleep(0.001)
        return b"HTTP/1.1 200 OK\r\n\r\n"

    client = BedrockNetherNetClient(Address("localhost", 19132))
    with (
        mock.patch.object(client, "_read_status") as mocked_read,
        mock.patch.object(client, "parse_response") as mocked_parse_response,
    ):
        mocked_read.side_effect = mocked_read_status

        _ = client.read_status()
        assert mocked_parse_response.call_args[0][1] >= 1


@pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
async def test_nethernet_async_latency_is_real_number():
    def mocked_read_status():
        time.sleep(0.001)
        return b"HTTP/1.1 200 OK\r\n\r\n"

    client = BedrockNetherNetClient(Address("localhost", 19132))
    with (
        mock.patch.object(client, "_read_status_async") as mocked_read,
        mock.patch.object(client, "parse_response") as mocked_parse_response,
    ):
        mocked_read.side_effect = mocked_read_status

        _ = await client.read_status_async()
        assert mocked_parse_response.call_args[0][1] >= 1
