"""Forge Data Decoder

Forge mod data is encoded into a UTF-16 string that represents
binary data containing data like the forge mod loader network
version, a big list of channels that all the forge mods use,
and a list of mods the server has.

For more information see this file from forge itself:
https://github.com/MinecraftForge/MinecraftForge/blob/42115d37d6a46856e3dc914b54a1ce6d33b9872a/src/main/java/net/minecraftforge/network/ServerStatusPing.java"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Final, TYPE_CHECKING

from mcstatus.protocol.connection import Connection

VERSION_FLAG_IGNORE_SERVER_ONLY: Final = 0b1
IGNORE_SERVER_ONLY: Final = "<not required for client>"


if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, TypeAlias, TypedDict

    class ForgeDataChannel(TypedDict):
        res: str
        """Channel name and ID (for example ``fml:handshake``)."""
        version: str
        """Channel version (for example ``1.2.3.4``)."""
        required: bool
        """Is this channel required for client to join?"""

    class ForgeDataMod(TypedDict):
        modid: str
        modmarker: str
        """Mod version"""

    class RawForgeData(TypedDict):
        fmlNetworkVersion: int
        channels: list[ForgeDataChannel]
        mods: list[ForgeDataMod]
        d: NotRequired[str]

else:
    ForgeDataChannel = dict
    ForgeDataMod = dict
    RawForgeData = dict


@dataclass
class ForgeData:
    fml_network_version: int
    """Forge Mod Loader network version."""
    channels: list[ForgeDataChannel]
    """List of channels, both for mods and non-mods."""
    mods: list[ForgeDataMod]
    """List of mods"""
    truncated: bool
    """Is the mods list and or channel list incomplete?"""

    @classmethod
    def build(cls, raw: RawForgeData) -> Self:
        """Build :class:`ForgeData` from raw response :class:`dict`.

        :param raw: Raw forge data response :class:`dict`.
        :return: :class:`ForgeData` object.
        """
        raw.setdefault("fmlNetworkVersion", 0)
        raw.setdefault("channels", [])
        raw.setdefault("mods", [])
        return decode_forge_data(raw)


def decode_optimized(string: str) -> Connection:
    """Decode buffer UTF-16 optimized binary data from `string`."""
    text = io.StringIO(string)

    def read() -> int:
        result = text.read(1)
        if not result:
            return 0
        return ord(result)

    size = read() | (read() << 15)

    buffer = Connection()
    value, bits = 0, 0
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


def decode_forge_data(response: RawForgeData) -> ForgeData:
    """Decode the encoded forge data if it exists."""

    if "d" not in response:
        return ForgeData(
            fml_network_version=response["fmlNetworkVersion"],
            channels=response["channels"],
            mods=response["mods"],
            truncated=False,
        )

    buffer = decode_optimized(response["d"])

    channels: list[ForgeDataChannel] = []
    mods: list[ForgeDataMod] = []

    truncated = buffer.read_bool()
    mod_size = buffer.read_ushort()
    try:
        for _ in range(mod_size):
            channel_version_flags = buffer.read_varint()

            channel_size = channel_version_flags >> 1
            is_server = channel_version_flags & VERSION_FLAG_IGNORE_SERVER_ONLY != 0
            mod_id = buffer.read_utf()

            mod_version = IGNORE_SERVER_ONLY
            if not is_server:
                mod_version = buffer.read_utf()

            for _ in range(channel_size):
                name = buffer.read_utf()
                version = buffer.read_utf()
                client_required = buffer.read_bool()
                channels.append(
                    ForgeDataChannel(
                        {
                            "res": f"{mod_id}:{name}",
                            "version": version,
                            "required": client_required,
                        }
                    )
                )

            mods.append(
                ForgeDataMod(
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
                ForgeDataChannel(
                    {
                        "res": channel_identifier,
                        "version": version,
                        "required": client_required,
                    }
                )
            )
    except IOError:
        if not truncated:
            raise
        # Semi-expect errors if truncated, we are missing data

    return ForgeData(
        fml_network_version=response["fmlNetworkVersion"],
        channels=channels,
        mods=mods,
        truncated=truncated,
    )
