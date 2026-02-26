from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mcstatus.motd import Motd
from mcstatus.responses.base import BaseStatusPlayers, BaseStatusResponse, BaseStatusVersion

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = [
    "LegacyStatusPlayers",
    "LegacyStatusResponse",
    "LegacyStatusVersion",
]


@dataclass(frozen=True)
class LegacyStatusResponse(BaseStatusResponse):
    """The response object for :meth:`LegacyServerStatus.status() <mcstatus.server.LegacyServer.status>`."""

    players: LegacyStatusPlayers
    version: LegacyStatusVersion
    """The version information, only populates for servers >=12w42b (1.4 onwards)."""

    @classmethod
    def build(cls, decoded_data: list[str], latency: float) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param decoded_data: Raw decoded response object.
        :param latency: Latency of the request.
        :return: :class:`LegacyStatusResponse` object.
        """
        return cls(
            players=LegacyStatusPlayers(
                online=int(decoded_data[3]),
                max=int(decoded_data[4]),
            ),
            version=LegacyStatusVersion(
                name=decoded_data[1],
                protocol=int(decoded_data[0]),
            ),
            motd=Motd.parse(decoded_data[2]),
            latency=latency,
        )


@dataclass(frozen=True)
class LegacyStatusPlayers(BaseStatusPlayers):
    """Class for storing information about players on the server."""


@dataclass(frozen=True)
class LegacyStatusVersion(BaseStatusVersion):
    """A class for storing version information."""

    name: str
    """The version name, like ``1.19.3``.

    See `Minecraft wiki <https://minecraft.wiki/w/Java_Edition_version_history>`__
    for complete list.

    Will be ``<1.4`` for older releases, as those did not send version
    information.
    """
    protocol: int
    """The protocol version, like ``761``.

    See `Minecraft wiki <https://minecraft.wiki/w/Protocol_version#Java_Edition_2>`__.

    ``-1`` means 1.3 and lower, before 1.4 servers did not send information
    about its version.
    """