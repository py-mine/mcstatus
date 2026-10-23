from __future__ import annotations

import asyncio
import socket
import struct
from time import perf_counter
from typing import ClassVar, TYPE_CHECKING, final

import asyncio_dgram

from mcstatus._utils import deprecation_warn
from mcstatus.responses import BedrockStatusResponse

if TYPE_CHECKING:
    from mcstatus._net.address import Address

__all__ = ["BedrockClient", "BedrockRakNetClient"]


class BedrockRakNetClient:
    address: Address
    timeout: float

    request_status_data: ClassVar[bytes] = bytes.fromhex(
        # see https://minecraft.wiki/w/RakNet#Unconnected_Ping
        "01" + "0000000000000000" + "00ffff00fefefefefdfdfdfd12345678" + "0000000000000000"
    )

    def __init__(self, address: Address, timeout: float = 3) -> None:
        self.address = address
        self.timeout = timeout

    @staticmethod
    def parse_response(data: bytes, latency: float) -> BedrockStatusResponse:
        data = data[1:]
        name_length = struct.unpack(">H", data[32:34])[0]
        decoded_data = data[34 : 34 + name_length].decode().split(";")

        return BedrockStatusResponse.build(decoded_data, latency)

    def read_status(self) -> BedrockStatusResponse:
        start = perf_counter()
        data = self._read_status()
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)

    def _read_status(self) -> bytes:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)

        _ = s.sendto(self.request_status_data, self.address)
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


@final
class BedrockClient(BedrockRakNetClient):
    """Deprecated alias for :class:`BedrockRakNetClient`.

    .. deprecated:: 14.3.0
        Use :class:`BedrockRakNetClient` instead. Scheduled for removal in 15.0.0.
    """

    def __init__(self, address: Address, timeout: float = 3) -> None:
        deprecation_warn(
            obj_name="mcstatus._protocol.bedrock_client.BedrockClient",
            removal_version="15.0.0",
            replacement="mcstatus._protocol.bedrock_raknet_client.BedrockRakNetClient",
        )
        super().__init__(address, timeout)
