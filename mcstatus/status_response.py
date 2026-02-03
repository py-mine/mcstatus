from mcstatus.responses import (
    BaseStatusPlayers,
    BaseStatusResponse,
    BaseStatusVersion,
    BedrockStatusPlayers,
    BedrockStatusResponse,
    BedrockStatusVersion,
    JavaStatusPlayer,
    JavaStatusPlayers,
    JavaStatusResponse,
    JavaStatusVersion,
)
from mcstatus.utils import deprecation_warn

# __all__ is frozen on the moment of deprecation
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


deprecation_warn(
    obj_name="mcstatus.status_response",
    removal_version="13.0.0",
    replacement="mcstatus.responses",
)
