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

from dataclasses import dataclass
from io import StringIO
from typing import Final, TYPE_CHECKING

from mcstatus.protocol.connection import BaseConnection, BaseReadSync, Connection

VERSION_FLAG_IGNORE_SERVER_ONLY: Final = 0b1
IGNORE_SERVER_ONLY: Final = "<not required for client>"


if TYPE_CHECKING:
    from typing_extensions import Self, TypedDict

    class RawForgeDataChannel(TypedDict):
        res: str
        """Channel name and ID (for example ``fml:handshake``)."""
        version: str
        """Channel version (for example ``1.2.3.4``)."""
        required: bool
        """Is this channel required for client to join?"""

    class RawForgeDataMod(TypedDict, total=False):
        modid: str
        modId: str
        modmarker: str
        """Mod version."""
        version: str

    class RawForgeData(TypedDict, total=False):
        fmlNetworkVersion: int
        channels: list[RawForgeDataChannel]
        mods: list[RawForgeDataMod]
        modList: list[RawForgeDataMod]
        d: str
        truncated: bool

else:
    RawForgeDataChannel = dict
    RawForgeDataMod = dict
    RawForgeData = dict


@dataclass(frozen=True)
class ForgeDataChannel:
    name: str
    """Channel name and ID (for example ``fml:handshake``)."""
    version: str
    """Channel version (for example ``1.2.3.4``)."""
    required: bool
    """Is this channel required for client to join?"""

    @classmethod
    def build(cls, raw: RawForgeDataChannel) -> Self:
        """Build an object about Forge channel from raw response.

        :param raw: ``channel`` element in raw forge response :class:`dict`.
        :return: :class:`ForgeDataChannel` object.
        """
        return cls(name=raw["res"], version=raw["version"], required=raw["required"])

    @classmethod
    def decode(cls, buffer: Connection, mod_id: str | None = None) -> Self:
        """Decode an object about Forge channel from decoded optimized buffer.

        :param buffer: :class:`Connection` object from UTF-16 encoded binary data.
        :param mod_id: Optional mod id prefix :class:`str`.
        :return: :class:`ForgeDataChannel` object.
        """
        channel_identifier = buffer.read_utf()
        if mod_id is not None:
            channel_identifier = f"{mod_id}:{channel_identifier}"
        version = buffer.read_utf()
        client_required = buffer.read_bool()

        return cls(
            name=channel_identifier,
            version=version,
            required=client_required,
        )


@dataclass(frozen=True)
class ForgeDataMod:
    name: str
    marker: str

    @classmethod
    def build(cls, raw: RawForgeDataMod) -> Self:
        """Build an object about Forge mod from raw response.

        :param raw: ``mod`` element in raw forge response :class:`dict`.
        :return: :class:`ForgeDataMod` object.
        """
        # In FML v1, modmarker was version instead.
        mod_version = raw.get("modmarker") or raw.get("version")
        if mod_version is None:
            raise KeyError("Mod version in Forge mod data must be provided.")

        # In FML v2, modid was modId instead. At least one of the two should exist.
        mod_id = raw.get("modid") or raw.get("modId")
        if mod_id is None:
            raise KeyError(f"Mod ID in Forge mod data must be provided. Mod version: {mod_version!r}.")

        return cls(name=mod_id, marker=mod_version)

    @classmethod
    def decode(cls, buffer: Connection) -> tuple[Self, list[ForgeDataChannel]]:
        """Decode data about a Forge mod from decoded optimized buffer.

        :param buffer: :class:`Connection` object from UTF-16 encoded binary data.
        :return: :class:`tuple` object of :class:`ForgeDataMod` object and :class:`list` of :class:`ForgeDataChannel` objects.
        """
        channel_version_flags = buffer.read_varint()

        channel_count = channel_version_flags >> 1
        is_server = channel_version_flags & VERSION_FLAG_IGNORE_SERVER_ONLY != 0
        mod_id = buffer.read_utf()

        mod_version = IGNORE_SERVER_ONLY
        if not is_server:
            mod_version = buffer.read_utf()

        channels: list[ForgeDataChannel] = []
        for _ in range(channel_count):
            channels.append(ForgeDataChannel.decode(buffer, mod_id))

        return cls(name=mod_id, marker=mod_version), channels


class StringBuffer(BaseReadSync, BaseConnection):
    """String Buffer for reading utf-16 encoded binary data."""

    __slots__ = ("received", "stringio")

    def __init__(self, stringio: StringIO) -> None:
        self.stringio = stringio
        self.received = bytearray()

    def read(self, length: int) -> bytearray:
        """Read length bytes from ``self``, and return a byte array."""
        data = bytearray()
        while self.received and len(data) < length:
            data.append(self.received.pop(0))
        while len(data) < length:
            result = self.stringio.read(1)
            if not result:
                raise IOError(f"Not enough data to read! {len(data)} < {length}")
            data.extend(result.encode("utf-16be"))
        while len(data) > length:
            self.received.append(data.pop())
        return data

    def remaining(self) -> int:
        """Return number of reads remaining."""
        return len(self.stringio.getvalue()) - self.stringio.tell() + len(self.received)

    def read_optimized_size(self) -> int:
        """Read encoded data length."""
        return self.read_short() | (self.read_short() << 15)

    def read_optimized_buffer(self) -> Connection:
        """Read encoded buffer."""
        size = self.read_optimized_size()

        buffer = Connection()
        value, bits = 0, 0
        while buffer.remaining() < size:
            if bits < 8 and self.remaining():
                # Ignoring sign bit
                value |= (self.read_short() & 0x7FFF) << bits
                bits += 15
            buffer.receive((value & 0xFF).to_bytes(1, "big"))
            value >>= 8
            bits -= 8

        return buffer


@dataclass(frozen=True)
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
        with StringIO(string) as text:
            str_buffer = StringBuffer(text)
            return str_buffer.read_optimized_buffer()

    @classmethod
    def build(cls, raw: RawForgeData) -> Self | None:
        """Build an object about Forge mods from raw response.

        :param raw: ``forgeData`` attribute in raw response :class:`dict`.
        :return: :class:`ForgeData` object.
        """
        fml_network_version = raw.get("fmlNetworkVersion", 1)

        # see https://github.com/MinecraftForge/MinecraftForge/blob/7d0330eb08299935714e34ac651a293e2609aa86/src/main/java/net/minecraftforge/network/ServerStatusPing.java#L27-L73  # noqa: E501  # line too long
        if "d" not in raw:
            mod_list = raw.get("mods") or raw.get("modList")
            if mod_list is None:
                raise KeyError("Neither `mods` or `modList` keys exist.")

            return cls(
                fml_network_version=fml_network_version,
                channels=[ForgeDataChannel.build(channel) for channel in raw.get("channels", ())],
                mods=[ForgeDataMod.build(mod) for mod in mod_list],
                truncated=False,
            )

        buffer = cls._decode_optimized(raw["d"])

        channels: list[ForgeDataChannel] = []
        mods: list[ForgeDataMod] = []

        truncated = buffer.read_bool()
        mod_count = buffer.read_ushort()
        try:
            for _ in range(mod_count):
                mod, mod_channels = ForgeDataMod.decode(buffer)

                channels.extend(mod_channels)
                mods.append(mod)

            non_mod_channel_count = buffer.read_varint()
            for _ in range(non_mod_channel_count):
                channels.append(ForgeDataChannel.decode(buffer))
        except IOError:
            if not truncated:
                raise  # If answer wasn't truncated, we lost some data on the way

        return cls(
            fml_network_version=fml_network_version,
            channels=channels,
            mods=mods,
            truncated=truncated,
        )
