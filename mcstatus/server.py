from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from mcstatus._net.address import Address, async_minecraft_srv_address_lookup, minecraft_srv_address_lookup
from mcstatus._protocol.bedrock_client import BedrockClient
from mcstatus._protocol.connection import (
    TCPAsyncSocketConnection,
    TCPSocketConnection,
    UDPAsyncSocketConnection,
    UDPSocketConnection,
)
from mcstatus._protocol.java_client import AsyncJavaClient, JavaClient
from mcstatus._protocol.legacy_client import AsyncLegacyClient, LegacyClient
from mcstatus._protocol.query_client import AsyncQueryClient, QueryClient
from mcstatus._utils import retry

if TYPE_CHECKING:
    from typing_extensions import Self

    from mcstatus.responses import BedrockStatusResponse, JavaStatusResponse, LegacyStatusResponse, QueryResponse


__all__ = ["BedrockServer", "JavaServer", "LegacyServer", "MCServer"]


class MCServer(ABC):
    """Base abstract class for a general minecraft server.

    This class only contains the basic logic shared across both java and bedrock versions,
    it doesn't include any version specific settings and it can't be used to make any requests.
    """

    DEFAULT_PORT: int

    def __init__(self, host: str, port: int | None = None, timeout: float = 3) -> None:
        """
        :param host: The host/ip of the minecraft server.
        :param port: The port that the server is on.
        :param timeout: The timeout in seconds before failing to connect.
        """  # noqa: D205, D212 # no summary line
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


class BaseJavaServer(MCServer):
    """Base class for a Minecraft Java Edition server.

    .. versionadded:: 12.1.0
    """

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


class JavaServer(BaseJavaServer):
    """Base class for a 1.7+ Minecraft Java Edition server."""

    def __init__(self, host: str, port: int | None = None, timeout: float = 3, query_port: int | None = None) -> None:
        """
        :param host: The host/ip of the minecraft server.
        :param port: The port that the server is on.
        :param timeout: The timeout in seconds before failing to connect.
        :param query_port: Typically the same as ``port`` but can be different.
        """  # noqa: D205, D212 # no summary line
        super().__init__(host, port, timeout)
        if query_port is None:
            query_port = port or self.DEFAULT_PORT
        self.query_port = query_port
        _ = Address(host, self.query_port)  # Ensure query_port is valid

    def ping(self, *, tries: int = 3, version: int = 47, ping_token: int | None = None) -> float:
        """Check the latency between a Minecraft Java Edition server and the client (you).

        Note that most non-vanilla implementations fail to respond to a ping
        packet unless a status packet is sent first. Expect ``OSError: Server
        did not respond with any information!`` in those cases. The workaround
        is to use the latency provided with :meth:`.status` as ping time.

        :param tries: The number of times to retry if an error is encountered.
        :param version: Version of the client, see https://minecraft.wiki/w/Protocol_version#List_of_protocol_versions.
        :param ping_token: Token of the packet, default is a random number.
        :return: The latency between the Minecraft Server and you.
        """
        with TCPSocketConnection(self.address, self.timeout) as connection:
            return self._retry_ping(connection, tries=tries, version=version, ping_token=ping_token)

    @retry(tries=3)
    def _retry_ping(
        self,
        connection: TCPSocketConnection,
        *,
        tries: int = 3,  # noqa: ARG002 # unused argument
        version: int,
        ping_token: int | None,
    ) -> float:
        java_client = JavaClient(
            connection,
            address=self.address,
            version=version,
            ping_token=ping_token,  # pyright: ignore[reportArgumentType] # None is not assignable to int
        )
        java_client.handshake()
        return java_client.test_ping()

    async def async_ping(self, *, tries: int = 3, version: int = 47, ping_token: int | None = None) -> float:
        """Asynchronously check the latency between a Minecraft Java Edition server and the client (you).

        Note that most non-vanilla implementations fail to respond to a ping
        packet unless a status packet is sent first. Expect ``OSError: Server
        did not respond with any information!`` in those cases. The workaround
        is to use the latency provided with :meth:`.async_status` as ping time.

        :param tries: The number of times to retry if an error is encountered.
        :param version: Version of the client, see https://minecraft.wiki/w/Protocol_version#List_of_protocol_versions.
        :param ping_token: Token of the packet, default is a random number.
        :return: The latency between the Minecraft Server and you.
        """
        async with TCPAsyncSocketConnection(self.address, self.timeout) as connection:
            return await self._retry_async_ping(connection, tries=tries, version=version, ping_token=ping_token)

    @retry(tries=3)
    async def _retry_async_ping(
        self,
        connection: TCPAsyncSocketConnection,
        *,
        tries: int = 3,  # noqa: ARG002 # unused argument
        version: int,
        ping_token: int | None,
    ) -> float:
        java_client = AsyncJavaClient(
            connection,
            address=self.address,
            version=version,
            ping_token=ping_token,  # pyright: ignore[reportArgumentType] # None is not assignable to int
        )
        java_client.handshake()
        ping = await java_client.test_ping()
        return ping

    def status(self, *, tries: int = 3, version: int = 47, ping_token: int | None = None) -> JavaStatusResponse:
        """Check the status of a Minecraft Java Edition server via the status protocol.

        :param tries: The number of times to retry if an error is encountered.
        :param version: Version of the client, see https://minecraft.wiki/w/Protocol_version#List_of_protocol_versions.
        :param ping_token: Token of the packet, default is a random number.
        :return: Status information in a :class:`~mcstatus.responses.JavaStatusResponse` instance.
        """
        with TCPSocketConnection(self.address, self.timeout) as connection:
            return self._retry_status(connection, tries=tries, version=version, ping_token=ping_token)

    @retry(tries=3)
    def _retry_status(
        self,
        connection: TCPSocketConnection,
        *,
        tries: int = 3,  # noqa: ARG002 # unused argument
        version: int,
        ping_token: int | None,
    ) -> JavaStatusResponse:
        java_client = JavaClient(
            connection,
            address=self.address,
            version=version,
            ping_token=ping_token,  # pyright: ignore[reportArgumentType] # None is not assignable to int
        )
        java_client.handshake()
        result = java_client.read_status()
        return result

    async def async_status(self, *, tries: int = 3, version: int = 47, ping_token: int | None = None) -> JavaStatusResponse:
        """Asynchronously check the status of a Minecraft Java Edition server via the status protocol.

        :param tries: The number of times to retry if an error is encountered.
        :param version: Version of the client, see https://minecraft.wiki/w/Protocol_version#List_of_protocol_versions.
        :param ping_token: Token of the packet, default is a random number.
        :return: Status information in a :class:`~mcstatus.responses.JavaStatusResponse` instance.
        """
        async with TCPAsyncSocketConnection(self.address, self.timeout) as connection:
            return await self._retry_async_status(connection, tries=tries, version=version, ping_token=ping_token)

    @retry(tries=3)
    async def _retry_async_status(
        self,
        connection: TCPAsyncSocketConnection,
        *,
        tries: int = 3,  # noqa: ARG002 # unused argument
        version: int,
        ping_token: int | None,
    ) -> JavaStatusResponse:
        java_client = AsyncJavaClient(
            connection,
            address=self.address,
            version=version,
            ping_token=ping_token,  # pyright: ignore[reportArgumentType] # None is not assignable to int
        )
        java_client.handshake()
        result = await java_client.read_status()
        return result

    def query(self, *, tries: int = 3) -> QueryResponse:
        """Check the status of a Minecraft Java Edition server via the query protocol.

        :param tries: The number of times to retry if an error is encountered.
        :return: Query information in a :class:`~mcstatus.responses.QueryResponse` instance.
        """
        ip = str(self.address.resolve_ip())
        return self._retry_query(Address(ip, self.query_port), tries=tries)

    @retry(tries=3)
    def _retry_query(self, addr: Address, tries: int = 3) -> QueryResponse:  # noqa: ARG002 # unused argument
        with UDPSocketConnection(addr, self.timeout) as connection:
            query_client = QueryClient(connection)
            query_client.handshake()
            return query_client.read_query()

    async def async_query(self, *, tries: int = 3) -> QueryResponse:
        """Asynchronously check the status of a Minecraft Java Edition server via the query protocol.

        :param tries: The number of times to retry if an error is encountered.
        :return: Query information in a :class:`~mcstatus.responses.QueryResponse` instance.
        """
        ip = str(await self.address.async_resolve_ip())
        return await self._retry_async_query(Address(ip, self.query_port), tries=tries)

    @retry(tries=3)
    async def _retry_async_query(self, address: Address, tries: int = 3) -> QueryResponse:  # noqa: ARG002 # unused argument
        async with UDPAsyncSocketConnection(address, self.timeout) as connection:
            query_client = AsyncQueryClient(connection)
            await query_client.handshake()
            return await query_client.read_query()


