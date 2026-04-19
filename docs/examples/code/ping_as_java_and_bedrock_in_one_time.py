from __future__ import annotations

import asyncio

from mcstatus import BedrockServer, JavaServer
from mcstatus.responses.bedrock import BedrockStatusResponse
from mcstatus.responses.java import JavaStatusResponse


async def handle_java(host: str) -> JavaStatusResponse:
    """Wrap mcstatus, to compress lookup and status into one function."""
    server = await JavaServer.async_lookup(host)
    return await server.async_status()


async def handle_bedrock(host: str) -> BedrockStatusResponse:
    """Wrap mcstatus, to compress lookup and status into one function."""
    # note: `BedrockServer` doesn't have `async_lookup` method, see it's docstring
    server = BedrockServer.lookup(host)
    return await server.async_status()


async def status(host: str) -> JavaStatusResponse | BedrockStatusResponse:
    """Get status from a server which can be either Java or Bedrock.

    The function will ping the server as both Java and as Bedrock at once, and return the first valid response, or fail.
    """
    tasks: list[asyncio.Task[JavaStatusResponse | BedrockStatusResponse]] = [
        asyncio.create_task(handle_java(host)),
        asyncio.create_task(handle_bedrock(host)),
    ]

    try:
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
            except Exception:  # noqa: S112,PERF203
                continue
            else:
                # Cancel the remaining task, we succeeded
                for t in tasks:
                    if t is not task:
                        t.cancel()
                return result
    finally:
        # Ensure all tasks are cleaned up
        for t in tasks:
            t.cancel()

    raise ValueError("No tasks were successful. Is the server offline?")
