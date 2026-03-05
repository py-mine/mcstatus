from __future__ import annotations

import struct
from abc import ABC, abstractmethod
from enum import Enum
from itertools import count
from typing import Literal, TYPE_CHECKING, TypeAlias, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

__all__ = [
    "FLOAT_FORMATS_TYPE",
    "INT_FORMATS_TYPE",
    "BaseAsyncReader",
    "BaseAsyncWriter",
    "BaseSyncReader",
    "BaseSyncWriter",
    "StructFormat",
]

T = TypeVar("T")
R = TypeVar("R")

# region: Utils


def to_twos_complement(number: int, bits: int) -> int:
    """Convert a given ``number`` into two's complement format with the specified number of ``bits``.

    :param number: The signed integer to convert.
    :param bits: Number of bits used for the two's complement representation.
    :return: The integer encoded in two's complement form within the given bit width.
    :raises ValueError:
        If given ``number`` is out of range, and can't be converted into twos complement format,
        since it wouldn't fit into the given amount of ``bits``.
    """
    value_max = 1 << (bits - 1)
    value_min = value_max * -1
    # With two's complement, we have one more negative number than positive
    # this means we can't be exactly at value_max, but we can be at exactly value_min
    if number >= value_max or number < value_min:
        raise ValueError(f"Can't convert number {number} into {bits}-bit twos complement format - out of range")

    return number + (1 << bits) if number < 0 else number


def from_twos_complement(number: int, bits: int) -> int:
    """Convert a ``number`` from a two's complement representation with the specified number of ``bits``.

    :param number: The integer encoded in two's complement form.
    :param bits: Number of bits used for the two's complement representation.
    :return: The decoded signed integer.
    :raises ValueError:
        If given ``number`` doesn't fit into given amount of ``bits``. This likely means that you're
        using the wrong number, or that the number was converted into twos complement with higher
        amount of `bits`.
    """
    value_max = (1 << bits) - 1
    if number < 0 or number > value_max:
        raise ValueError(f"Can't convert number {number} from {bits}-bit twos complement format - out of range")

    if number & (1 << (bits - 1)) != 0:
        number -= 1 << bits

    return number


# endregion


# region: Format types


class StructFormat(str, Enum):
    """All possible struct format types used for reading and writing binary data.

    These values correspond directly to format characters accepted by the
    :mod:`struct` module.
    """

    BOOL = "?"
    CHAR = "c"
    BYTE = "b"
    UBYTE = "B"
    SHORT = "h"
    USHORT = "H"
    INT = "i"
    UINT = "I"
    LONG = "l"
    ULONG = "L"
    FLOAT = "f"
    DOUBLE = "d"
    HALFFLOAT = "e"
    LONGLONG = "q"
    ULONGLONG = "Q"


INT_FORMATS_TYPE: TypeAlias = Literal[
    StructFormat.BYTE,
    StructFormat.UBYTE,
    StructFormat.SHORT,
    StructFormat.USHORT,
    StructFormat.INT,
    StructFormat.UINT,
    StructFormat.LONG,
    StructFormat.ULONG,
    StructFormat.LONGLONG,
    StructFormat.ULONGLONG,
]

FLOAT_FORMATS_TYPE: TypeAlias = Literal[
    StructFormat.FLOAT,
    StructFormat.DOUBLE,
    StructFormat.HALFFLOAT,
]

# endregion

# region: Writer classes


