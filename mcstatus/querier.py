from __future__ import annotations

import random
import re
import struct
from abc import abstractmethod
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import ClassVar, final

from mcstatus.protocol.connection import Connection, UDPAsyncSocketConnection, UDPSocketConnection
from mcstatus.responses import QueryResponse, RawQueryResponse


@dataclass
class _BaseServerQuerier:
    MAGIC_PREFIX: ClassVar = bytearray.fromhex("FEFD")
    PADDING: ClassVar = bytearray.fromhex("00000000")
    PACKET_TYPE_CHALLENGE: ClassVar = 9
    PACKET_TYPE_QUERY: ClassVar = 0

    connection: UDPSocketConnection | UDPAsyncSocketConnection
    challenge: int = field(init=False, default=0)

    @staticmethod
    def _generate_session_id() -> int:
        # minecraft only supports lower 4 bits
        return random.randint(0, 2**31) & 0x0F0F0F0F

    def _create_packet(self) -> Connection:
        packet = Connection()
        packet.write(self.MAGIC_PREFIX)
        packet.write(struct.pack("!B", self.PACKET_TYPE_QUERY))
        packet.write_uint(self._generate_session_id())
        packet.write_int(self.challenge)
        packet.write(self.PADDING)
        return packet

    def _create_handshake_packet(self) -> Connection:
        packet = Connection()
        packet.write(self.MAGIC_PREFIX)
        packet.write(struct.pack("!B", self.PACKET_TYPE_CHALLENGE))
        packet.write_uint(self._generate_session_id())
        return packet

    @abstractmethod
    def _read_packet(self) -> Connection | Awaitable[Connection]:
        raise NotImplementedError

    @abstractmethod
    def handshake(self) -> None | Awaitable[None]:
        raise NotImplementedError

    @abstractmethod
    def read_query(self) -> QueryResponse | Awaitable[QueryResponse]:
        raise NotImplementedError

    def _parse_response(self, response: Connection) -> tuple[RawQueryResponse, list[str]]:
        """Transform the connection object (the result) into dict which is passed to the QueryResponse constructor.

        :return: A tuple with two elements. First is `raw` answer and second is list of players.
        """
        response.read(len("splitnum") + 3)
        data = {}

        while True:
            key = response.read_ascii()
            if key == "hostname":  # hostname is actually motd in the query protocol
                match = re.search(
                    b"(.*?)\x00(hostip|hostport|game_id|gametype|map|maxplayers|numplayers|plugins|version)",
                    response.received,
                    flags=re.DOTALL,
                )
                motd = match.group(1) if match else ""
                # Since the query protocol does not properly support unicode, the motd is still not resolved
                # correctly; however, this will avoid other parameter parsing errors.
                data[key] = response.read(len(motd)).decode("ISO-8859-1")
                response.read(1)  # ignore null byte
            elif len(key) == 0:
                response.read(1)
                break
            else:
                value = response.read_ascii()
                data[key] = value

        response.read(len("player_") + 2)

        players_list = []
        while True:
            player = response.read_ascii()
            if len(player) == 0:
                break
            players_list.append(player)

        return RawQueryResponse(**data), players_list


@final
@dataclass
class ServerQuerier(_BaseServerQuerier):
    connection: UDPSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    def _read_packet(self) -> Connection:
        packet = Connection()
        packet.receive(self.connection.read(self.connection.remaining()))
        packet.read(1 + 4)
        return packet

    def handshake(self) -> None:
        self.connection.write(self._create_handshake_packet())

        packet = self._read_packet()
        self.challenge = int(packet.read_ascii())

    def read_query(self) -> QueryResponse:
        request = self._create_packet()
        self.connection.write(request)

        response = self._read_packet()
        return QueryResponse.build(*self._parse_response(response))


@final
@dataclass
class AsyncServerQuerier(_BaseServerQuerier):
    connection: UDPAsyncSocketConnection  # pyright: ignore[reportIncompatibleVariableOverride]

    async def _read_packet(self) -> Connection:
        packet = Connection()
        packet.receive(await self.connection.read(self.connection.remaining()))
        packet.read(1 + 4)
        return packet

    async def handshake(self) -> None:
        await self.connection.write(self._create_handshake_packet())

        packet = await self._read_packet()
        self.challenge = int(packet.read_ascii())

    async def read_query(self) -> QueryResponse:
        request = self._create_packet()
        await self.connection.write(request)

        response = await self._read_packet()
        return QueryResponse.build(*self._parse_response(response))
