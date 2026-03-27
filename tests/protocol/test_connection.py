from unittest.mock import Mock, patch

import pytest

from mcstatus._net.address import Address
from mcstatus._protocol.io.base_io import StructFormat
from mcstatus._protocol.io.buffer import Buffer
from mcstatus._protocol.io.connection import TCPSocketConnection, UDPSocketConnection


class TestBuffer:
    def setup_method(self):
        self.connection = Buffer()

    def test_flush(self):
        self.connection.write(bytearray.fromhex("7FAABB"))

        assert self.connection.flush() == bytearray.fromhex("7FAABB")
        assert self.connection == bytearray()

    def test_remaining(self):
        self.connection.write(bytearray.fromhex("7FAABB"))

        assert self.connection.remaining == 3

    def test_reset(self):
        self.connection.write(b"abcdef")

        assert self.connection.read(3) == b"abc"
        self.connection.reset()
        assert self.connection.read(6) == b"abcdef"

    def test_clear_only_already_read(self):
        self.connection.write(b"abcdef")
        assert self.connection.read(2) == b"ab"

        self.connection.clear(only_already_read=True)

        assert self.connection == bytearray(b"cdef")
        assert self.connection.remaining == 4

    def test_unread_view(self):
        self.connection.write(b"abcdef")
        assert self.connection.read(2) == b"ab"

        assert bytes(self.connection.unread_view()) == b"cdef"

    def test_flush_only_returns_unread_data(self):
        self.connection.write(b"abcdef")
        assert self.connection.read(2) == b"ab"

        assert self.connection.flush() == b"cdef"
        assert self.connection == bytearray()

    def test_send(self):
        self.connection.write(bytearray.fromhex("7F"))
        self.connection.write(bytearray.fromhex("AABB"))

        assert self.connection.flush() == bytearray.fromhex("7FAABB")

    def test_read(self):
        self.connection.write(bytearray.fromhex("7FAABB"))

        assert self.connection.read(2) == bytearray.fromhex("7FAA")
        assert self.connection.read(1) == bytearray.fromhex("BB")

    def _assert_varint_read_write(self, hexstr, value) -> None:
        self.connection.write(bytearray.fromhex(hexstr))
        assert self.connection.read_varint() == value

        self.connection.write_varint(value)
        assert self.connection.flush() == bytearray.fromhex(hexstr)

    def test_varint_cases(self):
        self._assert_varint_read_write("00", 0)
        self._assert_varint_read_write("01", 1)
        self._assert_varint_read_write("0F", 15)
        self._assert_varint_read_write("FFFFFFFF07", 2147483647)

        self._assert_varint_read_write("FFFFFFFF0F", -1)
        self._assert_varint_read_write("8080808008", -2147483648)

    def test_read_invalid_varint(self):
        self.connection.write(bytearray.fromhex("FFFFFFFF10"))

        with pytest.raises(IOError, match=r"^Received varint was outside the range of 32-bit int.$"):
            self.connection.read_varint()

    def test_write_invalid_varint(self):
        with pytest.raises(
            ValueError,
            match=r"^Can't convert number 2147483648 into 32-bit twos complement format - out of range$",
        ):
            self.connection.write_varint(2147483648)
        with pytest.raises(
            ValueError,
            match=r"^Can't convert number -2147483649 into 32-bit twos complement format - out of range$",
        ):
            self.connection.write_varint(-2147483649)

    def test_read_utf(self):
        self.connection.write(bytearray.fromhex("0D48656C6C6F2C20776F726C6421"))

        assert self.connection.read_utf() == "Hello, world!"

    def test_write_utf(self):
        self.connection.write_utf("Hello, world!")

        assert self.connection.flush() == bytearray.fromhex("0D48656C6C6F2C20776F726C6421")

    def test_read_empty_utf(self):
        self.connection.write_utf("")

        assert self.connection.flush() == bytearray.fromhex("00")

    def test_read_ascii(self):
        self.connection.write(bytearray.fromhex("48656C6C6F2C20776F726C642100"))

        assert self.connection.read_ascii() == "Hello, world!"

    def test_write_ascii(self):
        self.connection.write_ascii("Hello, world!")

        assert self.connection.flush() == bytearray.fromhex("48656C6C6F2C20776F726C642100")

    def test_read_empty_ascii(self):
        self.connection.write_ascii("")

        assert self.connection.flush() == bytearray.fromhex("00")

    def test_read_short_negative(self):
        self.connection.write(bytearray.fromhex("8000"))

        assert self.connection.read_value(StructFormat.SHORT) == -32768

    def test_write_short_negative(self):
        self.connection.write_value(StructFormat.SHORT, -32768)

        assert self.connection.flush() == bytearray.fromhex("8000")

    def test_read_short_positive(self):
        self.connection.write(bytearray.fromhex("7FFF"))

        assert self.connection.read_value(StructFormat.SHORT) == 32767

    def test_write_short_positive(self):
        self.connection.write_value(StructFormat.SHORT, 32767)

        assert self.connection.flush() == bytearray.fromhex("7FFF")

    def test_read_ushort_positive(self):
        self.connection.write(bytearray.fromhex("8000"))

        assert self.connection.read_value(StructFormat.USHORT) == 32768

    def test_write_ushort_positive(self):
        self.connection.write_value(StructFormat.USHORT, 32768)

        assert self.connection.flush() == bytearray.fromhex("8000")

    def test_read_int_negative(self):
        self.connection.write(bytearray.fromhex("80000000"))

        assert self.connection.read_value(StructFormat.INT) == -2147483648

    def test_write_int_negative(self):
        self.connection.write_value(StructFormat.INT, -2147483648)

        assert self.connection.flush() == bytearray.fromhex("80000000")

    def test_read_int_positive(self):
        self.connection.write(bytearray.fromhex("7FFFFFFF"))

        assert self.connection.read_value(StructFormat.INT) == 2147483647

    def test_write_int_positive(self):
        self.connection.write_value(StructFormat.INT, 2147483647)

        assert self.connection.flush() == bytearray.fromhex("7FFFFFFF")

    def test_read_uint_positive(self):
        self.connection.write(bytearray.fromhex("80000000"))

        assert self.connection.read_value(StructFormat.UINT) == 2147483648

    def test_write_uint_positive(self):
        self.connection.write_value(StructFormat.UINT, 2147483648)

        assert self.connection.flush() == bytearray.fromhex("80000000")

    def test_read_long_negative(self):
        self.connection.write(bytearray.fromhex("8000000000000000"))

        assert self.connection.read_value(StructFormat.LONGLONG) == -9223372036854775808

    def test_write_long_negative(self):
        self.connection.write_value(StructFormat.LONGLONG, -9223372036854775808)

        assert self.connection.flush() == bytearray.fromhex("8000000000000000")

    def test_read_long_positive(self):
        self.connection.write(bytearray.fromhex("7FFFFFFFFFFFFFFF"))

        assert self.connection.read_value(StructFormat.LONGLONG) == 9223372036854775807

    def test_write_long_positive(self):
        self.connection.write_value(StructFormat.LONGLONG, 9223372036854775807)

        assert self.connection.flush() == bytearray.fromhex("7FFFFFFFFFFFFFFF")

    def test_read_ulong_positive(self):
        self.connection.write(bytearray.fromhex("8000000000000000"))

        assert self.connection.read_value(StructFormat.ULONGLONG) == 9223372036854775808

    def test_write_ulong_positive(self):
        self.connection.write_value(StructFormat.ULONGLONG, 9223372036854775808)

        assert self.connection.flush() == bytearray.fromhex("8000000000000000")

    @pytest.mark.parametrize(("as_bytes", "as_bool"), [("01", True), ("00", False)])
    def test_read_bool(self, as_bytes: str, as_bool: bool) -> None:
        self.connection.write(bytearray.fromhex(as_bytes))

        assert self.connection.read_value(StructFormat.BOOL) is as_bool

    @pytest.mark.parametrize(("as_bytes", "as_bool"), [("01", True), ("00", False)])
    def test_write_bool(self, as_bytes: str, as_bool: bool) -> None:
        self.connection.write_value(StructFormat.BOOL, as_bool)

        assert self.connection.flush() == bytearray.fromhex(as_bytes)

    def test_read_bytearray(self):
        self.connection.write(bytearray.fromhex("027FAA"))

        assert self.connection.read_bytearray() == bytearray.fromhex("7FAA")

    def test_write_bytearray(self):
        self.connection.write_bytearray(bytearray.fromhex("7FAA"))

        assert self.connection.flush() == bytearray.fromhex("027FAA")

    def test_read_empty(self):
        with pytest.raises(
            IOError,
            match=r"^Requested to read more data than available. Read 0 bytes: bytearray\(b''\), out of 1 requested bytes.$",
        ):
            self.connection.read(1)

    def test_read_not_enough(self):
        self.connection.write(bytearray(b"a"))

        with pytest.raises(
            IOError,
            match=r"^Requested to read more data than available. Read 1 bytes: bytearray\(b'a'\), out of 2 requested bytes.$",
        ):
            self.connection.read(2)

    def test_read_negative_length(self):
        with pytest.raises(IOError, match=r"^Requested to read a negative amount of data: -1\.$"):
            self.connection.read(-1)


