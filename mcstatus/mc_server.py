"""Module for storing `MCServerResponse` object."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union

from typing_extensions import Literal

from mcstatus.bedrock_status import BedrockStatusResponse
from mcstatus.pinger import PingResponse


@dataclass
class MCServerResponse:
    """Dataclass for storing cross-platform status answer object."""

    # Can be only "java" or "bedrock".
    type: Literal["java", "bedrock"]
    players: ServerPlayers
    version: ServerVersion
    # Message Of The Day. Also known as `Description`.
    motd: str
    # Icon of the server. Always None in Bedrock, and if unset - in Java. BASE64 encoded.
    icon: Optional[str]
    # Latency between a server and the client (you). In milliseconds. Always None in Bedrock, and never None in Java.
    latency: Optional[float]
    # Only for Bedrock. Can be unset also in Bedrock.
    map_name: Optional[str]
    # Only for Bedrock. Can be hidden also in Bedrock.
    gamemode: Optional[str]

    @classmethod
    def build(cls, answer: Union[PingResponse, BedrockStatusResponse]) -> MCServerResponse:
        """Build MCServerResponse object from `PingResponse` or `BedrockStatusResponse`.

        :param answer: Answer from Minecraft server.
        :raise TypeError: When `answer` parameter not a `PingResponse`, and not a `BedrockStatusResponse`
        :return: `MCServerResponse` object.
        """
        if isinstance(answer, PingResponse):
            return cls(
                type="java",
                players=ServerPlayers(
                    online=answer.players.online,
                    max=answer.players.max,
                    list=ServerPlayers.build(answer.players.sample) if answer.players.sample is not None else None,
                ),
                version=ServerVersion(
                    name=answer.version.name,
                    protocol=answer.version.protocol,
                    brand=None,
                ),
                motd=answer.description,
                icon=answer.favicon,
                latency=answer.latency,
                map_name=None,
                gamemode=None,
            )
        elif isinstance(answer, BedrockStatusResponse):
            return cls(
                type="bedrock",
                players=ServerPlayers(
                    online=answer.players_online,
                    max=answer.players_max,
                    list=None,
                ),
                version=ServerVersion(
                    name=answer.version.version,
                    protocol=answer.version.protocol,
                    brand=answer.version.brand,
                ),
                motd=answer.motd,
                icon=None,
                latency=None,
                map_name=answer.map,
                gamemode=answer.gamemode,
            )
        else:
            raise TypeError(f"Unknown answer type: {type(answer)}")


@dataclass
class ServerPlayers:
    """Dataclass for storing players list and some global info about players, like current online."""

    online: int
    max: int
    # List of players. Always None in Bedrock, and if unset in java. In Java can be None even if online > 0.
    list: Optional[List[ServerPlayer]]

    @staticmethod
    def build(players: List[PingResponse.Players.Player]) -> List[ServerPlayer]:
        """Build value for `list` field from list with `PingResponse.Players.Player`."""
        return [ServerPlayer(name=player.name, uuid=player.id) for player in players]


@dataclass
class ServerPlayer:
    """Dataclass for storing player info."""

    name: str
    uuid: str


@dataclass
class ServerVersion:
    """Dataclass for storing version info."""

    # Version name. Example `1.18.0`.
    name: str
    # Version protocol. See https://minecraft.fandom.com/wiki/Protocol_version.
    protocol: int
    # Only in Bedrock. Like `MCPE` or another.
    brand: Optional[str]


class NotBedrockAndNotJavaServer(TypeError):
    """Exception for when server is not Bedrock or Java."""
