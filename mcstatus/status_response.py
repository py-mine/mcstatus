from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from mcstatus.motd import Motd

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, TypeAlias, TypedDict

    class RawJavaResponsePlayer(TypedDict):
        name: str
        id: str

    class RawJavaResponsePlayers(TypedDict):
        online: int
        max: int
        sample: NotRequired[list[RawJavaResponsePlayer]]

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

    RawJavaResponseMotd: TypeAlias = "RawJavaResponseMotdWhenDict | list[RawJavaResponseMotdWhenDict | str] | str"

    class RawJavaResponse(TypedDict):
        description: RawJavaResponseMotd
        players: RawJavaResponsePlayers
        version: RawJavaResponseVersion
        favicon: NotRequired[str]

else:
    RawJavaResponsePlayer = dict
    RawJavaResponsePlayers = dict
    RawJavaResponseVersion = dict
    RawJavaResponseMotdWhenDict = dict
    RawJavaResponse = dict

from mcstatus.utils import deprecated

__all__ = [
    "BaseStatusPlayers",
    "BaseStatusResponse",
    "BaseStatusVersion",
    "BedrockStatusPlayers",
    "BedrockStatusResponse",
    "BedrockStatusVersion",
    "JavaStatusPlayer",
    "JavaStatusPlayers",
    "JavaStatusResponse",
    "JavaStatusVersion",
]


@dataclass
class BaseStatusResponse(ABC):
    """Class for storing shared data from a status response."""

    players: BaseStatusPlayers
    """The players information."""
    version: BaseStatusVersion
    """The version information."""
    motd: Motd
    """Message Of The Day. Also known as description.

    .. seealso:: :doc:`/api/motd_parsing`.
    """
    latency: float
    """Latency between a server and the client (you). In milliseconds."""

    @property
    def description(self) -> str:
        """Alias to the :meth:`mcstatus.motd.Motd.to_minecraft` method."""
        return self.motd.to_minecraft()

    @classmethod
    @abstractmethod
    def build(cls, *args, **kwargs) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param args: Arguments in specific realisation.
        :param kwargs: Keyword arguments in specific realisation.
        :return: :class:`BaseStatusResponse` object.
        """
        raise NotImplementedError("You can't use abstract methods.")


@dataclass
class JavaStatusResponse(BaseStatusResponse):
    """The response object for :meth:`JavaServer.status() <mcstatus.server.JavaServer.status>`."""

    raw: RawJavaResponse
    """Raw response from the server.

    This is :class:`~typing.TypedDict` actually, please see sources to find what is here.
    """
    players: JavaStatusPlayers
    version: JavaStatusVersion
    enforces_secure_chat: bool | None
    """Whether the server enforces secure chat (every message is signed up with a key).

    .. seealso::
        `Signed Chat explanation <https://gist.github.com/kennytv/ed783dd244ca0321bbd882c347892874>`_,
        `22w17a changelog, where this was added <https://www.minecraft.net/nl-nl/article/minecraft-snapshot-22w17a>`_.

    .. versionadded:: 11.1.0
    """
    icon: str | None
    """The icon of the server. In `Base64 <https://en.wikipedia.org/wiki/Base64>`_ encoded PNG image format.

    .. seealso:: :ref:`pages/faq:how to get server image?`
    """

    @classmethod
    def build(cls, raw: RawJavaResponse, latency: float = 0) -> Self:
        """Build JavaStatusResponse and check is it valid.

        :param raw: Raw response :class:`dict`.
        :param latency: Time that server took to response (in milliseconds).
        :raise ValueError: If the required keys (``players``, ``version``, ``description``) are not present.
        :raise TypeError:
            If the required keys (``players`` - :class:`dict`, ``version`` - :class:`dict`,
            ``description`` - :class:`str`) are not of the expected type.
        :return: :class:`JavaStatusResponse` object.
        """
        return cls(
            raw=raw,
            players=JavaStatusPlayers.build(raw["players"]),
            version=JavaStatusVersion.build(raw["version"]),
            motd=Motd.parse(raw["description"], bedrock=False),
            enforces_secure_chat=raw.get("enforcesSecureChat"),
            icon=raw.get("favicon"),
            latency=latency,
        )

    @property
    @deprecated(replacement="icon", date="2023-12")
    def favicon(self) -> str | None:
        """
        .. deprecated:: 11.0.0
            Will be removed 2023-12, use :attr:`icon <JavaStatusResponse.icon>` instead.
        """
        return self.icon


@dataclass
class BedrockStatusResponse(BaseStatusResponse):
    """The response object for :meth:`BedrockServer.status() <mcstatus.server.BedrockServer.status>`."""

    players: BedrockStatusPlayers
    version: BedrockStatusVersion
    map_name: str | None
    """The name of the map."""
    gamemode: str | None
    """The name of the gamemode on the server."""

    @classmethod
    def build(cls, decoded_data: list[Any], latency: float) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param decoded_data: Raw decoded response object.
        :param latency: Latency of the request.
        :return: :class:`BedrockStatusResponse` object.
        """

        try:
            map_name = decoded_data[7]
        except IndexError:
            map_name = None
        try:
            gamemode = decoded_data[8]
        except IndexError:
            gamemode = None

        return cls(
            players=BedrockStatusPlayers(
                online=int(decoded_data[4]),
                max=int(decoded_data[5]),
            ),
            version=BedrockStatusVersion(
                name=decoded_data[3],
                protocol=int(decoded_data[2]),
                brand=decoded_data[0],
            ),
            motd=Motd.parse(decoded_data[1], bedrock=True),
            latency=latency,
            map_name=map_name,
            gamemode=gamemode,
        )

    @property
    @deprecated(replacement="players.online", date="2023-12")
    def players_online(self) -> int:
        """
        .. deprecated:: 11.0.0
            Will be removed 2023-12, use :attr:`players.online <BedrockStatusPlayers.online>` instead.
        """
        return self.players.online

    @property
    @deprecated(replacement="players.max", date="2023-12")
    def players_max(self) -> int:
        """
        .. deprecated:: 11.0.0
            Will be removed 2023-12, use :attr:`players.max <BedrockStatusPlayers.max>` instead.
        """
        return self.players.max

    @property
    @deprecated(replacement="map_name", date="2023-12")
    def map(self) -> str | None:
        """
        .. deprecated:: 11.0.0
            Will be removed 2023-12, use :attr:`.map_name` instead.
        """
        return self.map_name


