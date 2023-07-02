"""Forge Data Decoder

Forge mod data is encoded into a UTF-16 string that represents
binary data containing data like the forge mod loader network
version, a big list of channels that all the forge mods use,
and a list of mods the server has.

For more information see this file from forge itself:
https://github.com/MinecraftForge/MinecraftForge/blob/42115d37d6a46856e3dc914b54a1ce6d33b9872a/src/main/java/net/minecraftforge/network/ServerStatusPing.java"""  # noqa: E501

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Final, NotRequired, Self, TYPE_CHECKING, TypedDict

from mcstatus.protocol.connection import Connection

VERSION_FLAG_IGNORESERVERONLY: Final = 0b1
# IGNORESERVERONLY: Final = 'OHNOES\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31\uD83D\uDE31'  # noqa
IGNORESERVERONLY: Final = "<not required for client>"


if TYPE_CHECKING:

    class JavaForgeDataChannel(TypedDict):
        res: str
        """Channel name and ID (for example ``fml:handshake``)."""
        version: str
        """Channel version (for example ``1.2.3.4``)."""
        required: bool
        """Is this channel required for client to join?"""

    class JavaForgeDataMod(TypedDict):
        modid: str
        """Mod ID"""
        modmarker: str
        """Mod version"""

    class RawJavaForgeData(TypedDict):
        fmlNetworkVersion: int
        channels: list[JavaForgeDataChannel]
        mods: list[JavaForgeDataMod]
        d: NotRequired[str]

else:
    JavaForgeDataChannel = dict
    JavaForgeDataMod = dict
    RawJavaForgeData = dict


@dataclass
class JavaForgeData:
    fml_network_version: int
    """Forge Mod Loader network version"""
    channels: list[JavaForgeDataChannel]
    """List of channels, both for mods and non-mods"""
    mods: list[JavaForgeDataMod]
    """List of mods"""
    truncated: bool
    """Is the mods list and or channel list incomplete?"""

    @classmethod
    def build(cls, raw: RawJavaForgeData) -> Self:
        """Build :class:`JavaForgeData` from raw response :class:`dict`.

        :param raw: Raw forge data response :class:`dict`.
        :return: :class:`JavaForgeData` object.
        """
        raw.setdefault("fmlNetworkVersion", 0)
        raw.setdefault("channels", [])
        raw.setdefault("mods", [])
        return decode_forge_data(raw)


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


def decode_forge_data(response: RawJavaForgeData) -> JavaForgeData:
    "Return decoded forgeData if present or None"

    if "d" not in response:
        return JavaForgeData(
            fml_network_version=response["fmlNetworkVersion"],
            channels=response["channels"],
            mods=response["mods"],
            truncated=False,
        )

    buffer = decode_optimized(response["d"])

    channels: list[JavaForgeDataChannel] = []
    mods: list[JavaForgeDataMod] = []

    truncated = buffer.read_bool()
    mod_size = buffer.read_ushort()
    try:
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
                channels.append(
                    JavaForgeDataChannel(
                        {
                            "res": f"{mod_id}:{name}",
                            "version": version,
                            "required": client_required,
                        }
                    )
                )

            mods.append(
                JavaForgeDataMod(
                    {
                        "modid": mod_id,
                        "modmarker": mod_version,
                    }
                )
            )

        non_mod_channel_size = buffer.read_varint()
        for _ in range(non_mod_channel_size):
            channel_identifier = buffer.read_utf()
            version = buffer.read_utf()
            client_required = buffer.read_bool()
            channels.append(
                JavaForgeDataChannel(
                    {
                        "res": channel_identifier,
                        "version": version,
                        "required": client_required,
                    }
                )
            )
    except Exception:
        if not truncated:
            raise
        # Semi-expect errors if truncated

    return JavaForgeData(
        fml_network_version=response["fmlNetworkVersion"],
        channels=channels,
        mods=mods,
        truncated=truncated,
    )
