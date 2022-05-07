from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple

import dns.resolver

from mcstatus.address import Address, async_minecraft_srv_address_lookup, minecraft_srv_address_lookup
from mcstatus.bedrock_status import BedrockServerStatus
from mcstatus.mc_server import BedrockServerResponse, JavaServerResponse, MCServerResponse, NotBedrockAndNotJavaServer
from mcstatus.pinger import AsyncServerPinger, ServerPinger
from mcstatus.protocol.connection import (
    TCPAsyncSocketConnection,
    TCPSocketConnection,
    UDPAsyncSocketConnection,
    UDPSocketConnection,
)
from mcstatus.querier import AsyncServerQuerier, QueryResponse, ServerQuerier
from mcstatus.utils import deprecated, retry

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ["ping", "async_ping", "MCServer", "JavaServer", "BedrockServer", "MinecraftServer", "MinecraftBedrockServer"]


def ping(address: str, timeout: int = 3, java_first: bool = False, **kwargs) -> Tuple[MCServer, MCServerResponse]:
    """Ping a Minecraft server and get `MCServerResponse` object."""
    servers = [BedrockServer, JavaServer]
    if java_first:
        servers.reverse()

    for server_cls in servers:
        server = server_cls.lookup(address, timeout=timeout)

        try:
            return server, server.status(**kwargs)
        except Exception:  # TODO: better exception, also how about standardize exceptions?
            continue

    raise NotBedrockAndNotJavaServer(f"The server ({address}) is not a java or bedrock server.")


async def async_ping(address: str, timeout: int = 3, java_first: bool = False, **kwargs) -> Tuple[MCServer, MCServerResponse]:
    """Ping a Minecraft server and get `MCServerResponse` object."""
    servers = [BedrockServer, JavaServer]
    if java_first:
        servers.reverse()

    for server_cls in servers:
        server = await server_cls.async_lookup(address, timeout=timeout)

        try:
            return server, await server.async_status(**kwargs)
        except Exception:  # TODO: better exception, also how about standardize exceptions?
            continue

    raise NotBedrockAndNotJavaServer(f"The server ({address}) is not a java or bedrock server.")


class MCServer(ABC):
    """Base class for a general minecraft server.

    This class contains the basic logic shared across both java and bedrock versions,
    also it to can be used as cross-platform ping.

    Firstly it will try to ping server as `JavaServer`, if it fails it will try to ping as `BedrockServer`.
    You can reverse it with the `first_bedrock` argument.

    :param str host: The host/ip of the minecraft server.
    :param int port: The port that the server is on.
    :param float timeout: The timeout in seconds before failing to connect.
    """

    def __init__(self, host: str, port: int, timeout: float = 3):
        self.address = Address(host, port)
        self.timeout = timeout

    @property
    @deprecated(replacement="address.host", date="2022-08")
    def host(self) -> str:
        return self.address.host

    @property
    @deprecated(replacement="address.port", date="2022-08")
    def port(self) -> int:
        return self.address.port

    @classmethod
    @abstractmethod
    def lookup(cls, address: str, timeout: float = 3) -> Self:
        """Lookup a minecraft server. This can have additional logic in children classes."""

    @classmethod
    @abstractmethod
    async def async_lookup(cls, address: str, timeout: float = 3) -> Self:
        """Async lookup a minecraft server. This can have additional logic in children classes."""

    @classmethod
    @abstractmethod
    def status(cls, **kwargs) -> MCServerResponse:
        """Get the status of the minecraft server."""

    @classmethod
    @abstractmethod
    async def async_status(cls, **kwargs) -> MCServerResponse:
        """Async get the status of the minecraft server."""


