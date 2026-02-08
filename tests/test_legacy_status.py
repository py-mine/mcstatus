import pytest

from mcstatus.protocol.connection import Connection
from mcstatus.legacy_status import LegacyServerStatus


def test_invalid_kick_reason():
    with pytest.raises(IOError, match=r"^Received invalid kick packet reason$"):
        LegacyServerStatus.parse_response("Invalid Reason".encode("UTF-16BE"), 123.0)


def test_invalid_packet_id():
    socket = Connection()
    socket.receive(bytearray.fromhex("00"))
    server = LegacyServerStatus(socket)
    with pytest.raises(IOError, match=r"^Received invalid packet ID$"):
        server.read_status()
