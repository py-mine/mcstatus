"""Decoder for data from Forge, that is included into a response object.

After 1.18.1, Forge started to compress its mod data into a
UTF-16 string that represents binary data containing data like
the forge mod loader network version, a big list of channels
that all the forge mods use, and a list of mods the server has.

Before 1.18.1, the mod data was in `forgeData` attribute inside
a response object. We support this implementation too.

For more information see this file from forge itself:
https://github.com/MinecraftForge/MinecraftForge/blob/54b08d2711a15418130694342a3fe9a5dfe005d2/src/main/java/net/minecraftforge/network/ServerStatusPing.java#L27-L73
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Final, TYPE_CHECKING

from mcstatus.protocol.connection import Connection

VERSION_FLAG_IGNORE_SERVER_ONLY: Final = 0b1
IGNORE_SERVER_ONLY: Final = "<not required for client>"


if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, TypedDict

    class RawForgeDataChannel(TypedDict):
        res: str
        """Channel name and ID (for example ``fml:handshake``)."""
        version: str
        """Channel version (for example ``1.2.3.4``)."""
        required: bool
        """Is this channel required for client to join?"""

    class RawForgeDataMod(TypedDict):
        modid: str
        modmarker: str
        """Mod version."""

    class RawForgeData(TypedDict):
        fmlNetworkVersion: int  # noqa: N815 # camel case
        channels: list[RawForgeDataChannel]
        mods: list[RawForgeDataMod]
        d: NotRequired[str]
        truncated: NotRequired[bool]

else:
    RawForgeDataChannel = dict
    RawForgeDataMod = dict
    RawForgeData = dict


@dataclass
class ForgeDataChannel:
    res: str
    """Channel name and ID (for example ``fml:handshake``)."""
    version: str
    """Channel version (for example ``1.2.3.4``)."""
    required: bool
    """Is this channel required for client to join?"""

    @classmethod
    def build(cls, raw: RawForgeDataChannel) -> Self:
        """Build an object about Forge channel from raw response.

        :param raw: ``forgeData`` attribute in raw response :class:`dict`.
        :return: :class:`ForgeDataChannel` object.
        """
        return cls(res=raw["res"], version=raw["version"], required=raw["required"])


@dataclass
class ForgeDataMod:
    modid: str
    modmarker: str
    """Mod version."""

    @classmethod
    def build(cls, raw: RawForgeDataMod) -> Self:
        """Build an object about Forge mod from raw response.

        :param raw: ``forgeData`` attribute in raw response :class:`dict`.
        :return: :class:`ForgeDataMod` object.
        """
        return cls(modid=raw["modid"], modmarker=raw["modmarker"])


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

    @staticmethod
    def _decode_optimized(string: str) -> Connection:
        """Decode buffer from UTF-16 optimized binary data ``string``."""
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

    @classmethod
    def build(cls, raw: RawForgeData) -> Self:
        """Build an object about Forge mods from raw response.

        :param raw: ``forgeData`` attribute in raw response :class:`dict`.
        :return: :class:`ForgeData` object.
        """
        fml_network_version = raw["fmlNetworkVersion"]
        # Decode the encoded forge data if it exists.

        # see https://github.com/MinecraftForge/MinecraftForge/blob/7d0330eb08299935714e34ac651a293e2609aa86/src/main/java/net/minecraftforge/network/ServerStatusPing.java#L27-L73  # noqa: E501  # line too long
        if "d" not in raw:
            return cls(
                fml_network_version=fml_network_version,
                channels=[ForgeDataChannel.build(channel) for channel in raw["channels"]],
                mods=[ForgeDataMod.build(mod) for mod in raw["mods"]],
                truncated=False,
            )

        buffer = cls._decode_optimized(raw["d"])

        channels: list[ForgeDataChannel] = []
        mods: list[ForgeDataMod] = []

        truncated = buffer.read_bool()
        mod_count = buffer.read_ushort()
        try:
            for _ in range(mod_count):
                channel_version_flags = buffer.read_varint()

                channel_count = channel_version_flags >> 1
                is_server = channel_version_flags & VERSION_FLAG_IGNORE_SERVER_ONLY != 0
                mod_id = buffer.read_utf()

                mod_version = IGNORE_SERVER_ONLY
                if not is_server:
                    mod_version = buffer.read_utf()

                for _ in range(channel_count):
                    name = buffer.read_utf()
                    version = buffer.read_utf()
                    client_required = buffer.read_bool()
                    channels.append(
                        ForgeDataChannel(
                            res=f"{mod_id}:{name}",
                            version=version,
                            required=client_required,
                        )
                    )

                mods.append(
                    ForgeDataMod(
                        modid=mod_id,
                        modmarker=mod_version,
                    )
                )

            non_mod_channel_count = buffer.read_varint()
            for _ in range(non_mod_channel_count):
                channel_identifier = buffer.read_utf()
                version = buffer.read_utf()
                client_required = buffer.read_bool()
                channels.append(
                    ForgeDataChannel(
                        res=channel_identifier,
                        version=version,
                        required=client_required,
                    )
                )
        except IOError:
            if not truncated:
                raise
            # Semi-expect errors if truncated, we are missing data

        return cls(
            fml_network_version=fml_network_version,
            channels=channels,
            mods=mods,
            truncated=truncated,
        )
