from __future__ import annotations

import asyncio
import socket
import struct
from time import perf_counter

import asyncio_dgram

from mcstatus.address import Address


class BedrockServerStatus:
    request_status_data = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx"

    def __init__(self, address: Address, timeout: float = 3):
        self.address = address
        self.timeout = timeout

    @staticmethod
    def parse_response(data: bytes, latency: float) -> "BedrockStatusResponse":
        data = data[1:]
        name_length = struct.unpack(">H", data[32:34])[0]
        decoded_data = data[34 : 34 + name_length].decode().split(";")

        try:
            map_ = decoded_data[7]
        except IndexError:
            map_ = None
        try:
            gamemode = decoded_data[8]
        except IndexError:
            gamemode = None

        return BedrockStatusResponse(
            protocol=int(decoded_data[2]),
            brand=decoded_data[0],
            version=decoded_data[3],
            latency=latency,
            players_online=int(decoded_data[4]),
            players_max=int(decoded_data[5]),
            motd=decoded_data[1],
            map_=map_,
            gamemode=gamemode,
        )

    def read_status(self) -> BedrockStatusResponse:
        start = perf_counter()
        data = self._read_status()
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)

    def _read_status(self) -> bytes:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)

        s.sendto(self.request_status_data, self.address)
        data, _ = s.recvfrom(2048)

        return data

    async def read_status_async(self) -> BedrockStatusResponse:
        start = perf_counter()
        data = await self._read_status_async()
        end = perf_counter()

        return self.parse_response(data, (end - start) * 1000)

    async def _read_status_async(self) -> bytes:
        stream = None
        try:
            conn = asyncio_dgram.connect(self.address)
            stream = await asyncio.wait_for(conn, timeout=self.timeout)

            await asyncio.wait_for(stream.send(self.request_status_data), timeout=self.timeout)
            data, _ = await asyncio.wait_for(stream.recv(), timeout=self.timeout)
        finally:
            if stream is not None:
                stream.close()

        return data


class BedrockStatusResponse:
    class Version:
        def __init__(self, protocol: int, brand: str, version: str):
            self.protocol = protocol
            self.brand = brand
            self.version = version

    def __init__(
        self,
        protocol: int,
        brand: str,
        version: str,
        latency: float,
        players_online: int,
        players_max: int,
        motd: str,
        map_: str | None,
        gamemode: str | None,
    ):
        self.version = self.Version(protocol, brand, version)
        self.latency = latency
        self.players_online = players_online
        self.players_max = players_max
        self.motd = motd
        self.map = map_
        self.gamemode = gamemode
