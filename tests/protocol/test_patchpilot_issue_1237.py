import socket
from unittest import mock

from mcstatus._net.address import Address
from mcstatus._protocol.bedrock_client import BedrockClient


def _record_socket_family(client: BedrockClient) -> int:
    """Call the sync read path with a fake socket and return the address family used."""
    fake_socket = mock.MagicMock()
    fake_socket.recvfrom.return_value = (b"\x00" * 100, None)

    with mock.patch("mcstatus._protocol.bedrock_client.socket.socket", return_value=fake_socket) as mock_socket:
        _ = client._read_status()

    args = mock_socket.call_args.args
    if args:
        return args[0]
    return mock_socket.call_args.kwargs["family"]


def test_bedrock_client_uses_ipv6_socket_for_ipv6_address():
    """Issue #1237: the RakNet (Bedrock) client must not hardcode an IPv4 socket.

    With an IPv6 address (e.g. ``[::1]``) the socket must be created with the
    IPv6 address family, otherwise ``sendto`` fails with
    ``socket.gaierror: Address family for hostname not supported``.
    """
    client = BedrockClient(Address("::1", 19132))
    assert _record_socket_family(client) == socket.AF_INET6


def test_bedrock_client_uses_ipv4_socket_for_ipv4_address():
    client = BedrockClient(Address("127.0.0.1", 19132))
    assert _record_socket_family(client) == socket.AF_INET
