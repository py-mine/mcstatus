from __future__ import annotations

from typing import Literal, TYPE_CHECKING, TypeAlias, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired

__all__ = [
    "RawForgeData",
    "RawForgeDataChannel",
    "RawForgeDataMod",
    "RawJavaResponse",
    "RawJavaResponseMotd",
    "RawJavaResponseMotdWhenDict",
    "RawJavaResponsePlayer",
    "RawJavaResponsePlayers",
    "RawJavaResponseVersion",
    "RawQueryResponse",
]

RawJavaResponseMotd: TypeAlias = "RawJavaResponseMotdWhenDict | list[RawJavaResponseMotdWhenDict | str] | str"


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


class RawJavaResponsePlayer(TypedDict):
    name: str
    id: str


class RawJavaResponsePlayers(TypedDict):
    online: int
    max: int
    sample: NotRequired[list[RawJavaResponsePlayer] | None]


class RawJavaResponseVersion(TypedDict):
    name: str
    protocol: int


class RawJavaResponseMotdWhenDict(TypedDict, total=False):
    text: str  # only present if `translate` is set
    translate: str  # same to the above field
    extra: list[RawJavaResponseMotdWhenDict | str]

    color: str
    bold: bool
    strikethrough: bool
    italic: bool
    underlined: bool
    obfuscated: bool


class RawJavaResponse(TypedDict):
    description: RawJavaResponseMotd
    players: RawJavaResponsePlayers
    version: RawJavaResponseVersion
    favicon: NotRequired[str]
    forgeData: NotRequired[RawForgeData | None]
    modinfo: NotRequired[RawForgeData | None]
    enforcesSecureChat: NotRequired[bool]


class RawQueryResponse(TypedDict):
    hostname: str
    gametype: Literal["SMP"]
    game_id: Literal["MINECRAFT"]
    version: str
    plugins: str
    map: str
    numplayers: str  # can be transformed into `int`
    maxplayers: str  # can be transformed into `int`
    hostport: str  # can be transformed into `int`
    hostip: str
