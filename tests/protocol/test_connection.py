from unittest.mock import Mock, patch

import pytest

from mcstatus.address import Address
from mcstatus.protocol.connection import Connection, TCPSocketConnection, UDPSocketConnection


class TestConnection:
    connection: Connection

    def setup_method(self):
        self.connection = Connection()

    def test_flush(self):
        self.connection.sent = bytearray.fromhex("7FAABB")

        assert self.connection.flush() == bytearray.fromhex("7FAABB")
        assert self.connection.sent == bytearray()

    def test_receive(self):
        self.connection.receive(bytearray.fromhex("7F"))
        self.connection.receive(bytearray.fromhex("AABB"))

        assert self.connection.received == bytearray.fromhex("7FAABB")

    def test_remaining(self):
        self.connection.receive(bytearray.fromhex("7F"))
        self.connection.receive(bytearray.fromhex("AABB"))

        assert self.connection.remaining() == 3

    def test_send(self):
        self.connection.write(bytearray.fromhex("7F"))
        self.connection.write(bytearray.fromhex("AABB"))

        assert self.connection.flush() == bytearray.fromhex("7FAABB")

    def test_read(self):
        self.connection.receive(bytearray.fromhex("7FAABB"))

        assert self.connection.read(2) == bytearray.fromhex("7FAA")
        assert self.connection.read(1) == bytearray.fromhex("BB")

    def _assert_varint_read_write(self, hexstr, value) -> None:
        self.connection.receive(bytearray.fromhex(hexstr))
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
        self.connection.receive(bytearray.fromhex("FFFFFFFF80"))

        with pytest.raises(IOError):
            self.connection.read_varint()

    def test_write_invalid_varint(self):
        with pytest.raises(ValueError):
            self.connection.write_varint(2147483648)
        with pytest.raises(ValueError):
            self.connection.write_varint(-2147483649)

    def test_read_utf(self):
        self.connection.receive(bytearray.fromhex("0D48656C6C6F2C20776F726C6421"))

        assert self.connection.read_utf() == "Hello, world!"

    def test_write_utf(self):
        self.connection.write_utf("Hello, world!")

        assert self.connection.flush() == bytearray.fromhex("0D48656C6C6F2C20776F726C6421")

    def test_read_empty_utf(self):
        self.connection.write_utf("")

        assert self.connection.flush() == bytearray.fromhex("00")

    def test_read_ascii(self):
        self.connection.receive(bytearray.fromhex("48656C6C6F2C20776F726C642100"))

        assert self.connection.read_ascii() == "Hello, world!"

    def test_write_ascii(self):
        self.connection.write_ascii("Hello, world!")

        assert self.connection.flush() == bytearray.fromhex("48656C6C6F2C20776F726C642100")

    def test_read_empty_ascii(self):
        self.connection.write_ascii("")

        assert self.connection.flush() == bytearray.fromhex("00")

    def test_read_short_negative(self):
        self.connection.receive(bytearray.fromhex("8000"))

        assert self.connection.read_short() == -32768

    def test_write_short_negative(self):
        self.connection.write_short(-32768)

        assert self.connection.flush() == bytearray.fromhex("8000")

    def test_read_short_positive(self):
        self.connection.receive(bytearray.fromhex("7FFF"))

        assert self.connection.read_short() == 32767

    def test_write_short_positive(self):
        self.connection.write_short(32767)

        assert self.connection.flush() == bytearray.fromhex("7FFF")

    def test_read_ushort_positive(self):
        self.connection.receive(bytearray.fromhex("8000"))

        assert self.connection.read_ushort() == 32768

    def test_write_ushort_positive(self):
        self.connection.write_ushort(32768)

        assert self.connection.flush() == bytearray.fromhex("8000")

    def test_read_int_negative(self):
        self.connection.receive(bytearray.fromhex("80000000"))

        assert self.connection.read_int() == -2147483648

    def test_write_int_negative(self):
        self.connection.write_int(-2147483648)

        assert self.connection.flush() == bytearray.fromhex("80000000")

    def test_read_int_positive(self):
        self.connection.receive(bytearray.fromhex("7FFFFFFF"))

        assert self.connection.read_int() == 2147483647

    def test_write_int_positive(self):
        self.connection.write_int(2147483647)

        assert self.connection.flush() == bytearray.fromhex("7FFFFFFF")

    def test_read_uint_positive(self):
        self.connection.receive(bytearray.fromhex("80000000"))

        assert self.connection.read_uint() == 2147483648

    def test_write_uint_positive(self):
        self.connection.write_uint(2147483648)

        assert self.connection.flush() == bytearray.fromhex("80000000")

    def test_read_long_negative(self):
        self.connection.receive(bytearray.fromhex("8000000000000000"))

        assert self.connection.read_long() == -9223372036854775808

    def test_write_long_negative(self):
        self.connection.write_long(-9223372036854775808)

        assert self.connection.flush() == bytearray.fromhex("8000000000000000")

    def test_read_long_positive(self):
        self.connection.receive(bytearray.fromhex("7FFFFFFFFFFFFFFF"))

        assert self.connection.read_long() == 9223372036854775807

    def test_write_long_positive(self):
        self.connection.write_long(9223372036854775807)

        assert self.connection.flush() == bytearray.fromhex("7FFFFFFFFFFFFFFF")

    def test_read_ulong_positive(self):
        self.connection.receive(bytearray.fromhex("8000000000000000"))

        assert self.connection.read_ulong() == 9223372036854775808

    def test_write_ulong_positive(self):
        self.connection.write_ulong(9223372036854775808)

        assert self.connection.flush() == bytearray.fromhex("8000000000000000")

    @pytest.mark.parametrize("as_bytes,as_bool", [("01", True), ("00", False)])
    def test_read_bool(self, as_bytes: str, as_bool: bool) -> None:
        self.connection.receive(bytearray.fromhex(as_bytes))

        assert self.connection.read_bool() is as_bool

    @pytest.mark.parametrize("as_bytes,as_bool", [("01", True), ("00", False)])
    def test_write_bool(self, as_bytes: str, as_bool: bool) -> None:
        self.connection.write_bool(as_bool)

        assert self.connection.flush() == bytearray.fromhex(as_bytes)

    def test_read_buffer(self):
        self.connection.receive(bytearray.fromhex("027FAA"))
        buffer = self.connection.read_buffer()

        assert buffer.received == bytearray.fromhex("7FAA")
        assert self.connection.flush() == bytearray()

    def test_write_buffer(self):
        buffer = Connection()
        buffer.write(bytearray.fromhex("7FAA"))
        self.connection.write_buffer(buffer)

        assert self.connection.flush() == bytearray.fromhex("027FAA")

    def test_read_empty(self):
        self.connection.received = bytearray()

        with pytest.raises(IOError):
            self.connection.read(1)

    def test_read_not_enough(self):
        self.connection.received = bytearray(b"a")

        with pytest.raises(IOError):
            self.connection.read(2)


