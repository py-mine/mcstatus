from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, TYPE_CHECKING

from mcstatus._utils import deprecated
from mcstatus.motd import Motd

if TYPE_CHECKING:
    from typing_extensions import Self

    from mcstatus.responses._raw import RawQueryResponse

__all__ = [
    "QueryPlayers",
    "QueryResponse",
    "QuerySoftware",
]


@dataclass(frozen=True)
class QueryResponse:
    """The response object for :meth:`JavaServer.query() <mcstatus.server.JavaServer.query>`."""

    raw: RawQueryResponse
    """Raw response from the server.

    This is :class:`~typing.TypedDict` actually, please see sources to find what is here.
    """
    motd: Motd
    """The MOTD of the server. Also known as description.

    .. seealso:: :doc:`/api/motd_parsing`.
    """
    map_name: str
    """The name of the map. Default is ``world``."""
    players: QueryPlayers
    """The players information."""
    software: QuerySoftware
    """The software information."""
    ip: str
    """The IP address the server is listening/was contacted on."""
    port: int
    """The port the server is listening/was contacted on."""
    game_type: str = "SMP"
    """The game type of the server. Hardcoded to ``SMP`` (survival multiplayer)."""
    game_id: str = "MINECRAFT"
    """The game ID of the server. Hardcoded to ``MINECRAFT``."""

    @classmethod
    def build(cls, raw: RawQueryResponse, players_list: list[str]) -> Self:
        return cls(
            raw=raw,
            motd=Motd.parse(raw["hostname"], bedrock=False),
            map_name=raw["map"],
            players=QueryPlayers.build(raw, players_list),
            software=QuerySoftware.build(raw["version"], raw["plugins"]),
            ip=raw["hostip"],
            port=int(raw["hostport"]),
            game_type=raw["gametype"],
            game_id=raw["game_id"],
        )

    def as_dict(self) -> dict[str, Any]:
        """Return the dataclass as JSON-serializable :class:`dict`.

        Do note that this method doesn't return :class:`string <str>` but
        :class:`dict`, so you can do some processing on returned value.

        Difference from
        :attr:`~mcstatus.responses.JavaStatusResponse.raw` is in that,
        :attr:`~mcstatus.responses.JavaStatusResponse.raw` returns raw response
        in the same format as we got it. This method returns the response
        in a more user-friendly JSON serializable format (for example,
        :attr:`~mcstatus.responses.BaseStatusResponse.motd` is returned as a
        :func:`Minecraft string <mcstatus.motd.Motd.to_minecraft>` and not
        :class:`dict`).
        """
        as_dict = asdict(self)
        as_dict["motd"] = self.motd.simplify().to_minecraft()
        as_dict["players"] = asdict(self.players)
        as_dict["software"] = asdict(self.software)
        return as_dict

    @property
    @deprecated(replacement="map_name", removal_version="13.0.0")
    def map(self) -> str | None:
        """
        .. deprecated:: 12.0.0
            Will be removed in 13.0.0, use :attr:`.map_name` instead.
        """  # noqa: D205, D212 # no summary line
        return self.map_name


@dataclass(frozen=True)
class QueryPlayers:
    """Class for storing information about players on the server."""

    online: int
    """The number of online players."""
    max: int
    """The maximum allowed number of players (server slots)."""
    list: list[str]
    """The list of online players."""

    @classmethod
    def build(cls, raw: RawQueryResponse, players_list: list[str]) -> Self:
        return cls(
            online=int(raw["numplayers"]),
            max=int(raw["maxplayers"]),
            list=players_list,
        )

    @property
    @deprecated(replacement="'list' attribute", removal_version="13.0.0")
    def names(self) -> list[str]:
        """
        .. deprecated:: 12.0.0
            Will be removed in 13.0.0, use :attr:`.list` instead.
        """  # noqa: D205, D212 # no summary line
        return self.list


@dataclass(frozen=True)
class QuerySoftware:
    """Class for storing information about software on the server."""

    version: str
    """The version of the software."""
    brand: str
    """The brand of the software. Like `Paper <https://papermc.io>`_ or `Spigot <https://www.spigotmc.org>`_."""
    plugins: list[str]
    """The list of plugins. Can be an empty list if hidden."""

    @classmethod
    def build(cls, version: str, plugins: str) -> Self:
        brand, parsed_plugins = cls._parse_plugins(plugins)
        return cls(
            version=version,
            brand=brand,
            plugins=parsed_plugins,
        )

    @staticmethod
    def _parse_plugins(plugins: str) -> tuple[str, list[str]]:
        """Parse plugins string to list.

        Returns:
            :class:`tuple` with two elements. First is brand of server (:attr:`.brand`)
            and second is a list of :attr:`plugins`.
        """
        brand = "vanilla"
        parsed_plugins = []

        if plugins:
            parts = plugins.split(":", 1)
            brand = parts[0].strip()

            if len(parts) == 2:
                parsed_plugins = [s.strip() for s in parts[1].split(";")]

        return brand, parsed_plugins
