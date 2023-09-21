from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from mcstatus.address import Address, async_minecraft_srv_address_lookup, minecraft_srv_address_lookup
from mcstatus.bedrock_status import BedrockServerStatus
from mcstatus.pinger import AsyncServerPinger, ServerPinger
from mcstatus.protocol.connection import (
    TCPAsyncSocketConnection,
    TCPSocketConnection,
    UDPAsyncSocketConnection,
    UDPSocketConnection,
)
from mcstatus.querier import AsyncServerQuerier, QueryResponse, ServerQuerier
from mcstatus.status_response import BedrockStatusResponse, JavaStatusResponse
from mcstatus.utils import retry

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ["MCServer", "JavaServer", "BedrockServer"]


class MCServer(ABC):
    """Base abstract class for a general minecraft server.

    This class only contains the basic logic shared across both java and bedrock versions,
    it doesn't include any version specific settings and it can't be used to make any requests.
    """

    DEFAULT_PORT: int

    def __init__(self, host: str, port: int | None = None, timeout: float = 3):
        """
        :param host: The host/ip of the minecraft server.
        :param port: The port that the server is on.
        :param timeout: The timeout in seconds before failing to connect.
        """
        if port is None:
            port = self.DEFAULT_PORT
        self.address = Address(host, port)
        self.timeout = timeout

    @classmethod
    def lookup(cls, address: str, timeout: float = 3) -> Self:
        """Mimics minecraft's server address field.

        :param address: The address of the Minecraft server, like ``example.com:19132``
        :param timeout: The timeout in seconds before failing to connect.
        """
        addr = Address.parse_address(address, default_port=cls.DEFAULT_PORT)
        return cls(addr.host, addr.port, timeout=timeout)


class JavaServer(MCServer):
    """Base class for a Minecraft Java Edition server."""

    DEFAULT_PORT = 25565

    @classmethod
    def lookup(cls, address: str, timeout: float = 3) -> Self:
        """Mimics minecraft's server address field.

        With Java servers, on top of just parsing the address, we also check the
        DNS records for an SRV record that points to the server, which is the same
        behavior as with minecraft's server address field for Java. This DNS record
        resolution is happening synchronously (see :meth:`.async_lookup`).

        :param address: The address of the Minecraft server, like ``example.com:25565``.
        :param timeout: The timeout in seconds before failing to connect.
        """
        addr = minecraft_srv_address_lookup(address, default_port=cls.DEFAULT_PORT, lifetime=timeout)
        return cls(addr.host, addr.port, timeout=timeout)

    @classmethod
    async def async_lookup(cls, address: str, timeout: float = 3) -> Self:
        """Asynchronous alternative to :meth:`.lookup`.

        For more details, check the :meth:`JavaServer.lookup() <.lookup>` docstring.
        """
        addr = await async_minecraft_srv_address_lookup(address, default_port=cls.DEFAULT_PORT, lifetime=timeout)
        return cls(addr.host, addr.port, timeout=timeout)

    def ping(self, **kwargs) -> float:
        """Checks the latency between a Minecraft Java Edition server and the client (you).

        :param kwargs: Passed to a :class:`~mcstatus.pinger.ServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        """

        with TCPSocketConnection(self.address, self.timeout) as connection:
            return self._retry_ping(connection, **kwargs)

    @retry(tries=3)
    def _retry_ping(self, connection: TCPSocketConnection, **kwargs) -> float:
        pinger = ServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        return pinger.test_ping()

    async def async_ping(self, **kwargs) -> float:
        """Asynchronously checks the latency between a Minecraft Java Edition server and the client (you).

        :param kwargs: Passed to a :class:`~mcstatus.pinger.AsyncServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        """

        async with TCPAsyncSocketConnection(self.address, self.timeout) as connection:
            return await self._retry_async_ping(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_ping(self, connection: TCPAsyncSocketConnection, **kwargs) -> float:
        pinger = AsyncServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        ping = await pinger.test_ping()
        return ping

    def status(self, **kwargs) -> JavaStatusResponse:
        """Checks the status of a Minecraft Java Edition server via the status protocol.

        :param kwargs: Passed to a :class:`~mcstatus.pinger.ServerPinger` instance.
        :return: Status information in a :class:`~mcstatus.status_response.JavaStatusResponse` instance.
        """

        with TCPSocketConnection(self.address, self.timeout) as connection:
            return self._retry_status(connection, **kwargs)

    @retry(tries=3)
    def _retry_status(self, connection: TCPSocketConnection, **kwargs) -> JavaStatusResponse:
        pinger = ServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        result = pinger.read_status()
        return result

    async def async_status(self, **kwargs) -> JavaStatusResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the status protocol.

        :param kwargs: Passed to a :class:`~mcstatus.pinger.AsyncServerPinger` instance.
        :return: Status information in a :class:`~mcstatus.status_response.JavaStatusResponse` instance.
        """

        async with TCPAsyncSocketConnection(self.address, self.timeout) as connection:
            return await self._retry_async_status(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_status(self, connection: TCPAsyncSocketConnection, **kwargs) -> JavaStatusResponse:
        pinger = AsyncServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        result = await pinger.read_status()
        return result

    def query(self) -> QueryResponse:
        """Checks the status of a Minecraft Java Edition server via the query protocol."""
        ip = str(self.address.resolve_ip())
        return self._retry_query(Address(ip, self.address.port))

    @retry(tries=3)
    def _retry_query(self, addr: Address) -> QueryResponse:
        with UDPSocketConnection(addr, self.timeout) as connection:
            querier = ServerQuerier(connection)
            querier.handshake()
            return querier.read_query()

    async def async_query(self) -> QueryResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the query protocol."""
        ip = str(await self.address.async_resolve_ip())
        return await self._retry_async_query(Address(ip, self.address.port))

    @retry(tries=3)
    async def _retry_async_query(self, address: Address) -> QueryResponse:
        async with UDPAsyncSocketConnection(address, self.timeout) as connection:
            querier = AsyncServerQuerier(connection)
            await querier.handshake()
            return await querier.read_query()


class BedrockServer(MCServer):
    """Base class for a Minecraft Bedrock Edition server."""

    DEFAULT_PORT = 19132

    @retry(tries=3)
    def status(self, **kwargs) -> BedrockStatusResponse:
        """Checks the status of a Minecraft Bedrock Edition server.

        :param kwargs: Passed to a :class:`~mcstatus.bedrock_status.BedrockServerStatus` instance.
        :return: Status information in a :class:`~mcstatus.status_response.BedrockStatusResponse` instance.
        """
        return BedrockServerStatus(self.address, self.timeout, **kwargs).read_status()

    @retry(tries=3)
    async def async_status(self, **kwargs) -> BedrockStatusResponse:
        """Asynchronously checks the status of a Minecraft Bedrock Edition server.

        :param kwargs: Passed to a :class:`~mcstatus.bedrock_status.BedrockServerStatus` instance.
        :return: Status information in a :class:`~mcstatus.status_response.BedrockStatusResponse` instance.
        """
        return await BedrockServerStatus(self.address, self.timeout, **kwargs).read_status_async()
