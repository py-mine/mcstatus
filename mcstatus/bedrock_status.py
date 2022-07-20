from __future__ import annotations

import asyncio
import socket
import struct
from time import perf_counter

import asyncio_dgram

from mcstatus.address import Address
from mcstatus.status_response import BedrockStatusResponse


class BedrockServerStatus:
    request_status_data = b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x124Vx"

    def __init__(self, address: Address, timeout: float = 3):
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

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)

        s.sendto(self.request_status_data, self.address)
        data, _ = s.recvfrom(2048)

        return self.parse_response(data, (perf_counter() - start))

    async def read_status_async(self) -> BedrockStatusResponse:
        start = perf_counter()
        stream = None

        try:
            conn = asyncio_dgram.connect(self.address)
            stream = await asyncio.wait_for(conn, timeout=self.timeout)

            await asyncio.wait_for(stream.send(self.request_status_data), timeout=self.timeout)
            data, _ = await asyncio.wait_for(stream.recv(), timeout=self.timeout)
        finally:
            if stream is not None:
                stream.close()

        return self.parse_response(data, (perf_counter() - start))
