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
        :return: :class:LegacyStatusResponse object.
        """
        return cls(
            players=LegacyStatusPlayers(
                online=int(decoded_data[3]),
                max=int(decoded_data[4]),
            ),
            version=LegacyStatusVersion(
                name=decoded_data[1],
                protocol=tryint(decoded_data[0]),
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


def tryint(protocol: str) -> str | int:
    """Checks if the input string contains only digits and then, if True
    converts the string to an int. This allows the protocol value to be
    an int for servers running >=12w42b, and a str for servers running
    <=12w42a.
    """
    if protocol.isdigit():
        return int(protocol)
    return protocol