@dataclass
class BaseStatusPlayers(ABC):
    """Class for storing information about players on the server."""

    online: int
    """Current number of online players."""
    max: int
    """The maximum allowed number of players (aka server slots)."""


@dataclass
class JavaStatusPlayers(BaseStatusPlayers):
    """Class for storing information about players on the server."""

    sample: list[JavaStatusPlayer] | None
    """List of players, who are online. If server didn't provide this, it will be :obj:`None`.

    Actually, this is what appears when you hover over the slot count on the multiplayer screen.

    .. note::
        It's often empty or even contains some advertisement, because the specific server implementations or plugins can
        disable providing this information or even change it to something custom.

        There is nothing that ``mcstatus`` can to do here if the player sample was modified/disabled like this.
    """

    @classmethod
    def build(cls, raw: RawJavaResponsePlayers) -> Self:
        """Build :class:`JavaStatusPlayers` from raw response :class:`dict`.

        :param raw: Raw response :class:`dict`.
        :raise ValueError: If the required keys (``online``, ``max``) are not present.
        :raise TypeError:
            If the required keys (``online`` - :class:`int`, ``max`` - :class:`int`,
            ``sample`` - :class:`list`) are not of the expected type.
        :return: :class:`JavaStatusPlayers` object.
        """
        sample = None
        if "sample" in raw:
            sample = [JavaStatusPlayer.build(player) for player in raw["sample"]]
        return cls(
            online=raw["online"],
            max=raw["max"],
            sample=sample,
        )


@dataclass
class BedrockStatusPlayers(BaseStatusPlayers):
    """Class for storing information about players on the server."""


@dataclass
class JavaStatusPlayer:
    """Class with information about a single player."""

    name: str
    """Name of the player."""
    id: str
    """ID of the player (in `UUID <https://en.wikipedia.org/wiki/Universally_unique_identifier>`_ format)."""

    @property
    def uuid(self) -> str:
        """Alias to :attr:`.id` field."""
        return self.id

    @classmethod
    def build(cls, raw: RawJavaResponsePlayer) -> Self:
        """Build :class:`JavaStatusPlayer` from raw response :class:`dict`.

        :param raw: Raw response :class:`dict`.
        :raise ValueError: If the required keys (``name``, ``id``) are not present.
        :raise TypeError: If the required keys (``name`` - :class:`str`, ``id`` - :class:`str`)
            are not of the expected type.
        :return: :class:`JavaStatusPlayer` object.
        """
        return cls(name=raw["name"], id=raw["id"])


@dataclass
class BaseStatusVersion(ABC):
    """A class for storing version information."""

    name: str
    """The version name, like ``1.19.3``.

    See `Minecraft wiki <https://minecraft.wiki/w/Java_Edition_version_history#Full_release>`__
    for complete list.
    """
    protocol: int
    """The protocol version, like ``761``.

    See `Minecraft wiki <https://minecraft.wiki/w/Protocol_version#Java_Edition_2>`__.
    """


@dataclass
class JavaStatusVersion(BaseStatusVersion):
    """A class for storing version information."""

    @classmethod
    def build(cls, raw: RawJavaResponseVersion) -> Self:
        """Build :class:`JavaStatusVersion` from raw response dict.

        :param raw: Raw response :class:`dict`.
        :raise ValueError: If the required keys (``name``, ``protocol``) are not present.
        :raise TypeError: If the required keys (``name`` - :class:`str`, ``protocol`` - :class:`int`)
            are not of the expected type.
        :return: :class:`JavaStatusVersion` object.
        """
        return cls(name=raw["name"], protocol=raw["protocol"])


@dataclass
class BedrockStatusVersion(BaseStatusVersion):
    """A class for storing version information."""

    name: str
    """The version name, like ``1.19.60``.

    See `Minecraft wiki <https://minecraft.wiki/w/Bedrock_Edition_version_history#Bedrock_Edition>`__
    for complete list.
    """
    brand: str
    """``MCPE`` or ``MCEE`` for Education Edition."""

    @property
    @deprecated(replacement="name", date="2023-12")
    def version(self) -> str:
        """
        .. deprecated:: 11.0.0
            Will be removed 2023-12, use :attr:`.name` instead.
        """
        return self.name
