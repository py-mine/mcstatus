from __future__ import annotations

import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, TYPE_CHECKING, final

from mcstatus._protocol.io.base_io import StructFormat
from mcstatus._protocol.io.buffer import Buffer
from mcstatus.responses import QueryResponse
from mcstatus.responses._raw import RawQueryResponse

__all__ = ["AsyncQueryClient", "QueryClient"]

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from typing_extensions import override

    from mcstatus._protocol.io.connection import UDPAsyncSocketConnection, UDPSocketConnection
else:
    override = lambda f: f  # noqa: E731


@dataclass
class _BaseQueryClient(ABC):
    MAGIC_PREFIX: ClassVar[bytearray] = bytearray.fromhex("FEFD")
    PADDING: ClassVar[bytearray] = bytearray.fromhex("00000000")
    PACKET_TYPE_CHALLENGE: ClassVar[int] = 9
    PACKET_TYPE_QUERY: ClassVar[int] = 0

    connection: UDPSocketConnection | UDPAsyncSocketConnection
    challenge: int = field(init=False, default=0)

    @staticmethod
    def _generate_session_id() -> int:
        # minecraft only supports lower 4 bits
        return random.randint(0, 2**31) & 0x0F0F0F0F

    def _create_packet(self) -> Buffer:
        packet = Buffer()
        packet.write(self.MAGIC_PREFIX)
        packet.write_value(StructFormat.UBYTE, self.PACKET_TYPE_QUERY)
        packet.write_value(StructFormat.UINT, self._generate_session_id())
        packet.write_value(StructFormat.INT, self.challenge)
        packet.write(self.PADDING)
        return packet

    def _create_handshake_packet(self) -> Buffer:
        packet = Buffer()
        packet.write(self.MAGIC_PREFIX)
        packet.write_value(StructFormat.UBYTE, self.PACKET_TYPE_CHALLENGE)
        packet.write_value(StructFormat.UINT, self._generate_session_id())
        return packet

    @abstractmethod
    def _read_packet(self) -> Buffer | Awaitable[Buffer]:
        raise NotImplementedError

    @abstractmethod
    def handshake(self) -> None | Awaitable[None]:
        raise NotImplementedError

    @abstractmethod
    def read_query(self) -> QueryResponse | Awaitable[QueryResponse]:
        raise NotImplementedError

    def _parse_response(self, response: Buffer) -> tuple[RawQueryResponse, list[str]]:
        """Transform the connection object (the result) into dict which is passed to the QueryResponse constructor.

        :return: A tuple with two elements. First is `raw` answer and second is list of players.
        """
        _ = response.read(len("splitnum") + 3)
        data: dict[str, Any] = {}

        while True:
            key = response.read_ascii()
            if key == "hostname":  # hostname is actually motd in the query protocol
                match = re.search(
                    b"(.*?)\x00(hostip|hostport|game_id|gametype|map|maxplayers|numplayers|plugins|version)",
                    bytes(response.unread_view()),
                    flags=re.DOTALL,
                )
                motd = match.group(1) if match else ""
                # Since the query protocol does not properly support unicode, the motd is still not resolved
                # correctly; however, this will avoid other parameter parsing errors.
                data[key] = response.read(len(motd)).decode("ISO-8859-1")
                _ = response.read(1)  # ignore null byte
            elif len(key) == 0:
                _ = response.read(1)
                break
            else:
                value = response.read_ascii()
                data[key] = value

        _ = response.read(len("player_") + 2)

        players_list: list[str] = []
        while True:
            player = response.read_ascii()
            if len(player) == 0:
                break
            players_list.append(player)

        return RawQueryResponse(**data), players_list


@final
@dataclass
class QueryClient(_BaseQueryClient):
    connection: UDPSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    @override
    def _read_packet(self) -> Buffer:
        packet = Buffer(self.connection.read(self.connection.remaining))
        _ = packet.read(1 + 4)
        return packet

    @override
    def handshake(self) -> None:
        self.connection.write(self._create_handshake_packet())

        packet = self._read_packet()
        self.challenge = int(packet.read_ascii())

    @override
    def read_query(self) -> QueryResponse:
        request = self._create_packet()
        self.connection.write(request)

        response = self._read_packet()
        return QueryResponse.build(*self._parse_response(response))


@final
@dataclass
class AsyncQueryClient(_BaseQueryClient):
    connection: UDPAsyncSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    @override
    async def _read_packet(self) -> Buffer:
        packet = Buffer(await self.connection.read(self.connection.remaining))
        _ = packet.read(1 + 4)
        return packet

    @override
    async def handshake(self) -> None:
        await self.connection.write(self._create_handshake_packet())

        packet = await self._read_packet()
        self.challenge = int(packet.read_ascii())

    @override
    async def read_query(self) -> QueryResponse:
        request = self._create_packet()
        await self.connection.write(request)

        response = await self._read_packet()
        return QueryResponse.build(*self._parse_response(response))
