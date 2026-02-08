import pytest

from mcstatus._protocol.connection import Connection
from mcstatus._protocol.legacy_client import LegacyClient


def test_invalid_kick_reason():
    with pytest.raises(IOError, match=r"^Received invalid kick packet reason$"):
        LegacyClient.parse_response("Invalid Reason".encode("UTF-16BE"), 123.0)


def test_invalid_packet_id():
    socket = Connection()
    socket.receive(bytearray.fromhex("00"))
    server = LegacyClient(socket)
    with pytest.raises(IOError, match=r"^Received invalid packet ID$"):
        server.read_status()