class BaseAsyncWriter(ABC):
    """Base class holding asynchronous write buffer/connection interactions."""

    __slots__ = ()

    @abstractmethod
    async def write(self, data: bytes | bytearray, /) -> None:
        """Underlying write method, sending/storing the data.

        All of the writer functions will eventually call this method.
        """

    @overload
    async def write_value(self, fmt: INT_FORMATS_TYPE, value: int, /) -> None: ...

    @overload
    async def write_value(self, fmt: FLOAT_FORMATS_TYPE, value: float, /) -> None: ...

    @overload
    async def write_value(self, fmt: Literal[StructFormat.BOOL], value: bool, /) -> None: ...  # noqa: FBT001

    @overload
    async def write_value(self, fmt: Literal[StructFormat.CHAR], value: str, /) -> None: ...

    async def write_value(self, fmt: StructFormat, value: object, /) -> None:
        """Write a given ``value`` as given struct format (``fmt``) in big-endian mode."""
        await self.write(struct.pack(">" + fmt.value, value))

    async def _write_varuint(self, value: int, /, *, max_bits: int | None = None) -> None:
        """Write an arbitrarily large unsigned integer using a variable-length encoding.

        This is a standard way of transmitting integers with variable length over the network, allowing
        smaller numbers take up fewer bytes.

        Writing is limited to integers representable within ``max_bits`` bits. Attempting to write a larger
        value will raise :class:`ValueError`. Note that limiting the value to e.g. 32 bits does not mean
        that at most 4 bytes will be written. Due to the encoding overhead, values within 32 bits may require
        up to 5 bytes.

        Varints encode integers using groups of 7 bits. The 7 least significant bits of each byte store data,
        while the most significant bit acts as a continuation flag. If this bit is set (``1``), another byte
        follows.

        The least significant group is written first, followed by increasingly significant groups, making the
        encoding little-endian in 7-bit groups.

        :param value: Unsigned integer to encode.
        :param max_bits: Maximum allowed bit width for the encoded value.
        :raises ValueError: If ``value`` is negative or exceeds the allowed bit width.
        """
        value_max = (1 << (max_bits)) - 1 if max_bits is not None else float("inf")
        if value < 0 or value > value_max:
            raise ValueError(f"Tried to write varint outside of the range of {max_bits}-bit int.")

        remaining = value
        while True:
            if remaining & ~0x7F == 0:  # final byte
                await self.write_value(StructFormat.UBYTE, remaining)
                return
            # Write only 7 least significant bits with the first bit being 1, marking there will be another byte
            await self.write_value(StructFormat.UBYTE, remaining & 0x7F | 0x80)
            # Subtract the value we've already sent (7 least significant bits)
            remaining >>= 7

    async def write_varint(self, value: int, /) -> None:
        """Write a 32-bit signed integer using a variable-length encoding.

        The value is first converted to a 32-bit two's complement representation
        and then encoded using the varint format.

        See :meth:`_write_varuint` for details about the encoding.

        :param value: Signed integer to encode.
        """
        val = to_twos_complement(value, bits=32)
        await self._write_varuint(val, max_bits=32)

    async def write_varlong(self, value: int, /) -> None:
        """Write a 64-bit signed integer using a variable-length encoding.

        The value is first converted to a 64-bit two's complement representation
        and then encoded using the varint format.

        See :meth:`_write_varuint` for details about the encoding.

        :param value: Signed integer to encode.
        """
        val = to_twos_complement(value, bits=64)
        await self._write_varuint(val, max_bits=64)

    async def write_bytearray(self, data: bytes | bytearray, /) -> None:
        """Write an arbitrary sequence of bytes, prefixed with a varint of its size."""
        await self.write_varint(len(data))
        await self.write(data)

    async def write_ascii(self, value: str, /) -> None:
        """Write ISO-8859-1 encoded string, with NULL (0x00) at the end to indicate string end."""
        data = bytes(value, "ISO-8859-1")
        await self.write(data)
        await self.write(bytes([0]))

    async def write_utf(self, value: str, /) -> None:
        """Write a UTF-8 encoded string prefixed with its byte length as a varint.

        The maximum number of characters allowed is ``32767``.

        Individual UTF-8 characters can take up to 4 bytes, however most of the common ones take up less. Assuming the
        worst case of 4 bytes per every character, at most 131068 data bytes will be written + 3 additional bytes from
        the varint encoding overhead.

        :param value: String to encode.
        :raises ValueError: If the string exceeds the maximum allowed length.
        """
        if len(value) > 32767:
            raise ValueError("Maximum character limit for writing strings is 32767 characters.")

        data = bytes(value, "utf-8")
        await self.write_varint(len(data))
        await self.write(data)

    async def write_optional(self, value: T | None, /, writer: Callable[[T], Awaitable[R]]) -> R | None:
        """Write a bool indicating whether ``value`` is present and, if so, serialize the value using ``writer``.

        * If ``value`` is ``None``, ``False`` is written and ``None`` is returned.
        * If ``value`` is not ``None``, ``True`` is written and ``writer`` is called
        with the value. The return value of ``writer`` is then forwarded.

        :param value: Optional value to serialize.
        :param writer: Callable used to serialize the value when it is present.
        :return: ``None`` if the value is absent, otherwise the result of ``writer``.
        """
        if value is None:
            await self.write_value(StructFormat.BOOL, False)  # noqa: FBT003
            return None

        await self.write_value(StructFormat.BOOL, True)  # noqa: FBT003
        return await writer(value)


