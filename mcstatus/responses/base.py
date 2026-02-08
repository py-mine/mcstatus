from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

    from mcstatus.motd import Motd

__all__ = [
    "BaseStatusPlayers",
    "BaseStatusResponse",
    "BaseStatusVersion",
]


@dataclass(frozen=True)
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
    def build(cls, *args: Any, **kwargs: Any) -> Self:
        """Build BaseStatusResponse and check is it valid.

        :param args: Arguments in specific realisation.
        :param kwargs: Keyword arguments in specific realisation.
        :return: :class:`BaseStatusResponse` object.
        """
        raise NotImplementedError("You can't use abstract methods.")

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
        return as_dict


@dataclass(frozen=True)
class BaseStatusPlayers(ABC):
    """Class for storing information about players on the server."""

    online: int
    """Current number of online players."""
    max: int
    """The maximum allowed number of players (aka server slots)."""


@dataclass(frozen=True)
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
