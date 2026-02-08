from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from mcstatus._utils import deprecated
from mcstatus.motd import Motd
from mcstatus.responses.base import BaseStatusPlayers, BaseStatusResponse, BaseStatusVersion

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = [
    "BedrockStatusPlayers",
    "BedrockStatusResponse",
    "BedrockStatusVersion",
]


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class BedrockStatusPlayers(BaseStatusPlayers):
    """Class for storing information about players on the server."""


@dataclass(frozen=True)
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
    @deprecated(replacement="name", removal_version="13.0.0")
    def version(self) -> str:
        """
        .. deprecated:: 12.0.0
            Will be removed in 13.0.0, use :attr:`.name` instead.
        """  # noqa: D205, D212 # no summary line
        return self.name
