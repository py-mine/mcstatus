from time import perf_counter

from mcstatus.protocol.connection import BaseAsyncReadSyncWriteConnection, BaseSyncConnection
from mcstatus.responses import LegacyStatusResponse


class _BaseLegacyServerStatus:
    request_status_data = bytes.fromhex(
        # see https://minecraft.wiki/w/Java_Edition_protocol/Server_List_Ping#Client_to_server
        "fe01fa"
    )

    @staticmethod
    def parse_response(data: bytes, latency: float) -> LegacyStatusResponse:
        decoded_data = data.decode("UTF-16BE").split("\0")
        if decoded_data[0] != "§1":
            raise IOError("Recieved invalid kick packet reason")

        return LegacyStatusResponse.build(decoded_data[1:], latency)


class LegacyServerStatus(_BaseLegacyServerStatus):
    def __init__(self, connection: BaseSyncConnection):
        self.connection = connection

    def read_status(self) -> LegacyStatusResponse:
        """Send the status request and read the response."""
        start = perf_counter()
        self.connection.write(self.request_status_data)
        id = self.connection.read(1)
        if id != b"\xff":
            raise IOError("Received invalid packet ID")
        length = self.connection.read_ushort()
        data = self.connection.read(length * 2)
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)


class AsyncLegacyServerStatus(_BaseLegacyServerStatus):
    def __init__(self, connection: BaseAsyncReadSyncWriteConnection):
        self.connection = connection

    async def read_status(self) -> LegacyStatusResponse:
        """Send the status request and read the response."""
        start = perf_counter()
        self.connection.write(self.request_status_data)
        id = await self.connection.read(1)
        if id != b"\xff":
            raise IOError("Received invalid packet ID")
        length = await self.connection.read_ushort()
        data = await self.connection.read(length * 2)
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)