class LegacyServer(BaseJavaServer):
    """Base class for a pre-1.7 Minecraft Java Edition server.

    .. versionadded:: 12.1.0
    """

    @retry(tries=3)
    def status(self, *, tries: int = 3) -> LegacyStatusResponse:  # noqa: ARG002 # unused argument
        """Check the status of a pre-1.7 Minecraft Java Edition server.

        :param tries: The number of times to retry if an error is encountered.
        :return: Status information in a :class:`~mcstatus.responses.LegacyStatusResponse` instance.
        """
        with TCPSocketConnection(self.address, self.timeout) as connection:
            return LegacyClient(connection).read_status()

    @retry(tries=3)
    async def async_status(self, *, tries: int = 3) -> LegacyStatusResponse:  # noqa: ARG002 # unused argument
        """Asynchronously check the status of a pre-1.7 Minecraft Java Edition server.

        :param tries: The number of times to retry if an error is encountered.
        :return: Status information in a :class:`~mcstatus.responses.LegacyStatusResponse` instance.
        """
        async with TCPAsyncSocketConnection(self.address, self.timeout) as connection:
            return await AsyncLegacyClient(connection).read_status()


class BedrockServer(MCServer):
    """Base class for a Minecraft Bedrock Edition server."""

    DEFAULT_PORT = 19132

    @retry(tries=3)
    def status(self, *, tries: int = 3) -> BedrockStatusResponse:  # noqa: ARG002 # unused argument
        """Check the status of a Minecraft Bedrock Edition server.

        :param tries: The number of times to retry if an error is encountered.
        :return: Status information in a :class:`~mcstatus.responses.BedrockStatusResponse` instance.
        """
        return BedrockClient(self.address, self.timeout).read_status()

    @retry(tries=3)
    async def async_status(self, *, tries: int = 3) -> BedrockStatusResponse:  # noqa: ARG002 # unused argument
        """Asynchronously check the status of a Minecraft Bedrock Edition server.

        :param tries: The number of times to retry if an error is encountered.
        :return: Status information in a :class:`~mcstatus.responses.BedrockStatusResponse` instance.
        """
        return await BedrockClient(self.address, self.timeout).read_status_async()
