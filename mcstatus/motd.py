from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, List, Optional, TYPE_CHECKING, Tuple, Union, overload

if TYPE_CHECKING:
    from typing import TypeVar

    from typing_extensions import Self, TypeAlias

    _T = TypeVar("_T")

__all__ = [
    "Motd",
    "Formatting",
    "MinecraftColor",
    "WebColor",
    "TranslateString",
    "ParsedMotdItem",
    "MotdSimplifies",
]

MOTD_COLORS_RE = re.compile(r"([\xA7|&][0-9A-FK-OR])", re.IGNORECASE)


class Formatting(Enum):
    """Enum for Formatting codes.

    See `MineCraft wiki <https://minecraft.fandom.com/wiki/Formatting_codes#Formatting_codes>`_
    for more info.

    .. note::
        ``STRIKETHROUGH`` and ``UNDERLINED`` don't work on Bedrock, which our parser
        doesn't keep it in mind. See `MCPE-41729 <https://bugs.mojang.com/browse/MCPE-41729>`_.
    """

    BOLD = "l"
    ITALIC = "o"
    UNDERLINED = "n"
    STRIKETHROUGH = "m"
    OBFUSCATED = "k"
    RESET = "r"


FORMATTING_TO_HTML_TAGS = {
    Formatting.BOLD: "b",
    Formatting.STRIKETHROUGH: "s",
    Formatting.ITALIC: "i",
    Formatting.UNDERLINED: "u",
}


FORMATTING_TO_ANSI_TAGS = {
    Formatting.BOLD: "1",
    Formatting.STRIKETHROUGH: "9",
    Formatting.ITALIC: "3",
    Formatting.UNDERLINED: "4",
    Formatting.OBFUSCATED: "5",
}