class BaseSyncWriter(ABC):
    """Base class holding synchronous write buffer/connection interactions."""

    __slots__ = ()

    @abstractmethod
    def write(self, data: bytes | bytearray, /) -> None:
        """Underlying write method, sending/storing the data.

        All of the writer functions will eventually call this method.
        """

    @overload
    def write_value(self, fmt: INT_FORMATS_TYPE, value: int, /) -> None: ...

    @overload
    def write_value(self, fmt: FLOAT_FORMATS_TYPE, value: float, /) -> None: ...

    @overload
    def write_value(self, fmt: Literal[StructFormat.BOOL], value: bool, /) -> None: ...  # noqa: FBT001

    @overload
    def write_value(self, fmt: Literal[StructFormat.CHAR], value: str, /) -> None: ...

    def write_value(self, fmt: StructFormat, value: object, /) -> None:
        """Write a given ``value`` as given struct format (``fmt``) in big-endian mode."""
        self.write(struct.pack(">" + fmt.value, value))

    def _write_varuint(self, value: int, /, *, max_bits: int | None = None) -> None:
        """Write an arbitrarily large unsigned integer using a variable-length encoding.

        This is a standard way of transmitting integers with variable length over the network, allowing
        smaller numbers take up fewer bytes.

        Writing is limited to integers representable within ``max_bits`` bits. Attempting to write a larger
        value will raise :class:`ValueError`. Note that limiting the value to e.g. 32 bits does not mean
        that at most 4 bytes will be written. Due to the encoding overhead, values within 32 bits may require
        up to 5 bytes.

        Varints encode integers using groups of 7 bits. The 7 least significant bits of each byte store data,
        while the most significant bit acts as a continuation flag. If this bit is set (``1``), another byte
        follows.

        The least significant group is written first, followed by increasingly significant groups, making the
        encoding little-endian in 7-bit groups.

        :param value: Unsigned integer to encode.
        :param max_bits: Maximum allowed bit width for the encoded value.
        :raises ValueError: If ``value`` is negative or exceeds the allowed bit width.
        """
        value_max = (1 << (max_bits)) - 1 if max_bits is not None else float("inf")
        if value < 0 or value > value_max:
            raise ValueError(f"Tried to write varint outside of the range of {max_bits}-bit int.")

        remaining = value
        while True:
            if remaining & ~0x7F == 0:  # final byte
                self.write_value(StructFormat.UBYTE, remaining)
                return
            # Write only 7 least significant bits with the first bit being 1, marking there will be another byte
            self.write_value(StructFormat.UBYTE, remaining & 0x7F | 0x80)
            # Subtract the value we've already sent (7 least significant bits)
            remaining >>= 7

    def write_varint(self, value: int, /) -> None:
        """Write a 32-bit signed integer using a variable-length encoding.

        The value is first converted to a 32-bit two's complement representation
        and then encoded using the varint format.

        See :meth:`_write_varuint` for details about the encoding.

        :param value: Signed integer to encode.
        """
        val = to_twos_complement(value, bits=32)
        self._write_varuint(val, max_bits=32)

    def write_varlong(self, value: int, /) -> None:
        """Write a 64-bit signed integer using a variable-length encoding.

        The value is first converted to a 64-bit two's complement representation
        and then encoded using the varint format.

        See :meth:`_write_varuint` for details about the encoding.

        :param value: Signed integer to encode.
        """
        val = to_twos_complement(value, bits=64)
        self._write_varuint(val, max_bits=64)

    def write_bytearray(self, data: bytes | bytearray, /) -> None:
        """Write an arbitrary sequence of bytes, prefixed with a varint of its size."""
        self.write_varint(len(data))
        self.write(data)

    def write_ascii(self, value: str, /) -> None:
        """Write ISO-8859-1 encoded string, with NULL (0x00) at the end to indicate string end."""
        data = bytes(value, "ISO-8859-1")
        self.write(data)
        self.write(bytes([0]))

    def write_utf(self, value: str, /) -> None:
        """Write a UTF-8 encoded string prefixed with its byte length as a varint.

        The maximum number of characters allowed is ``32767``.

        Individual UTF-8 characters can take up to 4 bytes, however most of the common ones take up less. Assuming the
        worst case of 4 bytes per every character, at most 131068 data bytes will be written + 3 additional bytes from
        the varint encoding overhead.

        :param value: String to encode.
        :raises ValueError: If the string exceeds the maximum allowed length.
        """
        if len(value) > 32767:
            raise ValueError("Maximum character limit for writing strings is 32767 characters.")

        data = bytes(value, "utf-8")
        self.write_varint(len(data))
        self.write(data)

    def write_optional(self, value: T | None, /, writer: Callable[[T], R]) -> R | None:
        """Write a bool indicating whether ``value`` is present and, if so, serialize the value using ``writer``.

        * If ``value`` is ``None``, ``False`` is written and ``None`` is returned.
        * If ``value`` is not ``None``, ``True`` is written and ``writer`` is called
        with the value. The return value of ``writer`` is then forwarded.

        :param value: Optional value to serialize.
        :param writer: Callable used to serialize the value when it is present.
        :return: ``None`` if the value is absent, otherwise the result of ``writer``.
        """
        if value is None:
            self.write_value(StructFormat.BOOL, False)  # noqa: FBT003
            return None

        self.write_value(StructFormat.BOOL, True)  # noqa: FBT003
        return writer(value)


