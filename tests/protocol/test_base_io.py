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

IO_TYPE = type[SyncBufferConnection] | type[AsyncBufferConnection]
T = TypeVar("T")


@pytest.fixture(
    params=[
        pytest.param(SyncBufferConnection, id="sync"),
        pytest.param(AsyncBufferConnection, id="async"),
    ]
)
def io_type(request: pytest.FixtureRequest) -> IO_TYPE:
    """Provide a parametrized sync and async IO connections to each test."""
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
async def test_write_value_matches_reference(io_type: IO_TYPE, fmt: INT_FORMATS_TYPE, value: int, expected: bytes):
    io = io_type()
    await maybe_await(io.write_value(fmt, value))
    assert io.flush() == expected


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
async def test_write_value_rejects_out_of_range(io_type: IO_TYPE, fmt: INT_FORMATS_TYPE, value: int):
    io = io_type()
    with pytest.raises(struct.error):
        await maybe_await(io.write_value(fmt, value))


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
async def test_read_value_matches_reference(io_type: IO_TYPE, encoded: bytes, fmt: INT_FORMATS_TYPE, expected: int):
    io = io_type(encoded)
    assert await maybe_await(io.read_value(fmt)) == expected


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
async def test_write_varuint_matches_reference(io_type: IO_TYPE, number: int, expected: bytes):
    io = io_type()
    await maybe_await(io._write_varuint(number))
    assert io.flush() == expected


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
async def test_read_varuint_matches_reference(io_type: IO_TYPE, encoded: bytes, expected: int):
    io = io_type(encoded)
    assert await maybe_await(io._read_varuint()) == expected


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
async def test_write_varuint_rejects_out_of_range(io_type: IO_TYPE, number: int, max_bits: int):
    io = io_type()
    with pytest.raises(ValueError, match=r"outside of the range of"):
        await maybe_await(io._write_varuint(number, max_bits=max_bits))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("encoded", "max_bits"),
    [
        (b"\x80\x80\x04", 16),
        (b"\x80\x80\x80\x80\x10", 32),
    ],
)
async def test_read_varuint_rejects_out_of_range(io_type: IO_TYPE, encoded: bytes, max_bits: int):
    io = io_type(encoded)
    with pytest.raises(OSError, match=r"outside the range of"):
        await maybe_await(io._read_varuint(max_bits=max_bits))


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
async def test_write_varint_matches_reference(io_type: IO_TYPE, number: int, expected: bytes):
    io = io_type()
    await maybe_await(io.write_varint(number))
    assert io.flush() == expected


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
async def test_read_varint_matches_reference(io_type: IO_TYPE, encoded: bytes, expected: int):
    io = io_type(encoded)
    assert await maybe_await(io.read_varint()) == expected


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
async def test_write_varlong_matches_reference(io_type: IO_TYPE, number: int, expected: bytes):
    io = io_type()
    await maybe_await(io.write_varlong(number))
    assert io.flush() == expected


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
async def test_read_varlong_matches_reference(io_type: IO_TYPE, encoded: bytes, expected: int):
    io = io_type(encoded)
    assert await maybe_await(io.read_varlong()) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("number", [0, 1, 127, 16_384, -1, -(2**31), (2**31) - 1])
async def test_varint_roundtrip(io_type: IO_TYPE, number: int):
    io = io_type()
    await maybe_await(io.write_varint(number))
    io.receive(io.flush())
    assert await maybe_await(io.read_varint()) == number


@pytest.mark.asyncio
@pytest.mark.parametrize("number", [127, 16_384, -128, -16_383, -(2**63), (2**63) - 1])
async def test_varlong_roundtrip(io_type: IO_TYPE, number: int):
    io = io_type()
    await maybe_await(io.write_varlong(number))
    io.receive(io.flush())
    assert await maybe_await(io.read_varlong()) == number


@pytest.mark.asyncio
@pytest.mark.parametrize("number", [-(2**63) - 1, 2**63])
async def test_write_varlong_rejects_out_of_range(io_type: IO_TYPE, number: int):
    io = io_type()
    with pytest.raises(ValueError, match=r"out of range"):
        await maybe_await(io.write_varlong(number))