class MinecraftColor(Enum):
    """Enum for Color codes.

    See `MineCraft wiki <https://minecraft.fandom.com/wiki/Formatting_codes#Color_codes>`_
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


MINECRAFT_COLOR_TO_HEX_BEDROCK = {
    MinecraftColor.BLACK: ("#000000", "#000000"),
    MinecraftColor.DARK_BLUE: ("#0000AA", "#00002A"),
    MinecraftColor.DARK_GREEN: ("#00AA00", "#002A00"),
    MinecraftColor.DARK_AQUA: ("#00AAAA", "#002A2A"),
    MinecraftColor.DARK_RED: ("#AA0000", "#AA0000"),
    MinecraftColor.DARK_PURPLE: ("#AA00AA", "#2A002A"),
    MinecraftColor.GOLD: ("#FFAA00", "#402A00"),
    MinecraftColor.GRAY: ("#AAAAAA", "#2A2A2A"),
    MinecraftColor.DARK_GRAY: ("#555555", "#151515"),
    MinecraftColor.BLUE: ("#5555FF", "#15153F"),
    MinecraftColor.GREEN: ("#55FF55", "#153F15"),
    MinecraftColor.AQUA: ("#55FFFF", "#153F3F"),
    MinecraftColor.RED: ("#FF5555", "#3F1515"),
    MinecraftColor.LIGHT_PURPLE: ("#FF55FF", "#3F153F"),
    MinecraftColor.YELLOW: ("#FFFF55", "#3F3F15"),
    MinecraftColor.WHITE: ("#FFFFFF", "#3F3F3F"),
    MinecraftColor.MINECOIN_GOLD: ("#DDD605", "#373501"),
}

MINECRAFT_COLOR_TO_HEX_JAVA = MINECRAFT_COLOR_TO_HEX_BEDROCK.copy()
MINECRAFT_COLOR_TO_HEX_JAVA[MinecraftColor.GOLD] = ("#FFAA00", "#2A2A00")

MINECRAFT_COLOR_TO_ANSI = {
    MinecraftColor.BLACK: "30",
    MinecraftColor.DARK_BLUE: "34",
    MinecraftColor.DARK_GREEN: "32",
    MinecraftColor.DARK_AQUA: "36",
    MinecraftColor.DARK_RED: "31",
    MinecraftColor.DARK_PURPLE: "35",
    MinecraftColor.GOLD: "33",
    MinecraftColor.GRAY: "37",
    MinecraftColor.DARK_GRAY: "90",
    MinecraftColor.BLUE: "94",
    MinecraftColor.GREEN: "92",
    MinecraftColor.AQUA: "96",
    MinecraftColor.RED: "91",
    MinecraftColor.LIGHT_PURPLE: "95",
    MinecraftColor.YELLOW: "93",
    MinecraftColor.WHITE: "97",
    MinecraftColor.MINECOIN_GOLD: "33",
}


@dataclass
class WebColor:
    """Raw HTML color from MOTD.

    Can be found in MOTD when someone uses gradient.
    """

    hex: str
    rgb: Tuple[int, int, int]

    @classmethod
    @overload
    def parse(cls, *, hex: str, rgb: Optional[Tuple[int, int, int]] = None) -> Self:
        ...

    @classmethod
    @overload
    def parse(cls, *, rgb: Tuple[int, int, int], hex: Optional[str] = None) -> Self:
        ...

    @classmethod
    def parse(cls, *, hex: Optional[str] = None, rgb: Optional[Tuple[int, int, int]] = None) -> Self:
        """Parse hex or RGB color, from hex or RGB (one of them can be ``None``).

        Ensures that ``WebColor.hex`` starts with '#', and generate RGB color for it,
        if ``WebColor.rgb`` is None (default value). Or generate hex value from RGB, if
        ``WebColor.hex`` is None (also default value).

        :raises ValueError: When hex color isn't correct, so we can't generate RGB for it.
        :raises TypeError: When hex and RGB colors is ``None``.
        :returns: New ``WebColor`` instance.
        """
        if hex is None and rgb is None:
            raise TypeError("`hex` and `rgb` parameters is None, we need one of them.")

        if hex is None and rgb is not None:
            if not all(256 > e > -1 for e in rgb):
                raise ValueError("One of RGB colors is less than zero or more than 255: " + str(rgb))
            hex = "#%02x%02x%02x" % rgb
        elif hex is not None and rgb is None:  # pragma: no branch
            if not hex.startswith("#"):
                hex = "#" + hex
            try:
                rgb = tuple(int(hex.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                raise ValueError(f"Incorrect hex color '{hex}', failed to generate RGB.")

        return cls(hex=hex, rgb=rgb)  # type: ignore[assignment]


@dataclass
class TranslateString:
    """Represents a ``translate`` field in server's answer.

    This just exist, and completely ignored by our end-parsers (``ansi``, ``html`` etc. properties).
    You can parse them with ``Motd.parsed`` attribute.

    .. seealso:: `Minecraft's wiki. <https://minecraft.fandom.com/wiki/Raw_JSON_text_format#Translated_Text>`_
    """

    id: str


ParsedMotdItem: TypeAlias = Union[Formatting, MinecraftColor, WebColor, TranslateString, str]


@dataclass
class Motd:
    """Represents parsed MOTD.

    Basing on this class, you can write your own MOTD-to-something parser, see ``parsed`` field.
    """

    parsed: List[ParsedMotdItem]
    """Parsed MOTD, which then will be transformed.

    Bases on this field, you can easily write your own MOTD-to-something parser.
    """
    bedrock: bool = False
    """Is server Bedrock Edition? Some details may change in work of this class."""

    @classmethod
    def parse(cls, raw: Union[dict, list, str], *, bedrock: bool = False) -> Self:
        """Parse a raw MOTD to less raw MOTD (``Motd.parsed`` field).

        :param raw: Raw MOTD, directly from server.
        :param bedrock: Is server Bedrock Edition? Nothing changes here, just sets attribute.
        :returns: New ``MOTD`` instance.
        """
        if isinstance(raw, str):
            return cls(cls._parse_as_str(raw, bedrock=bedrock), bedrock)

        if isinstance(raw, list):
            raw = {"extra": raw}

        return cls(cls._parse_as_dict(raw), bedrock)

    @classmethod
    def _parse_as_dict(cls, item: dict, *, auto_add: Optional[List[ParsedMotdItem]] = None) -> List[ParsedMotdItem]:
        """Parse a MOTD when it's dict.

        :param item: ``dict`` directly from the server.
        :param auto_add: Values to add on this item.
            Most time, this is ``Formatting`` from top level.
        :returns: ``ParsedMotdItem`` list, which need to be passed to ``__init__``.
        """
        parsed_motd: List[ParsedMotdItem] = auto_add if auto_add is not None else []

        if item.get("color"):
            try:
                parsed_motd.append(MinecraftColor[item["color"].upper()])
            except KeyError:
                parsed_motd.append(WebColor.parse(hex=item["color"]))

        for style_key, style_val in Formatting.__members__.items():
            if item.get(style_key.lower()) is False or item.get(style_key.lower()) == "false":
                parsed_motd.remove(style_val)
            elif item.get(style_key.lower()) is not None:
                parsed_motd.append(style_val)

        text = item.get("text")
        if text is not None:
            parsed_motd.append(text)
        translate = item.get("translate")
        if text is None and translate is not None:
            parsed_motd.append(TranslateString(translate))
        parsed_motd.append(Formatting.RESET)

        if item.get("extra"):
            auto_add = list(filter(lambda e: type(e) is Formatting and e != Formatting.RESET, parsed_motd))

            for element in item["extra"]:
                parsed_motd.extend(cls._parse_as_dict(element, auto_add=auto_add.copy()))

        return parsed_motd

    @staticmethod
    def _parse_as_str(raw: str, *, bedrock: bool = False) -> List[ParsedMotdItem]:
        """Parse a MOTD when it's string.

        .. note:: This method returns a lot of empty strings, use ``Motd.simplify`` to remove them.

        :param raw: Raw MOTD, directly from server.
        :param bedrock: Is server Bedrock Edition?
            Ignores ``MinecraftColor.MINECOIN_GOLD`` if it's ``False``.
        :returns: ``ParsedMotdItem`` list, which need to be passed to ``__init__``.
        """
        parsed_motd: List[ParsedMotdItem] = []

        split_raw = MOTD_COLORS_RE.split(raw)
        for element in split_raw:
            clean_element = element.lstrip("&§")
            if clean_element == "g" and not bedrock:
                parsed_motd.append(element)  # minecoin_gold on java server
                continue
            try:
                parsed_motd.append(MinecraftColor(clean_element))
            except ValueError:
                try:
                    parsed_motd.append(Formatting(clean_element))
                except ValueError:
                    # just a text
                    parsed_motd.append(element)

        return parsed_motd

    def simplify(self) -> Self:
        """Simplify MOTD by removing unused formatting, unaffected colors etc.

        :returns: ``self`` parameter, so you can chain this method.
        """
        again = False

        simplifies = MotdSimplifies(self.parsed).simplifies
        for enumeration, item in enumerate(self.parsed):
            old_motd = self.parsed.copy()
            for hook in simplifies:
                hook(item, enumeration)
            again = old_motd != self.parsed

        if again:
            self.simplify()

        return self

    @property
    def plain(self) -> str:
        """Get plain text from MOTD.

        :returns: Plain text.
        """
        return "".join(str(e) for e in self.parsed if isinstance(e, str))

    @property
    def minecraft(self) -> str:
        """Getter for variant of a MOTD with Minecraft colors.

        :returns: Minecraft variant of MOTD.

        .. note:: This will always use "§", even if in original MOTD everywhere was "&".
        """
        result = ""
        for element in self.parsed:
            if isinstance(element, str):
                result += element
                continue
            if isinstance(element, WebColor) or isinstance(element, TranslateString):
                continue

            result += "§" + element.value

        return result

    @property
    def html(self) -> str:
        """Getter for HTML variant of a MOTD.

        .. warn::
            You should implement obfuscated CSS class yourself (name - ``obfuscated``).
            See `this answer <https://stackoverflow.com/a/30313558>`_ as example.

        :returns: String that contain HTML.
        """
        result = "<p>"
        on_reset = ""
        for element in self.parsed:
            if isinstance(element, str):
                result += element
            elif isinstance(element, TranslateString):
                continue
            elif isinstance(element, WebColor):
                result += f"<span style='color:{element.hex}'>"
                on_reset += "</span>"

            elif isinstance(element, Formatting):
                if element == Formatting.RESET:
                    result += on_reset
                    on_reset = ""
                elif element == Formatting.OBFUSCATED:
                    result += "<span class=obfuscated>"
                    on_reset += "</span>"
                else:
                    tag_name = FORMATTING_TO_HTML_TAGS[element]
                    result += "<" + tag_name + ">"
                    on_reset += "</" + tag_name + ">"
            else:
                mc_color_to_hex = MINECRAFT_COLOR_TO_HEX_BEDROCK if self.bedrock else MINECRAFT_COLOR_TO_HEX_JAVA
                foreground_color, background_color = mc_color_to_hex[element]

                result += f"<span style='color:{foreground_color};text-shadow:0 0 1px {background_color}'>"
                on_reset += "</span>"

        return result + on_reset + "</p>"

    @property
    def xterm_256(self) -> str:
        """Getter for a xterm-256 variant of MOTD.

        The only difference from ``ansi`` is that it's using RGB colors instead of ``red``, ``blue`` etc.

        :returns: String full of xterm-256 colors.
        """
        result = r"\e[0m"
        for element in self.parsed:
            if isinstance(element, str):
                result += element
            elif isinstance(element, TranslateString):
                continue
            elif isinstance(element, WebColor):
                result += r"\x1b[38;2;{0};{1};{2}m".format(*element.rgb)

            elif isinstance(element, Formatting):
                if element == Formatting.RESET:
                    result += r"\e[0m"
                else:
                    tag_number = FORMATTING_TO_ANSI_TAGS[element]
                    result += r"\e[" + tag_number + "m"
            else:
                mc_color_to_hex = MINECRAFT_COLOR_TO_HEX_BEDROCK if self.bedrock else MINECRAFT_COLOR_TO_HEX_JAVA
                foreground_color, background_color = mc_color_to_hex[element]

                result += r"\x1b[38;2;{0};{1};{2}m".format(
                    *tuple(int(foreground_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
                )
                result += r"\x1b[48;2;{0};{1};{2}m".format(
                    *tuple(int(background_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
                )

        return result + r"\e[0m"

    @property
    def ansi(self) -> str:
        """Getter for an ANSI colors variant of MOTD.

        The only difference from ``xterm_256`` is that it's using ``red``, ``blue`` etc. instead of RGB colors.
        This also using ``xterm_256`` colors, if found ``WebColor`` in ``Motd.parsed``.

        .. note:: ``MINECOIN_GOLD`` will be replaced by ``GOLD`` here.

        .. note:: This don't check non ANSI characters, only colors.

        .. warn:: There is no support for background colors, use ``xterm_256`` instead.

        :returns: String full of ANSI colors.
        """
        result = r"\e[0m"
        for element in self.parsed:
            if isinstance(element, str):
                result += element
            elif isinstance(element, TranslateString):
                continue
            elif isinstance(element, WebColor):
                result += r"\x1b[38;2;{0};{1};{2}m".format(*element.rgb)

            elif isinstance(element, Formatting):
                if element == Formatting.RESET:
                    result += r"\e[0m"
                else:
                    tag_number = FORMATTING_TO_ANSI_TAGS[element]
                    result += r"\e[" + tag_number + "m"
            else:
                foreground_color = MINECRAFT_COLOR_TO_ANSI[element]

                result += r"\e[0;" + foreground_color + "m"

        return result + r"\e[0m"


class MotdSimplifies:
    """Collection of MOTD simplifies.

    They're just removing unused formatting, unaffected colors etc.
    """

    def __init__(self, raw: List[ParsedMotdItem]) -> None:
        self.parsed: List[ParsedMotdItem] = raw

    @property
    def simplifies(self) -> Iterable[Callable[[ParsedMotdItem, int], None]]:
        """Generator with all simplifies.

        They must follow this signature:
        ``(self, item: ParsedMotdItem, enumeration: int) -> None``

        You can mock this method to add your simplifier,
        or just add it as attribute to this class.
        """
        for item in dir(self):
            if callable(getattr(self, item)) and not item.startswith("_"):
                yield getattr(self, item)

    def remove_double_items(self, item: ParsedMotdItem, enumeration: int) -> None:
        """Remove double items.

        This will check only next item, because anyway this check will run on all items.
        """
        try:
            if self.parsed[enumeration + 1] == item:
                self.parsed.pop(enumeration)
        except IndexError:
            pass

    def remove_double_colors(self, item: ParsedMotdItem, enumeration: int) -> None:
        """Remove double colors.

        This will check only next item, because anyway this check will run on all items.
        """
        try:
            if (isinstance(item, MinecraftColor) or isinstance(item, WebColor)) and (
                isinstance(self.parsed[enumeration + 1], MinecraftColor) or isinstance(self.parsed[enumeration + 1], WebColor)
            ):
                self.parsed.pop(enumeration)
        except IndexError:
            pass

    def remove_unused_formatting_before_color(self, item: ParsedMotdItem, enumeration: int) -> None:
        """Remove unused formatting before color.

        Color by default reset everything, so formatting will be unused.
        """
        try:
            if isinstance(item, Formatting) and (
                isinstance(self.parsed[enumeration + 1], MinecraftColor) or isinstance(self.parsed[enumeration + 1], WebColor)
            ):
                self.parsed.pop(enumeration)
        except IndexError:
            pass

    def remove_non_text_in_the_end(self, item: ParsedMotdItem, enumeration: int) -> None:
        """Remove non-text in the end.

        Only strings do something in the end.
        """
        if enumeration == len(self.parsed) - 1 and not isinstance(item, str):
            self.parsed.pop(enumeration)

    def remove_false_values(self, item: ParsedMotdItem, enumeration: int) -> None:
        """Remove values, that after wrapping to ``bool`` function, return ``False``.

        As example empty strings, empty lists, empty tuples, etc.

        .. note:: If follow ``ParsedMotdItem`` type, this will affect only empty strings.
        """
        if not item:
            self.parsed.pop(enumeration)