# endregion
# region: Reader classes


class BaseAsyncReader(ABC):
    """Base class holding asynchronous read buffer/connection interactions."""

    __slots__ = ()

    @abstractmethod
    async def read(self, length: int, /) -> bytes:
        """Underlying read method, obtaining the raw data.

        All of the reader functions will eventually call this method.
        """

    @overload
    async def read_value(self, fmt: INT_FORMATS_TYPE, /) -> int: ...

    @overload
    async def read_value(self, fmt: FLOAT_FORMATS_TYPE, /) -> float: ...

    @overload
    async def read_value(self, fmt: Literal[StructFormat.BOOL], /) -> bool: ...

    @overload
    async def read_value(self, fmt: Literal[StructFormat.CHAR], /) -> str: ...

    async def read_value(self, fmt: StructFormat, /) -> object:
        """Read a value as given struct format (``fmt``) in big-endian mode.

        The amount of bytes to read will be determined based on the struct format automatically.
        """
        length = struct.calcsize(fmt.value)
        data = await self.read(length)
        unpacked = struct.unpack(">" + fmt.value, data)
        return unpacked[0]

    async def _read_varuint(self, *, max_bits: int | None = None) -> int:
        """Read an arbitrarily large unsigned integer using a variable-length encoding.

        This is a standard way of transmitting integers with variable length over the network,
        allowing smaller numbers to take fewer bytes.

        Reading is limited to integers representable within ``max_bits`` bits. Attempting to read
        a larger value will raise :class:`OSError`. Note that limiting the value to e.g. 32 bits
        does not mean that at most 4 bytes will be read. Due to the encoding overhead, values
        within 32 bits may require up to 5 bytes.

        Varints encode integers using groups of 7 bits. The 7 least significant bits of each byte
        store data, while the most significant bit acts as a continuation flag. If this bit is set
        (``1``), another byte follows.

        The least significant group is read first, followed by increasingly significant groups,
        making the encoding little-endian in 7-bit groups.

        :param max_bits: Maximum allowed bit width for the decoded value.
        :raises OSError: If the decoded value exceeds the allowed bit width.
        :return: The decoded unsigned integer.
        """
        value_max = (1 << (max_bits)) - 1 if max_bits is not None else float("inf")

        result = 0
        for i in count():
            byte = await self.read_value(StructFormat.UBYTE)
            # Read 7 least significant value bits in this byte, and shift them appropriately to be in the right place
            # then simply add them (OR) as additional 7 most significant bits in our result
            result |= (byte & 0x7F) << (7 * i)

            # Ensure that we stop reading and raise an error if the size gets over the maximum
            # (if the current amount of bits is higher than allowed size in bits)
            if result > value_max:
                raise OSError(f"Received varint was outside the range of {max_bits}-bit int.")

            # If the most significant bit is 0, we should stop reading
            if not byte & 0x80:
                break

        return result

    async def read_varint(self) -> int:
        """Read a 32-bit signed integer using a variable-length encoding.

        The value is read as an unsigned varint and then converted from a
        32-bit two's complement representation.

        See :meth:`_read_varuint` for details about the encoding.

        :return: Decoded signed integer.
        """
        unsigned_num = await self._read_varuint(max_bits=32)
        return from_twos_complement(unsigned_num, bits=32)

    async def read_varlong(self) -> int:
        """Read a 64-bit signed integer using a variable-length encoding.

        The value is read as an unsigned varint and then converted from a
        64-bit two's complement representation.

        See :meth:`_read_varuint` for details about the encoding.

        :return: Decoded signed integer.
        """
        unsigned_num = await self._read_varuint(max_bits=64)
        return from_twos_complement(unsigned_num, bits=64)

    async def read_bytearray(self, /) -> bytes:
        """Read a sequence of bytes prefixed with its length encoded as a varint.

        :return: The decoded byte sequence.
        """
        length = await self.read_varint()
        return await self.read(length)

    async def read_ascii(self) -> str:
        """Read ISO-8859-1 encoded string, until we encounter NULL (0x00) at the end indicating string end.

        Bytes are read until a NULL terminator is encountered. The terminator itself is not included in the
        returned string. There is no limit that can be set for how long this string can end up being.

        :return: Decoded string.
        """
        # Keep reading bytes until we find NULL
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            byte = await self.read(1)
            result.extend(byte)
        return result[:-1].decode("ISO-8859-1")

    async def read_utf(self) -> str:
        """Read a UTF-8 encoded string prefixed with its byte length as a varint.

        The maximum number of characters allowed is ``32767``.

        Individual UTF-8 characters can take up to 4 bytes, however most of the common ones take up less. Assuming the
        worst case of 4 bytes per every character, at most 131068 data bytes will be read + 3 additional bytes from
        the varint encoding overhead.

        :raises OSError:
            * If the length prefix exceeds the maximum of ``131068``, the string will not be read at all,
              and the error will be raised immediately after reading the prefix.
            * If the decoded string contains more than ``32767`` characters. In this case the data is still
              fully read because it fits within the byte limit. This behavior mirrors Minecraft's implementation.

        :return: Decoded UTF-8 string.
        """
        length = await self.read_varint()
        if length > 131068:
            raise OSError(f"Maximum read limit for utf strings is 131068 bytes, got {length}.")

        data = await self.read(length)
        chars = data.decode("utf-8")

        if len(chars) > 32767:
            raise OSError(f"Maximum read limit for utf strings is 32767 characters, got {len(chars)}.")

        return chars

    async def read_optional(self, reader: Callable[[], Awaitable[R]]) -> R | None:
        """Read a boolean indicating whether a value is present and, if so, deserialize it using ``reader``.

        * If ``False`` is read, nothing further is read and ``None`` is returned.
        * If ``True`` is read, ``reader`` is called and its return value is forwarded.

        :param reader: Callable used to read the value when it is present.
        :return: ``None`` if the value is absent, otherwise the result of ``reader``.
        """
        if not await self.read_value(StructFormat.BOOL):
            return None

        return await reader()


