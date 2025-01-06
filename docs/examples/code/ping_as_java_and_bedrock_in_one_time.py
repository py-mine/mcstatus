from __future__ import annotations
import asyncio

from mcstatus import BedrockServer, JavaServer
from mcstatus.responses import BedrockStatusResponse, JavaStatusResponse


async def status(host: str) -> JavaStatusResponse | BedrockStatusResponse:
    """Get status from server, which can be Java or Bedrock.

    The function will ping server as Java and as Bedrock in one time, and return the first response.
    """
    success_task = await handle_exceptions(
        *(
            await asyncio.wait(
                {
                    asyncio.create_task(handle_java(host), name="Get status as Java"),
                    asyncio.create_task(handle_bedrock(host), name="Get status as Bedrock"),
                },
                return_when=asyncio.FIRST_COMPLETED,
            )
        )
    )

    if success_task is None:
        raise ValueError("No tasks were successful. Is server offline?")

    return success_task.result()


async def handle_exceptions(done: set[asyncio.Task], pending: set[asyncio.Task]) -> asyncio.Task | None:
    """Handle exceptions from tasks.

    Also, cancel all pending tasks, if found correct one.
    """
    if len(done) == 0:
        raise ValueError("No tasks was given to `done` set.")

    for i, task in enumerate(done):
        if task.exception() is not None:
            if len(pending) == 0:
                continue

            if i == len(done) - 1:  # firstly check all items from `done` set, and then handle pending set
                return await handle_exceptions(*(await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)))
        else:
            for pending_task in pending:
                pending_task.cancel()
            return task


async def handle_java(host: str) -> JavaStatusResponse:
    """A wrapper around mcstatus, to compress it in one function."""
    return await (await JavaServer.async_lookup(host)).async_status()


async def handle_bedrock(host: str) -> BedrockStatusResponse:
    """A wrapper around mcstatus, to compress it in one function."""
    # note: `BedrockServer` doesn't have `async_lookup` method, see it's docstring
    return await BedrockServer.lookup(host).async_status()
