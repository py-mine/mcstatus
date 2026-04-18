from __future__ import annotations

import struct
from inspect import isawaitable
from typing import TYPE_CHECKING, TypeVar, overload
from unittest.mock import AsyncMock, Mock

import pytest

from mcstatus._protocol.io.base_io import INT_FORMATS_TYPE, StructFormat
from mcstatus._protocol.io.buffer import Buffer
from tests.protocol.helpers import AsyncBufferConnection, SyncBufferConnection

if TYPE_CHECKING:
    from collections.abc import Awaitable

ConnectionClass = type[SyncBufferConnection] | type[AsyncBufferConnection]
T = TypeVar("T")


@pytest.fixture(
    params=[
        pytest.param(SyncBufferConnection, id="sync"),
        pytest.param(AsyncBufferConnection, id="async"),
    ]
)
def conn_cls(request: pytest.FixtureRequest) -> ConnectionClass:
    """Provide a parametrized sync/async connection class for each test."""
    return request.param


@overload
async def maybe_await(value: Awaitable[T], /) -> T: ...


@overload
async def maybe_await(value: T, /) -> T: ...


async def maybe_await(value: Awaitable[T] | T, /) -> T:
    """Return a value directly or await it when needed.

    This keeps test calls explicit and type-checkable for both sync and async IO APIs.
    """
    if isawaitable(value):
        return await value
    return value


@pytest.mark.parametrize(
    ("fmt", "value", "expected"),
    [
        pytest.param(StructFormat.UBYTE, 0, b"\x00", id="ubyte-0"),
        pytest.param(StructFormat.UBYTE, 15, b"\x0f", id="ubyte-15"),
        pytest.param(StructFormat.UBYTE, 255, b"\xff", id="ubyte-max"),
        pytest.param(StructFormat.BYTE, 0, b"\x00", id="byte-0"),
        pytest.param(StructFormat.BYTE, 15, b"\x0f", id="byte-15"),
        pytest.param(StructFormat.BYTE, 127, b"\x7f", id="byte-max"),
        pytest.param(StructFormat.BYTE, -20, b"\xec", id="byte-neg-20"),
        pytest.param(StructFormat.BYTE, -128, b"\x80", id="byte-min"),
    ],
)
@pytest.mark.asyncio
async def test_write_value_matches_reference(
    conn_cls: ConnectionClass,
    fmt: INT_FORMATS_TYPE,
    value: int,
    expected: bytes,
):
    conn = conn_cls()
    _ = await maybe_await(conn.write_value(fmt, value))
    assert conn.flush() == expected


@pytest.mark.asyncio
async def test_write_value_char_uses_single_byte(conn_cls: ConnectionClass):
    conn = conn_cls()
    _ = await maybe_await(conn.write_value(StructFormat.CHAR, b"a"))
    assert conn.flush() == b"a"


@pytest.mark.asyncio
async def test_write_value_char_rejects_non_single_byte(conn_cls: ConnectionClass):
    conn = conn_cls()
    with pytest.raises(struct.error):
        _ = await maybe_await(conn.write_value(StructFormat.CHAR, b"ab"))


@pytest.mark.parametrize(
    ("fmt", "value"),
    [
        pytest.param(StructFormat.UBYTE, -1, id="ubyte-neg"),
        pytest.param(StructFormat.UBYTE, 256, id="ubyte-overflow"),
        pytest.param(StructFormat.BYTE, -129, id="byte-underflow"),
        pytest.param(StructFormat.BYTE, 128, id="byte-overflow"),
    ],
)
@pytest.mark.asyncio
async def test_write_value_rejects_out_of_range(conn_cls: ConnectionClass, fmt: INT_FORMATS_TYPE, value: int):
    conn = conn_cls()
    with pytest.raises(struct.error):
        _ = await maybe_await(conn.write_value(fmt, value))


@pytest.mark.parametrize(
    ("encoded", "fmt", "expected"),
    [
        pytest.param(b"\x00", StructFormat.UBYTE, 0, id="ubyte-0"),
        pytest.param(b"\x0f", StructFormat.UBYTE, 15, id="ubyte-15"),
        pytest.param(b"\xff", StructFormat.UBYTE, 255, id="ubyte-max"),
        pytest.param(b"\x00", StructFormat.BYTE, 0, id="byte-0"),
        pytest.param(b"\x0f", StructFormat.BYTE, 15, id="byte-15"),
        pytest.param(b"\x7f", StructFormat.BYTE, 127, id="byte-max"),
        pytest.param(b"\xec", StructFormat.BYTE, -20, id="byte-neg-20"),
        pytest.param(b"\x80", StructFormat.BYTE, -128, id="byte-min"),
    ],
)
@pytest.mark.asyncio
async def test_read_value_matches_reference(
    conn_cls: ConnectionClass,
    encoded: bytes,
    fmt: INT_FORMATS_TYPE,
    expected: int,
):
    conn = conn_cls(encoded)
    assert await maybe_await(conn.read_value(fmt)) == expected


