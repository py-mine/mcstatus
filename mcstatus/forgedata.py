"""Forge Data Decoder

Forge mod data is encoded into a UTF-16 string that represents
binary data containing data like the forge mod loader network
version, a big list of channels that all the forge mods use,
and a list of mods the server has.

For more information see this file from forge itself:
https://github.com/MinecraftForge/MinecraftForge/blob/42115d37d6a46856e3dc914b54a1ce6d33b9872a/src/main/java/net/minecraftforge/network/ServerStatusPing.java"""

from __future__ import annotations

from typing import Final, NotRequired, TypedDict

from mcstatus.pinger import RawResponse
from mcstatus.protocol.connection import Connection

VERSION_FLAG_IGNORESERVERONLY: Final = 0b1
# IGNORESERVERONLY: Final = 'OHNOES\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31'  # noqa
IGNORESERVERONLY: Final = "<not required for client>"


class JavaForgeDataChannel(TypedDict):
    res: str
    """Channel name and id (ex. "fml:handshake")"""
    version: str
    """Channel version (ex. "1.2.3.4")"""
    required: bool
    """Is this channel required for client to join"""


class JavaForgeDataMod(TypedDict):
    modid: str
    """Mod ID"""
    modmarker: str
    """Mod marker"""


class RawJavaForgeData(TypedDict):
    fml_network_version: int
    channels: list[RawJavaForgeDataChannel]
    mods: list[RawJavaForgeDataMod]
    d: NotRequired[str]


def decode_optimized(string: str) -> Connection:
    """Decode buffer UTF-16 optimized binary data from `string`"""
    text = io.StringIO(string)

    def read() -> int:
        result = text.read(1)
        if not result:
            return 0
        return ord(result)

    size = read() | (read() << 15)

    buffer = Connection()
    value = 0
    bits = 0
    for _ in range(len(string) - 2):
        while bits >= 8:
            buffer.receive((value & 0xFF).to_bytes(length=1, byteorder="big", signed=False))
            value >>= 8
            bits -= 8
        value |= (read() & 0x7FFF) << bits
        bits += 15

    while buffer.remaining() < size:
        buffer.receive((value & 0xFF).to_bytes(length=1, byteorder="big", signed=False))
        value >>= 8
        bits -= 8
    return buffer


def decode_forge_data(response: RawResponse) -> dict[str, Any] | None:
    "Return decoded forgeData if present or None"
    data: dict[str, Any] = response

    if "forgeData" not in response:
        return None
    forge = response["forgeData"]
    if "d" not in response:
        return forge

    buffer = decode_optimized(forge["d"])

    channels: dict[tuple[str, str], tuple[str, bool]] = {}
    # channels: dict[str, tuple[str, bool]] = {}
    mods: dict[str, str] = {}

    try:
        truncated = buffer.read_bool()
        mod_size = buffer.read_ushort()
        for _ in range(mod_size):
            channel_version_flags = buffer.read_varint()

            channel_size = channel_version_flags >> 1
            is_server = channel_version_flags & VERSION_FLAG_IGNORESERVERONLY != 0
            mod_id = buffer.read_utf()

            mod_version = IGNORESERVERONLY
            if not is_server:
                mod_version = buffer.read_utf()

            for _ in range(channel_size):
                name = buffer.read_utf()
                version = buffer.read_utf()
                client_required = buffer.read_bool()
                channels[(mod_id, name)] = (version, client_required)

            mods[mod_id] = mod_version

        non_mod_channel_size = buffer.read_varint()
        for _ in range(non_mod_channel_size):
            mod_name, mod_id = buffer.read_utf().split(":", 1)
            channel_key: tuple[str, str] = mod_name, mod_id
            # name = buffer.read_utf()
            version = buffer.read_utf()
            client_required = buffer.read_bool()
            # channels[name] = (version, client_required)
            channels[channel_key] = (version, client_required)
    except Exception as ex:
        if not truncated:
            raise
        # Semi-expect errors if truncated

    new_forge = forge.update({"truncated": truncated, "mods": mods, "channels": channels})
    if "d" in new_forge:
        del new_forge["d"]
    return new_forge
