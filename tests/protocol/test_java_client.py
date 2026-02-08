import sys
import time
from unittest import mock

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.connection import Connection
from mcstatus._protocol.java_client import JavaClient


class TestJavaClient:
    def setup_method(self):
        self.java_client = JavaClient(
            Connection(),  # pyright: ignore[reportArgumentType]
            address=Address("localhost", 25565),
            version=44,
        )

    def test_handshake(self):
        self.java_client.handshake()

        assert self.java_client.connection.flush() == bytearray.fromhex("0F002C096C6F63616C686F737463DD01")

    def test_read_status(self):
        self.java_client.connection.receive(
            bytearray.fromhex(
                "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A7B2"
                "26D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531222C22"
                "70726F746F636F6C223A34347D7D"
            )
        )
        status = self.java_client.read_status()

        assert status.raw == {
            "description": "A Minecraft Server",
            "players": {"max": 20, "online": 0},
            "version": {"name": "1.8-pre1", "protocol": 44},
        }
        assert self.java_client.connection.flush() == bytearray.fromhex("0100")

    def test_read_status_invalid_json(self):
        self.java_client.connection.receive(bytearray.fromhex("0300017B"))
        with pytest.raises(IOError, match=r"^Received invalid JSON$"):
            self.java_client.read_status()

    def test_read_status_invalid_reply(self):
        self.java_client.connection.receive(
            # no motd, see also #922
            bytearray.fromhex(
                "4F004D7B22706C6179657273223A7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616"
                "D65223A22312E382D70726531222C2270726F746F636F6C223A34347D7D"
            )
        )

        self.java_client.read_status()

    def test_read_status_invalid_status(self):
        self.java_client.connection.receive(bytearray.fromhex("0105"))

        with pytest.raises(IOError, match=r"^Received invalid status response packet.$"):
            self.java_client.read_status()

    def test_test_ping(self):
        self.java_client.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.java_client.ping_token = 14515484

        assert self.java_client.test_ping() >= 0
        assert self.java_client.connection.flush() == bytearray.fromhex("09010000000000DD7D1C")

    def test_test_ping_invalid(self):
        self.java_client.connection.receive(bytearray.fromhex("011F"))
        self.java_client.ping_token = 14515484

        with pytest.raises(IOError, match=r"^Received invalid ping response packet.$"):
            self.java_client.test_ping()

    def test_test_ping_wrong_token(self):
        self.java_client.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.java_client.ping_token = 12345

        with pytest.raises(IOError, match=r"^Received mangled ping response \(expected token 12345, got 14515484\)$"):
            self.java_client.test_ping()

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
            java_client = JavaClient(
                Connection(),  # pyright: ignore[reportArgumentType]
                address=Address("localhost", 25565),
                version=44,
            )

            java_client.connection.receive(
                bytearray.fromhex(
                    "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A"
                    "7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531"
                    "222C2270726F746F636F6C223A34347D7D"
                )
            )
            # we slept 1ms, so this should be always ~1.
            assert java_client.read_status().latency >= 1

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
            java_client = JavaClient(
                Connection(),  # pyright: ignore[reportArgumentType]
                address=Address("localhost", 25565),
                version=44,
                ping_token=123456789,
            )

            java_client.connection.receive(
                bytearray.fromhex(
                    "7200707B226465736372697074696F6E223A2241204D696E65637261667420536572766572222C22706C6179657273223A"
                    "7B226D6178223A32302C226F6E6C696E65223A307D2C2276657273696F6E223A7B226E616D65223A22312E382D70726531"
                    "222C2270726F746F636F6C223A34347D7D"
                )
            )
            # we slept 1ms, so this should be always ~1.
            assert java_client.test_ping() >= 1