@pytest.mark.asyncio
async def test_read_value_char_returns_bytes(conn_cls: ConnectionClass):
    conn = conn_cls(b"a")
    value = await maybe_await(conn.read_value(StructFormat.CHAR))
    assert value == b"a"
    assert isinstance(value, bytes)


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        pytest.param(0, b"\x00", id="0"),
        pytest.param(127, b"\x7f", id="127"),
        pytest.param(128, b"\x80\x01", id="128"),
        pytest.param(255, b"\xff\x01", id="255"),
        pytest.param(1_000_000, b"\xc0\x84\x3d", id="1m"),
        pytest.param((2**31) - 1, b"\xff\xff\xff\xff\x07", id="max-32"),
    ],
)
@pytest.mark.asyncio
async def test_write_varuint_matches_reference(conn_cls: ConnectionClass, number: int, expected: bytes):
    conn = conn_cls()
    _ = await maybe_await(conn._write_varuint(number))
    assert conn.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"\x00", 0, id="0"),
        pytest.param(b"\x7f", 127, id="127"),
        pytest.param(b"\x80\x01", 128, id="128"),
        pytest.param(b"\xff\x01", 255, id="255"),
        pytest.param(b"\xc0\x84\x3d", 1_000_000, id="1m"),
        pytest.param(b"\xff\xff\xff\xff\x07", (2**31) - 1, id="max-32"),
    ],
)
@pytest.mark.asyncio
async def test_read_varuint_matches_reference(conn_cls: ConnectionClass, encoded: bytes, expected: int):
    conn = conn_cls(encoded)
    assert await maybe_await(conn._read_varuint()) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("number", "max_bits"),
    [
        (-1, 128),
        (-1, 1),
        (2**16, 16),
        (2**32, 32),
    ],
)
async def test_write_varuint_rejects_out_of_range(conn_cls: ConnectionClass, number: int, max_bits: int):
    conn = conn_cls()
    with pytest.raises(ValueError, match=r"outside of the range of"):
        _ = await maybe_await(conn._write_varuint(number, max_bits=max_bits))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("encoded", "max_bits"),
    [
        (b"\x80\x80\x04", 16),
        (b"\x80\x80\x80\x80\x10", 32),
    ],
)
async def test_read_varuint_rejects_out_of_range(conn_cls: ConnectionClass, encoded: bytes, max_bits: int):
    conn = conn_cls(encoded)
    with pytest.raises(OSError, match=r"outside the range of"):
        _ = await maybe_await(conn._read_varuint(max_bits=max_bits))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("encoded", "max_bits", "max_bytes"),
    [
        (b"\x80\x80\x80\x00", 16, 3),
        (b"\x80\x80\x80\x80\x80\x00", 32, 5),
    ],
)
async def test_read_varuint_rejects_too_many_bytes(
    conn_cls: ConnectionClass,
    encoded: bytes,
    max_bits: int,
    max_bytes: int,
):
    conn = conn_cls(encoded)
    with pytest.raises(
        OSError,
        match=rf"^Received varint had too many bytes for {max_bits}-bit int \(continuation bit set on byte {max_bytes}\)\.$",
    ):
        _ = await maybe_await(conn._read_varuint(max_bits=max_bits))


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        pytest.param(127, b"\x7f", id="127"),
        pytest.param(16_384, b"\x80\x80\x01", id="16384"),
        pytest.param(-128, b"\x80\xff\xff\xff\x0f", id="-128"),
        pytest.param(-16_383, b"\x81\x80\xff\xff\x0f", id="-16383"),
    ],
)
@pytest.mark.asyncio
async def test_write_varint_matches_reference(conn_cls: ConnectionClass, number: int, expected: bytes):
    conn = conn_cls()
    _ = await maybe_await(conn.write_varint(number))
    assert conn.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"\x7f", 127, id="127"),
        pytest.param(b"\x80\x80\x01", 16_384, id="16384"),
        pytest.param(b"\x80\xff\xff\xff\x0f", -128, id="-128"),
        pytest.param(b"\x81\x80\xff\xff\x0f", -16_383, id="-16383"),
    ],
)
@pytest.mark.asyncio
async def test_read_varint_matches_reference(conn_cls: ConnectionClass, encoded: bytes, expected: int):
    conn = conn_cls(encoded)
    assert await maybe_await(conn.read_varint()) == expected


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        pytest.param(127, b"\x7f", id="127"),
        pytest.param(16_384, b"\x80\x80\x01", id="16384"),
        pytest.param(-128, b"\x80\xff\xff\xff\xff\xff\xff\xff\xff\x01", id="-128"),
        pytest.param(-16_383, b"\x81\x80\xff\xff\xff\xff\xff\xff\xff\x01", id="-16383"),
    ],
)
@pytest.mark.asyncio
async def test_write_varlong_matches_reference(conn_cls: ConnectionClass, number: int, expected: bytes):
    conn = conn_cls()
    _ = await maybe_await(conn.write_varlong(number))
    assert conn.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"\x7f", 127, id="127"),
        pytest.param(b"\x80\x80\x01", 16_384, id="16384"),
        pytest.param(b"\x80\xff\xff\xff\xff\xff\xff\xff\xff\x01", -128, id="-128"),
        pytest.param(b"\x81\x80\xff\xff\xff\xff\xff\xff\xff\x01", -16_383, id="-16383"),
    ],
)
@pytest.mark.asyncio
async def test_read_varlong_matches_reference(conn_cls: ConnectionClass, encoded: bytes, expected: int):
    conn = conn_cls(encoded)
    assert await maybe_await(conn.read_varlong()) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("number", [0, 1, 127, 16_384, -1, -(2**31), (2**31) - 1])
