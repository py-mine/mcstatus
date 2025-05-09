import sys
import time
from unittest import mock

import pytest

from mcstatus.address import Address
from mcstatus.pinger import ServerPinger
from mcstatus.protocol.connection import Connection


class TestServerPinger:
    def setup_method(self):
        self.pinger = ServerPinger(
            Connection(),  # type: ignore[arg-type]
            address=Address("localhost", 25565),
            version=44,
        )

    def test_handshake(self):
        self.pinger.handshake()

        assert self.pinger.connection.flush() == bytearray.fromhex("0F002C096C6F63616C686F737463DD01")

    def test_read_status(self):
        self.pinger.connection.receive(
            bytearray.fromhex(
                "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C22"
                "70726F746F636F6C223A34347D7D"
            )
        )
        status = self.pinger.read_status()

        assert status.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
        }
        assert self.pinger.connection.flush() == bytearray.fromhex("0100")

    def test_read_status_invalid_json(self):
        self.pinger.connection.receive(bytearray.fromhex("0300017B"))
        with pytest.raises(IOError):
            self.pinger.read_status()

    def test_read_status_invalid_reply(self):
        self.pinger.connection.receive(
            # no motd, see also #922
            bytearray.fromhex(
                "4F004D7B22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616"
                "D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"
            )
        )

        self.pinger.read_status()

    def test_read_status_invalid_status(self):
        self.pinger.connection.receive(bytearray.fromhex("0105"))

        with pytest.raises(IOError):
            self.pinger.read_status()

    def test_test_ping(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 14515484

        assert self.pinger.test_ping() >= 0
        assert self.pinger.connection.flush() == bytearray.fromhex("09010000000000DD7D1C")

    def test_test_ping_invalid(self):
        self.pinger.connection.receive(bytearray.fromhex("011F"))
        self.pinger.ping_token = 14515484

        with pytest.raises(IOError):
            self.pinger.test_ping()

    def test_test_ping_wrong_token(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 12345

        with pytest.raises(IOError):
            self.pinger.test_ping()

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    def test_latency_is_real_number(self):
        """``time.perf_counter`` returns fractional seconds, we must convert it to milliseconds."""

        def mocked_read_buffer():
            time.sleep(0.001)
            return mock.DEFAULT

        with mock.patch.object(Connection, "read_buffer") as mocked:
            mocked.side_effect = mocked_read_buffer
            mocked.return_value.read_varint.return_value = 0
            mocked.return_value.read_utf.return_value = """
            {
                "description": "A Minecraft Server",
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44}
            }
            """
            pinger = ServerPinger(
                Connection(),  # type: ignore[arg-type]
                address=Address("localhost", 25565),
                version=44,
            )

            pinger.connection.receive(
                bytearray.fromhex(
                    "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A"
                    "7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531"
                    "222C2270726F746F636F6C223A34347D7D"
                )
            )
            # we slept 1ms, so this should be always ~1.
            assert pinger.read_status().latency >= 1

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    def test_test_ping_is_in_milliseconds(self):
        """``time.perf_counter`` returns fractional seconds, we must convert it to milliseconds."""

        def mocked_read_buffer():
            time.sleep(0.001)
            return mock.DEFAULT

        with mock.patch.object(Connection, "read_buffer") as mocked:
            mocked.side_effect = mocked_read_buffer
            mocked.return_value.read_varint.return_value = 1
            mocked.return_value.read_long.return_value = 123456789
            pinger = ServerPinger(
                Connection(),  # type: ignore[arg-type]
                address=Address("localhost", 25565),
                version=44,
                ping_token=123456789,
            )

            pinger.connection.receive(
                bytearray.fromhex(
                    "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A"
                    "7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531"
                    "222C2270726F746F636F6C223A34347D7D"
                )
            )
            # we slept 1ms, so this should be always ~1.
            assert pinger.test_ping() >= 1
