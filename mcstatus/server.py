from __future__ import annotations

import warnings
from abc import ABC
from typing import Optional, TYPE_CHECKING

import dns.resolver

from mcstatus.address import Address, async_minecraft_srv_address_lookup, minecraft_srv_address_lookup
from mcstatus.bedrock_status import BedrockServerStatus, BedrockStatusResponse
from mcstatus.pinger import AsyncServerPinger, PingResponse, ServerPinger
from mcstatus.protocol.connection import (
    TCPAsyncSocketConnection,
    TCPSocketConnection,
    UDPAsyncSocketConnection,
    UDPSocketConnection,
)
from mcstatus.querier import AsyncServerQuerier, QueryResponse, ServerQuerier
from mcstatus.utils import retry

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ["JavaServer", "BedrockServer"]


class MCServer(ABC):
    """Base abstract class for a general minecraft server.

    This class only contains the basic logic shared across both java and bedrock versions,
    it doesn't include any version specific settings and it can't be used to make any requests.

    :param str host: The host/ip of the minecraft server.
    :param int port: The port that the server is on.
    :param float timeout: The timeout in seconds before failing to connect.
    """

    DEFAULT_PORT: int

    def __init__(self, host: str, port: Optional[int] = None, timeout: float = 3):
        if port is None:
            port = self.DEFAULT_PORT
        self.address = Address(host, port)
        self.timeout = timeout

    @classmethod
    def lookup(cls, address: str, timeout: float = 3) -> Self:
        """Mimics minecraft's server address field.

        :param str address: The address of the Minecraft server, like `example.com:19132`
        :param float timeout: The timeout in seconds before failing to connect.
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
        behavior as with minecraft's server address field for java. This DNS record
        resolution is happening synchronously (see async_lookup).

        :param str address: The address of the Minecraft server, like `example.com:25565`.
        :param float timeout: The timeout in seconds before failing to connect.
        """
        addr = minecraft_srv_address_lookup(address, default_port=cls.DEFAULT_PORT, lifetime=timeout)
        return cls(addr.host, addr.port, timeout=timeout)

    @classmethod
    async def async_lookup(cls, address: str, timeout: float = 3) -> Self:
        """Asynchronous alternative to lookup

        For more details, check the docstring of the synchronous lookup function.
        """
        addr = await async_minecraft_srv_address_lookup(address, default_port=cls.DEFAULT_PORT, lifetime=timeout)
        return cls(addr.host, addr.port, timeout=timeout)

    def ping(self, **kwargs) -> float:
        """Checks the latency between a Minecraft Java Edition server and the client (you).

        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        """

        connection = TCPSocketConnection(self.address, self.timeout)
        return self._retry_ping(connection, **kwargs)

    @retry(tries=3)
    def _retry_ping(self, connection: TCPSocketConnection, **kwargs) -> float:
        pinger = ServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        return pinger.test_ping()

    async def async_ping(self, **kwargs) -> float:
        """Asynchronously checks the latency between a Minecraft Java Edition server and the client (you).

        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: The latency between the Minecraft Server and you.
        """

        connection = TCPAsyncSocketConnection()
        await connection.connect(self.address, self.timeout)
        return await self._retry_async_ping(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_ping(self, connection: TCPAsyncSocketConnection, **kwargs) -> float:
        pinger = AsyncServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        ping = await pinger.test_ping()
        return ping

    def status(self, **kwargs) -> PingResponse:
        """Checks the status of a Minecraft Java Edition server via the ping protocol.

        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        """

        connection = TCPSocketConnection(self.address, self.timeout)
        return self._retry_status(connection, **kwargs)

    @retry(tries=3)
    def _retry_status(self, connection: TCPSocketConnection, **kwargs) -> PingResponse:
        pinger = ServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        result = pinger.read_status()
        result.latency = pinger.test_ping()
        return result

    async def async_status(self, **kwargs) -> PingResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the ping protocol.

        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        """

        connection = TCPAsyncSocketConnection()
        await connection.connect(self.address, self.timeout)
        return await self._retry_async_status(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_status(self, connection: TCPAsyncSocketConnection, **kwargs) -> PingResponse:
        pinger = AsyncServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        result = await pinger.read_status()
        result.latency = await pinger.test_ping()
        return result

    def query(self) -> QueryResponse:
        """Checks the status of a Minecraft Java Edition server via the query protocol."""
        # TODO: WARNING: This try-except for NXDOMAIN is only done because
        # of failing tests on mac-os, which for some reason can't resolve 'localhost'
        # into '127.0.0.1'. This try-except needs to be removed once this issue
        # is resolved!
        try:
            ip = str(self.address.resolve_ip())
        except dns.resolver.NXDOMAIN:
            warnings.warn(f"Resolving IP for {self.address.host} failed with NXDOMAIN")
            ip = self.address.host

        return self._retry_query(Address(ip, self.address.port))

    @retry(tries=3)
    def _retry_query(self, addr: Address) -> QueryResponse:
        connection = UDPSocketConnection(addr, self.timeout)
        querier = ServerQuerier(connection)
        querier.handshake()
        return querier.read_query()

    async def async_query(self) -> QueryResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the query protocol."""
        # TODO: WARNING: This try-except for NXDOMAIN is only done because
        # of failing tests on mac-os, which for some reason can't resolve 'localhost'
        # into '127.0.0.1'. This try-except needs to be removed once this issue
        # is resolved!
        try:
            ip = str(await self.address.async_resolve_ip())
        except dns.resolver.NXDOMAIN:
            warnings.warn(f"Resolving IP for {self.address.host} failed with NXDOMAIN")
            ip = self.address.host

        return await self._retry_async_query(Address(ip, self.address.port))

    @retry(tries=3)
    async def _retry_async_query(self, address: Address) -> QueryResponse:
        connection = UDPAsyncSocketConnection()
        await connection.connect(address, self.timeout)
        querier = AsyncServerQuerier(connection)
        await querier.handshake()
        return await querier.read_query()


class BedrockServer(MCServer):
    """Base class for a Minecraft Bedrock Edition server."""

    DEFAULT_PORT = 19132

    @retry(tries=3)
    def status(self, **kwargs) -> BedrockStatusResponse:
        """Checks the status of a Minecraft Bedrock Edition server.

        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockStatusResponse` instance.
        :rtype: BedrockStatusResponse
        """
        return BedrockServerStatus(self.address, self.timeout, **kwargs).read_status()

    @retry(tries=3)
    async def async_status(self, **kwargs) -> BedrockStatusResponse:
        """Asynchronously checks the status of a Minecraft Bedrock Edition server.

        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockStatusResponse` instance.
        :rtype: BedrockStatusResponse
        """
        return await BedrockServerStatus(self.address, self.timeout, **kwargs).read_status_async()