async def test_varint_roundtrip(conn_cls: ConnectionClass, number: int):
    conn = conn_cls()
    _ = await maybe_await(conn.write_varint(number))
    conn.receive(conn.flush())
    assert await maybe_await(conn.read_varint()) == number


@pytest.mark.asyncio
@pytest.mark.parametrize("number", [127, 16_384, -128, -16_383, -(2**63), (2**63) - 1])
async def test_varlong_roundtrip(conn_cls: ConnectionClass, number: int):
    conn = conn_cls()
    _ = await maybe_await(conn.write_varlong(number))
    conn.receive(conn.flush())
    assert await maybe_await(conn.read_varlong()) == number


@pytest.mark.asyncio
@pytest.mark.parametrize("number", [-(2**63) - 1, 2**63])
async def test_write_varlong_rejects_out_of_range(conn_cls: ConnectionClass, number: int):
    conn = conn_cls()
    with pytest.raises(ValueError, match=r"out of range"):
        _ = await maybe_await(conn.write_varlong(number))


@pytest.mark.asyncio
async def test_optional_helpers(conn_cls: ConnectionClass):
    conn = conn_cls()

    if isinstance(conn, AsyncBufferConnection):
        writer = AsyncMock(return_value="written")

        assert await conn.write_optional(None, writer) is None
        writer.assert_not_awaited()
        assert conn.flush() == b"\x00"

        assert await conn.write_optional("value", writer) == "written"
        writer.assert_awaited_once_with("value")
        assert conn.flush() == b"\x01"

        reader = AsyncMock(return_value="parsed")
        conn.receive(b"\x00")
        assert await conn.read_optional(reader) is None
        reader.assert_not_awaited()

        conn.receive(b"\x01")
        assert await conn.read_optional(reader) == "parsed"
        reader.assert_awaited_once_with()
        return

    writer = Mock(return_value="written")

    assert conn.write_optional(None, writer) is None
    writer.assert_not_called()
    assert conn.flush() == b"\x00"

    assert conn.write_optional("value", writer) == "written"
    writer.assert_called_once_with("value")
    assert conn.flush() == b"\x01"

    reader = Mock(return_value="parsed")
    conn.receive(b"\x00")
    assert conn.read_optional(reader) is None
    reader.assert_not_called()

    conn.receive(b"\x01")
    assert conn.read_optional(reader) == "parsed"
    reader.assert_called_once_with()


@pytest.mark.asyncio
async def test_write_and_read_ascii(conn_cls: ConnectionClass):
    conn = conn_cls()
    _ = await maybe_await(conn.write_ascii("hello"))

    conn.receive(conn.flush())
    assert await maybe_await(conn.read_ascii()) == "hello"