class JavaServer(MCServer):
    """Base class for a Minecraft Java Edition server."""

    def __init__(self, host: str, port: int = 25565, timeout: float = 3):
        """Override init to add a default port for java servers of 25565."""
        super().__init__(host, port, timeout=timeout)

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
        addr = minecraft_srv_address_lookup(address, default_port=25565, lifetime=timeout)
        return cls(addr.host, addr.port, timeout=timeout)

    @classmethod
    async def async_lookup(cls, address: str, timeout: float = 3) -> Self:
        """Asynchronous alternative to lookup

        For more details, check the docstring of the synchronous lookup function.
        """
        addr = await async_minecraft_srv_address_lookup(address, default_port=25565, lifetime=timeout)
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

    def status(self, **kwargs) -> JavaServerResponse:
        """Checks the status of a Minecraft Java Edition server via the ping protocol.

        :param type **kwargs: Passed to a `ServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        """

        connection = TCPSocketConnection(self.address, self.timeout)
        return self._retry_status(connection, **kwargs)

    @retry(tries=3)
    def _retry_status(self, connection: TCPSocketConnection, **kwargs) -> JavaServerResponse:
        pinger = ServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        result = pinger.read_status()
        result.latency = pinger.test_ping()
        return JavaServerResponse.build(result)

    async def async_status(self, **kwargs) -> JavaServerResponse:
        """Asynchronously checks the status of a Minecraft Java Edition server via the ping protocol.

        :param type **kwargs: Passed to a `AsyncServerPinger` instance.
        :return: Status information in a `PingResponse` instance.
        """

        connection = TCPAsyncSocketConnection()
        await connection.connect(self.address, self.timeout)
        return await self._retry_async_status(connection, **kwargs)

    @retry(tries=3)
    async def _retry_async_status(self, connection: TCPAsyncSocketConnection, **kwargs) -> JavaServerResponse:
        pinger = AsyncServerPinger(connection, address=self.address, **kwargs)
        pinger.handshake()
        result = await pinger.read_status()
        result.latency = await pinger.test_ping()
        return JavaServerResponse.build(result)

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

    def __init__(self, host: str, port: int = 19132, timeout: float = 3):
        """Override init to add a default port for bedrock servers of 19132."""
        super().__init__(host, port, timeout=timeout)

    @classmethod
    def lookup(cls, address: str, timeout: float = 3) -> Self:
        """Parse `address` parameter and return initialized object."""
        host, port = address.split(":")
        return cls(host, int(port), timeout=timeout)

    @classmethod
    async def async_lookup(cls, address: str, timeout: float = 3) -> Self:
        """Just call `lookup` without any async, for implement all methods from abstract class."""
        return cls.lookup(address, timeout)

    @retry(tries=3)
    def status(self, **kwargs) -> BedrockServerResponse:
        """Checks the status of a Minecraft Bedrock Edition server.

        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockServerResponse` instance.
        :rtype: BedrockServerResponse
        """
        return BedrockServerResponse.build(BedrockServerStatus(self.address, self.timeout, **kwargs).read_status())

    @retry(tries=3)
    async def async_status(self, **kwargs) -> BedrockServerResponse:
        """Asynchronously checks the status of a Minecraft Bedrock Edition server.

        :param type **kwargs: Passed to a `BedrockServerStatus` instance.
        :return: Status information in a `BedrockServerResponse` instance.
        :rtype: BedrockServerResponse
        """
        return BedrockServerResponse.build(await BedrockServerStatus(self.address, self.timeout, **kwargs).read_status_async())


@deprecated(replacement="JavaServer", date="2022-08", methods=("__init__",))
class MinecraftServer(JavaServer):
    """This is a deprecated version of the base class for a Java Minecraft Server.

    This class is kept purely for backwards compatibility reasons and will be removed eventually.
    """

    def __init__(self, host: str, port: int = 25565, timeout: float = 3):
        super().__init__(host, port=port, timeout=timeout)


@deprecated(replacement="BedrockServer", date="2022-08", methods=("__init__",))
class MinecraftBedrockServer(BedrockServer):
    """This is a deprecated version of the base class for a Bedrock Minecraft Server.

    This class is kept purely for backwards compatibility reasons and will be removed eventually.
    """

    def __init__(self, host: str, port: int = 19132, timeout: float = 3):
        super().__init__(host, port=port, timeout=timeout)