class BaseSyncReader(ABC):
    """Base class holding synchronous read buffer/connection interactions."""

    __slots__ = ()

    @abstractmethod
    def read(self, length: int, /) -> bytes:
        """Underlying read method, obtaining the raw data.

        All of the reader functions will eventually call this method.
        """

    @overload
    def read_value(self, fmt: INT_FORMATS_TYPE, /) -> int: ...

    @overload
    def read_value(self, fmt: FLOAT_FORMATS_TYPE, /) -> float: ...

    @overload
    def read_value(self, fmt: Literal[StructFormat.BOOL], /) -> bool: ...

    @overload
    def read_value(self, fmt: Literal[StructFormat.CHAR], /) -> str: ...

    def read_value(self, fmt: StructFormat, /) -> object:
        """Read a value as given struct format (``fmt``) in big-endian mode.

        The amount of bytes to read will be determined based on the struct format automatically.
        """
        length = struct.calcsize(fmt.value)
        data = self.read(length)
        unpacked = struct.unpack(">" + fmt.value, data)
        return unpacked[0]

    def _read_varuint(self, *, max_bits: int | None = None) -> int:
        """Read an arbitrarily large unsigned integer using a variable-length encoding.

        This is a standard way of transmitting integers with variable length over the network,
        allowing smaller numbers to take fewer bytes.

        Reading is limited to integers representable within ``max_bits`` bits. Attempting to read
        a larger value will raise :class:`OSError`. Note that limiting the value to e.g. 32 bits
        does not mean that at most 4 bytes will be read. Due to the encoding overhead, values
        within 32 bits may require up to 5 bytes.

        Varints encode integers using groups of 7 bits. The 7 least significant bits of each byte
        store data, while the most significant bit acts as a continuation flag. If this bit is set
        (``1``), another byte follows.

        The least significant group is read first, followed by increasingly significant groups,
        making the encoding little-endian in 7-bit groups.

        :param max_bits: Maximum allowed bit width for the decoded value.
        :raises OSError: If the decoded value exceeds the allowed bit width.
        :return: The decoded unsigned integer.
        """
        value_max = (1 << (max_bits)) - 1 if max_bits is not None else float("inf")

        result = 0
        for i in count():
            byte = self.read_value(StructFormat.UBYTE)
            # Read 7 least significant value bits in this byte, and shift them appropriately to be in the right place
            # then simply add them (OR) as additional 7 most significant bits in our result
            result |= (byte & 0x7F) << (7 * i)

            # Ensure that we stop reading and raise an error if the size gets over the maximum
            # (if the current amount of bits is higher than allowed size in bits)
            if result > value_max:
                raise OSError(f"Received varint was outside the range of {max_bits}-bit int.")

            # If the most significant bit is 0, we should stop reading
            if not byte & 0x80:
                break

        return result

    def read_varint(self) -> int:
        """Read a 32-bit signed integer using a variable-length encoding.

        The value is read as an unsigned varint and then converted from a
        32-bit two's complement representation.

        See :meth:`_read_varuint` for details about the encoding.

        :return: Decoded signed integer.
        """
        unsigned_num = self._read_varuint(max_bits=32)
        return from_twos_complement(unsigned_num, bits=32)

    def read_varlong(self) -> int:
        """Read a 64-bit signed integer using a variable-length encoding.

        The value is read as an unsigned varint and then converted from a
        64-bit two's complement representation.

        See :meth:`_read_varuint` for details about the encoding.

        :return: Decoded signed integer.
        """
        unsigned_num = self._read_varuint(max_bits=64)
        return from_twos_complement(unsigned_num, bits=64)

    def read_bytearray(self) -> bytes:
        """Read a sequence of bytes prefixed with its length encoded as a varint.

        :return: The decoded byte sequence.
        """
        length = self.read_varint()
        return self.read(length)

    def read_ascii(self) -> str:
        """Read ISO-8859-1 encoded string, until we encounter NULL (0x00) at the end indicating string end.

        Bytes are read until a NULL terminator is encountered. The terminator itself is not included in the
        returned string. There is no limit that can be set for how long this string can end up being.

        :return: Decoded string.
        """
        # Keep reading bytes until we find NULL
        result = bytearray()
        while len(result) == 0 or result[-1] != 0:
            byte = self.read(1)
            result.extend(byte)
        return result[:-1].decode("ISO-8859-1")

    def read_utf(self) -> str:
        """Read a UTF-8 encoded string prefixed with its byte length as a varint.

        The maximum number of characters allowed is ``32767``.

        Individual UTF-8 characters can take up to 4 bytes, however most of the common ones take up less. Assuming the
        worst case of 4 bytes per every character, at most 131068 data bytes will be read + 3 additional bytes from
        the varint encoding overhead.

        :raises OSError:
            * If the length prefix exceeds the maximum of ``131068``, the string will not be read at all,
              and the error will be raised immediately after reading the prefix.
            * If the decoded string contains more than ``32767`` characters. In this case the data is still
              fully read because it fits within the byte limit. This behavior mirrors Minecraft's implementation.

        :return: Decoded UTF-8 string.
        """
        length = self.read_varint()
        if length > 131068:
            raise OSError(f"Maximum read limit for utf strings is 131068 bytes, got {length}.")

        data = self.read(length)
        chars = data.decode("utf-8")

        if len(chars) > 32767:
            raise OSError(f"Maximum read limit for utf strings is 32767 characters, got {len(chars)}.")

        return chars

    def read_optional(self, reader: Callable[[], R]) -> R | None:
        """Read a boolean indicating whether a value is present and, if so, deserialize it using ``reader``.

        * If ``False`` is read, nothing further is read and ``None`` is returned.
        * If ``True`` is read, ``reader`` is called and its return value is forwarded.

        :param reader: Callable used to read the value when it is present.
        :return: ``None`` if the value is absent, otherwise the result of ``reader``.
        """
        if not self.read_value(StructFormat.BOOL):
            return None

        return reader()


# endregion
