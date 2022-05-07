"""Module for storing `MCServerResponse` object."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

from mcstatus.bedrock_status import BedrockStatusResponse
from mcstatus.pinger import PingResponse


@dataclass
class AbstractDataclass(ABC):
    def __new__(cls, *args, **kwargs):
        if cls == AbstractDataclass or cls.__bases__[0] == AbstractDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)


@dataclass
class MCServerResponse(AbstractDataclass):
    """Dataclass for storing cross-platform status answer object."""

    players: ServerPlayers
    version: ServerVersion
    # Message Of The Day. Also known as `Description`.
    motd: str

    @classmethod
    @abstractmethod
    def build(cls, answer: Union[PingResponse, BedrockStatusResponse]) -> MCServerResponse:
        """Build MCServerResponse object from `PingResponse` or `BedrockStatusResponse`.

        :param answer: Answer from Minecraft server.
        :return: `MCServerResponse` object.
        """


@dataclass
class JavaServerResponse(MCServerResponse):
    """Dataclass for storing Java status answer object."""

    # Icon of the server. Can be unset. BASE64 encoded.
    icon: Optional[str]
    # Latency between a server and the client (you). In milliseconds.
    latency: float

    @classmethod
    def build(cls, answer: PingResponse) -> JavaServerResponse:
        """Build MCServerResponse object from `PingResponse`.

        :param answer: Answer from Minecraft server.
        :return: `JavaServerResponse` object.
        """
        return cls(
            players=JavaServerPlayers(
                online=answer.players.online,
                max=answer.players.max,
                list=JavaServerPlayers.build(answer.players.sample) if answer.players.sample is not None else None,
            ),
            version=JavaServerVersion(
                name=answer.version.name,
                protocol=answer.version.protocol,
            ),
            motd=answer.description,
            icon=answer.favicon,
            latency=answer.latency,
        )


@dataclass
class BedrockServerResponse(MCServerResponse):
    """Dataclass for storing Java status answer object."""

    # Can be unset.
    map_name: Optional[str]
    # Can be hidden.
    gamemode: Optional[str]

    @classmethod
    def build(cls, answer: BedrockStatusResponse) -> BedrockServerResponse:
        """Build MCServerResponse object from `BedrockStatusResponse`.

        :param answer: Answer from Minecraft server.
        :return: `MCServerResponse` object.
        """
        return cls(
            players=BedrockServerPlayers(
                online=answer.players_online,
                max=answer.players_max,
            ),
            version=BedrockServerVersion(
                name=answer.version.version,
                protocol=answer.version.protocol,
                brand=answer.version.brand,
            ),
            motd=answer.motd,
            map_name=answer.map,
            gamemode=answer.gamemode,
        )


@dataclass
class ServerPlayers(AbstractDataclass):
    """Dataclass for storing players list and some global info about players, like current online."""

    online: int
    max: int


@dataclass
class JavaServerPlayers(ServerPlayers):
    """Dataclass for storing players list and some global info about players, like current online."""

    # List of players. Can be unset. In Java can be None even if online > 0.
    list: Optional[List[JavaServerPlayer]]

    @staticmethod
    def build(players: List[PingResponse.Players.Player]) -> List[JavaServerPlayer]:
        """Build value for `list` field from list with `PingResponse.Players.Player`."""
        return [JavaServerPlayer(name=player.name, uuid=player.id) for player in players]


@dataclass
class BedrockServerPlayers(ServerPlayers):
    """Dataclass for storing players list and some global info about players, like current online."""


@dataclass
class JavaServerPlayer:
    """Dataclass for storing player info. Only for Java."""

    name: str
    uuid: str


@dataclass
class ServerVersion(AbstractDataclass):
    """Dataclass for storing version info."""

    # Version name. Example `1.18.0`.
    name: str
    # Version protocol. See https://minecraft.fandom.com/wiki/Protocol_version.
    protocol: int


@dataclass
class JavaServerVersion(ServerVersion):
    """Dataclass for storing version info for Java."""


@dataclass
class BedrockServerVersion(ServerVersion):
    """Dataclass for storing version info for Bedrock."""

    # Like `MCPE` or another.
    brand: Optional[str]


class NotBedrockAndNotJavaServer(TypeError):
    """Exception for when server is not Bedrock or Java."""