class TestTCPSocketConnection:
    @pytest.fixture(scope="class")
    def connection(self):
        test_addr = Address("localhost", 1234)

        socket = Mock()
        socket.recv = Mock()
        socket.sendall = Mock()
        with patch("socket.create_connection") as create_connection:
            create_connection.return_value = socket
            with TCPSocketConnection(test_addr) as connection:
                yield connection

    def test_read(self, connection):
        connection.socket.recv.return_value = bytearray.fromhex("7FAA")

        assert connection.read(2) == bytearray.fromhex("7FAA")

    def test_read_empty(self, connection):
        connection.socket.recv.return_value = bytearray()

        with pytest.raises(IOError, match=r"^Server did not respond with any information!$"):
            connection.read(1)

    def test_read_not_enough(self, connection):
        connection.socket.recv.side_effect = [bytearray(b"a"), bytearray()]

        with pytest.raises(IOError, match=r"^Server did not respond with any information!$"):
            connection.read(2)

    def test_write(self, connection):
        connection.write(bytearray.fromhex("7FAA"))

        connection.socket.sendall.assert_called_once_with(bytearray.fromhex("7FAA"))


class TestUDPSocketConnection:
    @pytest.fixture(scope="class")
    def connection(self):
        test_addr = Address("127.0.0.1", 1234)

        socket = Mock()
        socket.recvfrom = Mock()
        socket.sendto = Mock()
        with patch("socket.socket") as create_socket:
            create_socket.return_value = socket
            with UDPSocketConnection(test_addr) as connection:
                yield connection

    def test_remaining(self, connection):
        assert connection.remaining == 65535

    def test_read(self, connection):
        connection.socket.recvfrom.return_value = [bytearray.fromhex("7FAA")]

        assert connection.read(2) == bytearray.fromhex("7FAA")

    def test_read_empty(self, connection):
        connection.socket.recvfrom.return_value = []

        with pytest.raises(IndexError, match=r"^list index out of range$"):
            connection.read(1)

    def test_write(self, connection):
        connection.write(bytearray.fromhex("7FAA"))

        connection.socket.sendto.assert_called_once_with(
            bytearray.fromhex("7FAA"),
            Address("127.0.0.1", 1234),
        )