@pytest.mark.asyncio
async def test_write_and_read_bytearray(conn_cls: ConnectionClass):
    conn = conn_cls()
    data = b"\x00\x01hello\xff"

    _ = await maybe_await(conn.write_bytearray(data))
    conn.receive(conn.flush())

    assert await maybe_await(conn.read_bytearray()) == data


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param(b"", b"\x00", id="empty"),
        pytest.param(b"\x01", b"\x01\x01", id="single"),
        pytest.param(b"hello\x00world", b"\x0bhello\x00world", id="with-null"),
        pytest.param(b"\x01\x02\x03four\x05", b"\x08\x01\x02\x03four\x05", id="mixed"),
    ],
)
@pytest.mark.asyncio
async def test_write_bytearray_matches_reference(conn_cls: ConnectionClass, data: bytes, expected: bytes):
    conn = conn_cls()
    _ = await maybe_await(conn.write_bytearray(data))
    assert conn.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"\x00", b"", id="empty"),
        pytest.param(b"\x01\x01", b"\x01", id="single"),
        pytest.param(b"\x0bhello\x00world", b"hello\x00world", id="with-null"),
        pytest.param(b"\x08\x01\x02\x03four\x05", b"\x01\x02\x03four\x05", id="mixed"),
    ],
)
@pytest.mark.asyncio
async def test_read_bytearray_matches_reference(conn_cls: ConnectionClass, encoded: bytes, expected: bytes):
    conn = conn_cls(encoded)
    assert await maybe_await(conn.read_bytearray()) == expected


@pytest.mark.asyncio
async def test_read_bytearray_rejects_negative_length(conn_cls: ConnectionClass):
    conn = conn_cls(b"\xff\xff\xff\xff\x0f")
    with pytest.raises(OSError, match=r"^Length prefix for byte arrays must be non-negative, got -1\.$"):
        _ = await maybe_await(conn.read_bytearray())


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("test", b"test\x00", id="test"),
        pytest.param("a" * 100, b"a" * 100 + b"\x00", id="100-as"),
        pytest.param("", b"\x00", id="empty"),
    ],
)
@pytest.mark.asyncio
async def test_write_ascii_matches_reference(conn_cls: ConnectionClass, value: str, expected: bytes):
    conn = conn_cls()
    _ = await maybe_await(conn.write_ascii(value))
    assert conn.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"test\x00", "test", id="test"),
        pytest.param(b"a" * 100 + b"\x00", "a" * 100, id="100-as"),
        pytest.param(b"\x00", "", id="empty"),
    ],
)
@pytest.mark.asyncio
async def test_read_ascii_matches_reference(conn_cls: ConnectionClass, encoded: bytes, expected: str):
    conn = conn_cls(encoded)
    assert await maybe_await(conn.read_ascii()) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("test", b"\x04test", id="test"),
        pytest.param("a" * 100, b"\x64" + b"a" * 100, id="100-as"),
        pytest.param("", b"\x00", id="empty"),
        pytest.param("नमस्ते", b"\x12" + "नमस्ते".encode(), id="hindi"),
    ],
)
@pytest.mark.asyncio
async def test_write_utf_matches_reference(conn_cls: ConnectionClass, value: str, expected: bytes):
    conn = conn_cls()
    _ = await maybe_await(conn.write_utf(value))
    assert conn.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"\x04test", "test", id="test"),
        pytest.param(b"\x64" + b"a" * 100, "a" * 100, id="100-as"),
        pytest.param(b"\x00", "", id="empty"),
        pytest.param(b"\x12" + "नमस्ते".encode(), "नमस्ते", id="hindi"),
    ],
)
@pytest.mark.asyncio
async def test_read_utf_matches_reference(conn_cls: ConnectionClass, encoded: bytes, expected: str):
    conn = conn_cls(encoded)
    assert await maybe_await(conn.read_utf()) == expected


@pytest.mark.asyncio
async def test_write_utf_rejects_too_many_characters(conn_cls: ConnectionClass):
    conn = conn_cls()
    with pytest.raises(ValueError, match=r"Maximum character limit for writing strings is 32767 characters"):
        _ = await maybe_await(conn.write_utf("a" * 32768))


@pytest.mark.asyncio
async def test_read_utf_rejects_too_many_bytes(conn_cls: ConnectionClass):
    payload = Buffer()
    payload.write_varint(131069)

    conn = conn_cls(payload)
    with pytest.raises(OSError, match=r"Maximum read limit for utf strings is 131068 bytes, got 131069"):
        _ = await maybe_await(conn.read_utf())


@pytest.mark.asyncio
async def test_read_utf_rejects_negative_length(conn_cls: ConnectionClass):
    conn = conn_cls(b"\xff\xff\xff\xff\x0f")
    with pytest.raises(OSError, match=r"^Length prefix for utf strings must be non-negative, got -1\.$"):
        _ = await maybe_await(conn.read_utf())


@pytest.mark.asyncio
async def test_read_utf_rejects_too_many_characters(conn_cls: ConnectionClass):
    text = "a" * 32768
    payload = Buffer()
    payload.write_varint(len(text.encode("utf-8")))
    payload.write(text.encode("utf-8"))

    conn = conn_cls(payload)
    with pytest.raises(OSError, match=r"Maximum read limit for utf strings is 32767 characters, got 32768"):
        _ = await maybe_await(conn.read_utf())
