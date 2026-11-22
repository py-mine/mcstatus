from __future__ import annotations

import asyncio
import threading
import time

import pytest

from mcstatus._utils.concurrency import async_first_success, first_success


class TestSyncFirstSuccess:
    """Tests for the synchronous `first_success` function variant."""

    def test_single_item_success(self):
        assert first_success([lambda: 42]) == 42

    def test_single_item_failure(self):
        def fail():
            raise RuntimeError("failed")

        with pytest.raises(RuntimeError, match="failed"):
            _ = first_success([fail])

    def test_first_succeeds(self):
        def fast():
            return "fast"

        def slow():
            time.sleep(1)
            return "slow"

        assert first_success([fast, slow]) == "fast"

    def test_fallback_succeeds(self):
        def fail():
            raise RuntimeError("first failed")

        def succeed():
            time.sleep(0.05)
            return "fallback"

        assert first_success([fail, succeed]) == "fallback"

    def test_all_fail_raises_exception_group(self):
        def fail1():
            time.sleep(0.05)
            raise RuntimeError("err 1")

        def fail2():
            raise ValueError("err 2")

        with pytest.RaisesGroup(RuntimeError, ValueError) as exc_info:
            _ = first_success([fail1, fail2])

        assert exc_info.value.message == "All concurrent operations failed"
        # ExceptionGroup order is guaranteed to match the input function sequence order,
        # even though fail2 finished before fail1.
        assert len(exc_info.value.exceptions) == 2
        assert isinstance(exc_info.value.exceptions[0], RuntimeError)
        assert isinstance(exc_info.value.exceptions[1], ValueError)

    def test_base_exception_immediate(self):
        class CustomBaseError(BaseException):
            pass

        def raise_base():
            raise CustomBaseError("critical failure")

        def normal():
            time.sleep(1)
            return "ok"

        with pytest.raises(CustomBaseError, match="critical failure"):
            _ = first_success([raise_base, normal])

    def test_thread_name_prefix(self):
        captured_names: list[str] = []

        def task():
            captured_names.append(threading.current_thread().name)
            return "ok"

        res = first_success([task], thread_name_prefix="custom-worker")
        assert res == "ok"

        # Multi-item concurrency
        def slow_task():
            captured_names.append(threading.current_thread().name)
            return "multi-ok"

        res = first_success([slow_task, slow_task], thread_name_prefix="custom-worker")
        assert res == "multi-ok"
        assert any(name.startswith("custom-worker-") for name in captured_names)


class TestAsyncFirstSuccess:
    """Tests for the asynchronous `async_first_success` function variant."""

    async def test_single_item_success(self):
        async def succeed():
            await asyncio.sleep(0)
            return 42

        assert await async_first_success([succeed()]) == 42

    async def test_single_item_failure(self):
        async def fail():
            await asyncio.sleep(0)
            raise RuntimeError("failed")

        with pytest.raises(RuntimeError, match="failed"):
            _ = await async_first_success([fail()])

    async def test_first_succeeds(self):
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

    async def test_success_fallback_succeeds(self):
        async def fail():
            await asyncio.sleep(0)
            raise RuntimeError("first failed")

        async def succeed():
            await asyncio.sleep(0.05)
            return "fallback"

        assert await async_first_success([fail(), succeed()]) == "fallback"

    async def test_all_fail_raises_exception_group(self):
        async def fail1():
            await asyncio.sleep(0.05)
            raise RuntimeError("err 1")

        async def fail2():
            await asyncio.sleep(0)
            raise ValueError("err 2")

        with pytest.RaisesGroup(RuntimeError, ValueError) as exc_info:
            _ = await async_first_success([fail1(), fail2()])

        assert exc_info.value.message == "All concurrent operations failed"
        # ExceptionGroup order is guaranteed to match the input coroutine sequence order,
        # even though fail2 finished before fail1.
        assert len(exc_info.value.exceptions) == 2
        assert isinstance(exc_info.value.exceptions[0], RuntimeError)
        assert isinstance(exc_info.value.exceptions[1], ValueError)

    async def test_base_exception_immediate(self):
        class CustomBaseError(BaseException):
            pass

        async def raise_base():
            await asyncio.sleep(0)
            raise CustomBaseError("critical failure")

        async def normal():
            await asyncio.sleep(1)
            return "ok"

        with pytest.raises(CustomBaseError, match="critical failure"):
            _ = await async_first_success([raise_base(), normal()])

    async def test_task_name_prefix(self):
        captured_names: list[str] = []

        async def task():  # ruff: ignore[unused-async]
            current = asyncio.current_task()
            assert current is not None
            captured_names.append(current.get_name())
            return "ok"

        result = await async_first_success([task()], task_name_prefix="custom-worker")
        assert result == "ok"
        assert captured_names == ["custom-worker-0"]

        captured_names.clear()

        result = await async_first_success([task(), task()], task_name_prefix="custom-worker")
        assert result == "ok"
        assert set(captured_names) == {"custom-worker-0", "custom-worker-1"}
