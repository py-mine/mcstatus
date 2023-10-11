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


import warnings

warnings.warn("`mcstatus.status_response` is deprecated, use `mcstatus.responses` instead", DeprecationWarning, stacklevel=2)