class TestTCPSocketConnection:
    @pytest.fixture(scope="class")
    def connection(self):
        test_addr = Address("localhost", 1234)

        socket = Mock()
        socket.recv = Mock()
        socket.send = Mock()
        with patch("socket.create_connection") as create_connection:
            create_connection.return_value = socket
            with TCPSocketConnection(test_addr) as connection:
                yield connection

    def test_flush(self, connection):
        with pytest.raises(TypeError):
            connection.flush()

    def test_receive(self, connection):
        with pytest.raises(TypeError):
            connection.receive("")  # type: ignore # This is desired to produce TypeError

    def test_remaining(self, connection):
        with pytest.raises(TypeError):
            connection.remaining()

    def test_read(self, connection):
        connection.socket.recv.return_value = bytearray.fromhex("7FAA")

        assert connection.read(2) == bytearray.fromhex("7FAA")

    def test_read_empty(self, connection):
        connection.socket.recv.return_value = bytearray()

        with pytest.raises(IOError):
            connection.read(1)

    def test_read_not_enough(self, connection):
        connection.socket.recv.side_effect = [bytearray(b"a"), bytearray()]

        with pytest.raises(IOError):
            connection.read(2)

    def test_write(self, connection):
        connection.write(bytearray.fromhex("7FAA"))

        connection.socket.send.assert_called_once_with(bytearray.fromhex("7FAA"))  # type: ignore[attr-defined]


class TestUDPSocketConnection:
    @pytest.fixture(scope="class")
    def connection(self):
        test_addr = Address("localhost", 1234)

        socket = Mock()
        socket.recvfrom = Mock()
        socket.sendto = Mock()
        with patch("socket.socket") as create_socket:
            create_socket.return_value = socket
            with UDPSocketConnection(test_addr) as connection:
                yield connection

    def test_flush(self, connection):
        with pytest.raises(TypeError):
            connection.flush()

    def test_receive(self, connection):
        with pytest.raises(TypeError):
            connection.receive("")  # type: ignore # This is desired to produce TypeError

    def test_remaining(self, connection):
        assert connection.remaining() == 65535

    def test_read(self, connection):
        connection.socket.recvfrom.return_value = [bytearray.fromhex("7FAA")]

        assert connection.read(2) == bytearray.fromhex("7FAA")

    def test_read_empty(self, connection):
        connection.socket.recvfrom.return_value = []

        with pytest.raises(IndexError):
            connection.read(1)

    def test_write(self, connection):
        connection.write(bytearray.fromhex("7FAA"))

        connection.socket.sendto.assert_called_once_with(  # type: ignore[attr-defined]
            bytearray.fromhex("7FAA"),
            Address("localhost", 1234),
        )