@pytest.mark.asyncio
async def test_optional_helpers(io_type: IO_TYPE):
    io = io_type()

    if isinstance(io, AsyncBufferConnection):
        writer = AsyncMock(return_value="written")

        assert await io.write_optional(None, writer) is None
        writer.assert_not_awaited()
        assert io.flush() == b"\x00"

        assert await io.write_optional("value", writer) == "written"
        writer.assert_awaited_once_with("value")
        assert io.flush() == b"\x01"

        reader = AsyncMock(return_value="parsed")
        io.receive(b"\x00")
        assert await io.read_optional(reader) is None
        reader.assert_not_awaited()

        io.receive(b"\x01")
        assert await io.read_optional(reader) == "parsed"
        reader.assert_awaited_once_with()
        return

    writer = Mock(return_value="written")

    assert io.write_optional(None, writer) is None
    writer.assert_not_called()
    assert io.flush() == b"\x00"

    assert io.write_optional("value", writer) == "written"
    writer.assert_called_once_with("value")
    assert io.flush() == b"\x01"

    reader = Mock(return_value="parsed")
    io.receive(b"\x00")
    assert io.read_optional(reader) is None
    reader.assert_not_called()

    io.receive(b"\x01")
    assert io.read_optional(reader) == "parsed"
    reader.assert_called_once_with()


@pytest.mark.asyncio
async def test_write_and_read_ascii(io_type: IO_TYPE):
    io = io_type()
    await maybe_await(io.write_ascii("hello"))

    io.receive(io.flush())
    assert await maybe_await(io.read_ascii()) == "hello"


@pytest.mark.asyncio
async def test_write_and_read_bytearray(io_type: IO_TYPE):
    io = io_type()
    data = b"\x00\x01hello\xff"

    await maybe_await(io.write_bytearray(data))
    io.receive(io.flush())

    assert await maybe_await(io.read_bytearray()) == data


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
async def test_write_bytearray_matches_reference(io_type: IO_TYPE, data: bytes, expected: bytes):
    io = io_type()
    await maybe_await(io.write_bytearray(data))
    assert io.flush() == expected


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
async def test_read_bytearray_matches_reference(io_type: IO_TYPE, encoded: bytes, expected: bytes):
    io = io_type(encoded)
    assert await maybe_await(io.read_bytearray()) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param("test", b"test\x00", id="test"),
        pytest.param("a" * 100, b"a" * 100 + b"\x00", id="100-as"),
        pytest.param("", b"\x00", id="empty"),
    ],
)
@pytest.mark.asyncio
async def test_write_ascii_matches_reference(io_type: IO_TYPE, value: str, expected: bytes):
    io = io_type()
    await maybe_await(io.write_ascii(value))
    assert io.flush() == expected


@pytest.mark.parametrize(
    ("encoded", "expected"),
    [
        pytest.param(b"test\x00", "test", id="test"),
        pytest.param(b"a" * 100 + b"\x00", "a" * 100, id="100-as"),
        pytest.param(b"\x00", "", id="empty"),
    ],
)
@pytest.mark.asyncio
async def test_read_ascii_matches_reference(io_type: IO_TYPE, encoded: bytes, expected: str):
    io = io_type(encoded)
    assert await maybe_await(io.read_ascii()) == expected


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
async def test_write_utf_matches_reference(io_type: IO_TYPE, value: str, expected: bytes):
    io = io_type()
    await maybe_await(io.write_utf(value))
    assert io.flush() == expected


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
async def test_read_utf_matches_reference(io_type: IO_TYPE, encoded: bytes, expected: str):
    io = io_type(encoded)
    assert await maybe_await(io.read_utf()) == expected


@pytest.mark.asyncio
async def test_write_utf_rejects_too_many_characters(io_type: IO_TYPE):
    io = io_type()
    with pytest.raises(ValueError, match=r"Maximum character limit for writing strings is 32767 characters"):
        await maybe_await(io.write_utf("a" * 32768))


@pytest.mark.asyncio
async def test_read_utf_rejects_too_many_bytes(io_type: IO_TYPE):
    payload = Buffer()
    payload.write_varint(131069)

    io = io_type(payload)
    with pytest.raises(OSError, match=r"Maximum read limit for utf strings is 131068 bytes, got 131069"):
        await maybe_await(io.read_utf())


@pytest.mark.asyncio
async def test_read_utf_rejects_too_many_characters(io_type: IO_TYPE):
    text = "a" * 32768
    payload = Buffer()
    payload.write_varint(len(text.encode("utf-8")))
    payload.write(text.encode("utf-8"))

    io = io_type(payload)
    with pytest.raises(OSError, match=r"Maximum read limit for utf strings is 32767 characters, got 32768"):
        await maybe_await(io.read_utf())
