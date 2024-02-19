from __future__ import annotations

import typing as t
from dataclasses import dataclass
from enum import Enum

if t.TYPE_CHECKING:
    from typing_extensions import Self, TypeAlias


class Formatting(Enum):
    """Enum for Formatting codes.

    See `Minecraft wiki <https://minecraft.wiki/w/Formatting_codes#Formatting_codes>`__
    for more info.

    .. note::
        :attr:`.STRIKETHROUGH` and :attr:`.UNDERLINED` don't work on Bedrock, which our parser
        doesn't keep it in mind. See `MCPE-41729 <https://bugs.mojang.com/browse/MCPE-41729>`_.
    """

    BOLD = "l"
    ITALIC = "o"
    UNDERLINED = "n"
    STRIKETHROUGH = "m"
    OBFUSCATED = "k"
    RESET = "r"


class MinecraftColor(Enum):
    """Enum for Color codes.

    See `Minecraft wiki <https://minecraft.wiki/w/Formatting_codes#Color_codes>`_
    for more info.
    """

    BLACK = "0"
    DARK_BLUE = "1"
    DARK_GREEN = "2"
    DARK_AQUA = "3"
    DARK_RED = "4"
    DARK_PURPLE = "5"
    GOLD = "6"
    GRAY = "7"
    DARK_GRAY = "8"
    BLUE = "9"
    GREEN = "a"
    AQUA = "b"
    RED = "c"
    LIGHT_PURPLE = "d"
    YELLOW = "e"
    WHITE = "f"

    # Only for bedrock
    MINECOIN_GOLD = "g"


@dataclass(frozen=True)
class WebColor:
    """Raw HTML color from MOTD.

    Can be found in MOTD when someone uses gradient.

    .. note:: Actually supported in Minecraft 1.16+ only.
    """

    hex: str
    rgb: tuple[int, int, int]

    @classmethod
    def from_hex(cls, hex: str) -> Self:
        """Construct web color using hex color string.

        :raises ValueError: Invalid hex color string.
        :returns: New :class:`WebColor` instance.
        """
        hex = hex.lstrip("#")

        if len(hex) not in (3, 6):
            raise ValueError(f"Got too long/short hex color: {'#' + hex!r}")
        if len(hex) == 3:
            hex = "{0}{0}{1}{1}{2}{2}".format(*hex)

        try:
            rgb = t.cast("tuple[int, int, int]", tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4)))
        except ValueError:
            raise ValueError(f"Failed to parse given hex color: {'#' + hex!r}")

        return cls.from_rgb(rgb)

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int]) -> Self:
        """Construct web color using rgb color tuple.

        :raises ValueError: When RGB color is out of its 8-bit range.
        :returns: New :class:`WebColor` instance.
        """
        cls._check_rgb(rgb)

        hex = "#{:02x}{:02x}{:02x}".format(*rgb)
        return cls(hex, rgb)

    @staticmethod
    def _check_rgb(rgb: tuple[int, int, int]) -> None:
        index_to_color_name = {0: "red", 1: "green", 2: "blue"}

        for index, value in enumerate(rgb):
            if not 255 >= value >= 0:
                color_name = index_to_color_name[index]
                raise ValueError(f"RGB color byte out of its 8-bit range (0-255) for {color_name} ({value=})")


@dataclass(frozen=True)
class TranslationTag:
    """Represents a ``translate`` field in server's answer.

    This just exists, but is completely ignored by our transformers.
    You can find translation tags in :attr:`Motd.parsed <mcstatus.motd.Motd.parsed>` attribute.

    .. seealso:: `Minecraft's wiki. <https://minecraft.wiki/w/Raw_JSON_text_format#Translated_Text>`__
    """

    id: str


ParsedMotdComponent: TypeAlias = "Formatting | MinecraftColor | WebColor | TranslationTag | str"
