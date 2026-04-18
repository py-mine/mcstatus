import pytest

from mcstatus._protocol.legacy_client import LegacyClient
from mcstatus.motd import Motd
from mcstatus.responses.legacy import LegacyStatusPlayers, LegacyStatusResponse, LegacyStatusVersion
from tests.protocol.helpers import SyncBufferConnection


def test_invalid_kick_reason():
    with pytest.raises(IOError, match=r"^Received invalid kick packet reason$"):
        _ = LegacyClient.parse_response("Invalid Reason".encode("UTF-16BE"), 123.0)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (
            "A Minecraft Server§0§20".encode("UTF-16BE"),
            LegacyStatusResponse(
                players=LegacyStatusPlayers(online=0, max=20),
                version=LegacyStatusVersion(name="<1.4", protocol=-1),
                motd=Motd.parse("A Minecraft Server"),
                latency=123.0,
            ),
        ),
        (
            "§1\x0051\x001.4.7\x00A Minecraft Server\x000\x0020".encode("UTF-16BE"),
            LegacyStatusResponse(
                players=LegacyStatusPlayers(online=0, max=20),
                version=LegacyStatusVersion(name="1.4.7", protocol=51),
                motd=Motd.parse("A Minecraft Server"),
                latency=123.0,
            ),
        ),
    ],
    ids=["b1.8", "1.4.7"],
)
def test_parse_response(response: bytes, expected: LegacyStatusResponse):
    assert LegacyClient.parse_response(response, 123.0) == expected


def test_invalid_packet_id():
    socket = SyncBufferConnection()
    socket.receive(bytearray.fromhex("00"))
    server = LegacyClient(socket)
    with pytest.raises(IOError, match=r"^Received invalid packet ID$"):
        _ = server.read_status()
