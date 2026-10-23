from __future__ import annotations

import asyncio
import time

import pytest

from mcstatus._utils.concurrency import async_first_success, first_success, primary_error


def test_primary_error():
    err1 = RuntimeError("first failure")
    err2 = ValueError("second failure")

    result = primary_error([err1, err2])
    assert result is err1
    assert hasattr(result, "__notes__")
    assert any("second failure" in str(note) for note in result.__notes__)


def test_first_success_single_item_fast_path():
    assert first_success([lambda: 42]) == 42

    def fail():
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        _ = first_success([fail])


def test_first_success_first_succeeds():
    def fast():
        return "fast"

    def slow():
        time.sleep(1)
        return "slow"

    assert first_success([fast, slow]) == "fast"


def test_first_success_fallback_succeeds():
    def fail():
        raise RuntimeError("first failed")

    def succeed():
        return "fallback"

    assert first_success([fail, succeed]) == "fallback"


def test_first_success_all_fail_with_notes():
    def fail1():
        raise RuntimeError("err 1")

    def fail2():
        raise ValueError("err 2")

    with pytest.raises(RuntimeError, match="err 1") as exc_info:
        _ = first_success([fail1, fail2])

    assert any("err 2" in str(note) for note in exc_info.value.__notes__)


def test_first_success_base_exception_immediate():
    class CustomBaseError(BaseException):
        pass

    def raise_base():
        raise CustomBaseError("critical failure")

    def normal():
        time.sleep(1)
        return "ok"

    with pytest.raises(CustomBaseError, match="critical failure"):
        _ = first_success([raise_base, normal])


async def test_async_first_success_single_item_fast_path():
    async def succeed():
        await asyncio.sleep(0)
        return 42

    async def fail():
        await asyncio.sleep(0)
        raise RuntimeError("failed")

    assert await async_first_success([succeed()]) == 42
    with pytest.raises(RuntimeError, match="failed"):
        _ = await async_first_success([fail()])


async def test_async_first_success_first_succeeds():
    cancelled = False

    async def fast():
        await asyncio.sleep(0)
        return "fast"

    async def slow():
        nonlocal cancelled
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            cancelled = True
            raise
        else:
            return "slow"

    assert await async_first_success([fast(), slow()]) == "fast"
    assert cancelled


async def test_async_first_success_fallback_succeeds():
    async def fail():
        await asyncio.sleep(0)
        raise RuntimeError("first failed")

    async def succeed():
        await asyncio.sleep(0)
        return "fallback"

    assert await async_first_success([fail(), succeed()]) == "fallback"


async def test_async_first_success_all_fail_with_notes():
    async def fail1():
        await asyncio.sleep(0)
        raise RuntimeError("err 1")

    async def fail2():
        await asyncio.sleep(0)
        raise ValueError("err 2")

    with pytest.raises(RuntimeError, match="err 1") as exc_info:
        _ = await async_first_success([fail1(), fail2()])

    assert any("err 2" in str(note) for note in exc_info.value.__notes__)
