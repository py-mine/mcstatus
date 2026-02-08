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
