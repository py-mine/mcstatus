from time import perf_counter

from mcstatus._protocol.io.base_io import StructFormat
from mcstatus._protocol.io.connection import BaseAsyncConnection, BaseSyncConnection
from mcstatus.responses import LegacyStatusResponse

__all__ = ["AsyncLegacyClient", "LegacyClient"]


class _BaseLegacyClient:
    request_status_data = bytes.fromhex(
        # see https://minecraft.wiki/w/Java_Edition_protocol/Server_List_Ping#Client_to_server
        "fe01fa"
    )

    @staticmethod
    def parse_response(data: bytes, latency: float) -> LegacyStatusResponse:
        decoded_data = data.decode("UTF-16BE").split("\0")
        if decoded_data[0] != "§1":
            # kick packets before 1.4 (12w42a) did not start with §1 and did
            # not included information about server and protocol version
            decoded_data = ["§1", -1, "<1.4", *decoded_data[0].split("§")]
            if len(decoded_data) != 6:
                raise OSError("Received invalid kick packet reason")
        return LegacyStatusResponse.build(decoded_data[1:], latency)


class LegacyClient(_BaseLegacyClient):
    def __init__(self, connection: BaseSyncConnection) -> None:
        self.connection = connection

    def read_status(self) -> LegacyStatusResponse:
        """Send the status request and read the response."""
        start = perf_counter()
        self.connection.write(self.request_status_data)
        id = self.connection.read(1)
        if id != b"\xff":
            raise OSError("Received invalid packet ID")
        length = self.connection.read_value(StructFormat.USHORT)
        data = self.connection.read(length * 2)
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)


class AsyncLegacyClient(_BaseLegacyClient):
    def __init__(self, connection: BaseAsyncConnection) -> None:
        self.connection = connection

    async def read_status(self) -> LegacyStatusResponse:
        """Send the status request and read the response."""
        start = perf_counter()
        await self.connection.write(self.request_status_data)
        id = await self.connection.read(1)
        if id != b"\xff":
            raise OSError("Received invalid packet ID")
        length = await self.connection.read_value(StructFormat.USHORT)
        data = await self.connection.read(length * 2)
        end = perf_counter()
        return self.parse_response(data, (end - start) * 1000)
