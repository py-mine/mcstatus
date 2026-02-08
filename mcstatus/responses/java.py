from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mcstatus.motd import Motd
from mcstatus.responses.base import BaseStatusPlayers, BaseStatusResponse, BaseStatusVersion
from mcstatus.responses.forge import ForgeData

if TYPE_CHECKING:
    from typing_extensions import Self

    from mcstatus.responses._raw import RawJavaResponse, RawJavaResponsePlayer, RawJavaResponsePlayers, RawJavaResponseVersion

__all__ = [
    "JavaStatusPlayer",
    "JavaStatusPlayers",
    "JavaStatusResponse",
    "JavaStatusVersion",
]


@dataclass(frozen=True)
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
    forge_data: ForgeData | None
    """Forge mod data (mod list, channels, etc). Only present if this is a forge (modded) server."""

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
        forge_data: ForgeData | None = None
        if (raw_forge := raw.get("forgeData") or raw.get("modinfo")) and raw_forge is not None:
            forge_data = ForgeData.build(raw_forge)

        return cls(
            raw=raw,
            players=JavaStatusPlayers.build(raw["players"]),
            version=JavaStatusVersion.build(raw["version"]),
            motd=Motd.parse(raw.get("description", ""), bedrock=False),
            enforces_secure_chat=raw.get("enforcesSecureChat"),
            icon=raw.get("favicon"),
            latency=latency,
            forge_data=forge_data,
        )


@dataclass(frozen=True)
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
        if (sample := raw.get("sample")) is not None:
            sample = [JavaStatusPlayer.build(player) for player in sample]
        return cls(
            online=raw["online"],
            max=raw["max"],
            sample=sample,
        )


@dataclass(frozen=True)
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


@dataclass(frozen=True)
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
