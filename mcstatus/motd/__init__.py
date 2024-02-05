from __future__ import annotations

import re
import typing as t
from dataclasses import dataclass

from mcstatus.motd.components import Formatting, MinecraftColor, ParsedMotdComponent, TranslationTag, WebColor
from mcstatus.motd.simplifies import get_unused_elements, squash_nearby_strings
from mcstatus.motd.transformers import AnsiTransformer, HtmlTransformer, MinecraftTransformer, PlainTransformer

if t.TYPE_CHECKING:
    from typing_extensions import Self

    from mcstatus.status_response import RawJavaResponseMotd, RawJavaResponseMotdWhenDict  # circular import
else:
    RawJavaResponseMotdWhenDict = dict

__all__ = ["Motd"]

MOTD_COLORS_RE = re.compile(r"([\xA7|&][0-9A-FK-OR])", re.IGNORECASE)


@dataclass
class Motd:
    """Represents parsed MOTD."""

    parsed: list[ParsedMotdComponent]
    """Parsed MOTD, which then will be transformed.

    Bases on this attribute, you can easily write your own MOTD-to-something parser.
    """
    raw: RawJavaResponseMotd
    """MOTD in raw format, just like the server gave."""
    bedrock: bool = False
    """Is server Bedrock Edition? Some details may change in work of this class."""

    @classmethod
    def parse(
        cls,
        raw: RawJavaResponseMotd,  # type: ignore # later, we overwrite the type
        *,
        bedrock: bool = False,
    ) -> Self:
        """Parse a raw MOTD to less raw MOTD (:attr:`.parsed` attribute).

        :param raw: Raw MOTD, directly from server.
        :param bedrock: Is server Bedrock Edition? Nothing changes here, just sets attribute.
        :returns: New :class:`.Motd` instance.
        """
        original_raw = raw.copy() if hasattr(raw, "copy") else raw  # type: ignore # Cannot access "copy" for type "str"
        if isinstance(raw, list):
            raw: RawJavaResponseMotdWhenDict = {"extra": raw}

        if isinstance(raw, str):
            parsed = cls._parse_as_str(raw, bedrock=bedrock)
        elif isinstance(raw, dict):
            parsed = cls._parse_as_dict(raw, bedrock=bedrock)
        else:
            raise TypeError(f"Expected list, string or dict data, got {raw.__class__!r} ({raw!r}), report this!")

        return cls(parsed, original_raw, bedrock)

    @staticmethod
    def _parse_as_str(raw: str, *, bedrock: bool = False) -> list[ParsedMotdComponent]:
        """Parse a MOTD when it's string.

        .. note:: This method returns a lot of empty strings, use :meth:`Motd.simplify` to remove them.

        :param raw: Raw MOTD, directly from server.
        :param bedrock: Is server Bedrock Edition?
            Ignores :attr:`MinecraftColor.MINECOIN_GOLD` if it's :obj:`False`.
        :returns: :obj:`ParsedMotdComponent` list, which need to be passed to ``__init__``.
        """
        parsed_motd: list[ParsedMotdComponent] = []

        split_raw = MOTD_COLORS_RE.split(raw)
        for element in split_raw:
            clean_element = element.lstrip("&§").lower()
            standardized_element = element.replace("&", "§").lower()

            if standardized_element == "§g" and not bedrock:
                parsed_motd.append(element)  # minecoin_gold on java server, treat as string
                continue

            if standardized_element.startswith("§"):
                try:
                    parsed_motd.append(MinecraftColor(clean_element))
                except ValueError:
                    try:
                        parsed_motd.append(Formatting(clean_element))
                    except ValueError:
                        # just a text
                        parsed_motd.append(element)
            else:
                parsed_motd.append(element)

        return parsed_motd

    @classmethod
    def _parse_as_dict(
        cls,
        item: RawJavaResponseMotdWhenDict,
        *,
        bedrock: bool = False,
        auto_add: list[ParsedMotdComponent] | None = None,
    ) -> list[ParsedMotdComponent]:
        """Parse a MOTD when it's dict.

        :param item: :class:`dict` directly from the server.
        :param bedrock: Is the server Bedrock Edition?
            Nothing does here, just going to :meth:`._parse_as_str` while parsing ``text`` field.
        :param auto_add: Values to add on this item.
            Most time, this is :class:`Formatting` from top level.
        :returns: :obj:`ParsedMotdComponent` list, which need to be passed to ``__init__``.
        """
        parsed_motd: list[ParsedMotdComponent] = auto_add if auto_add is not None else []

        if (color := item.get("color")) is not None:
            parsed_motd.append(cls._parse_color(color))

        for style_key, style_val in Formatting.__members__.items():
            lowered_style_key = style_key.lower()
            if item.get(lowered_style_key) is False:
                try:
                    parsed_motd.remove(style_val)
                except ValueError:
                    # some servers set the formatting keys to false here, even without it ever being set to true before
                    continue
            elif item.get(lowered_style_key) is not None:
                parsed_motd.append(style_val)

        if (text := item.get("text")) is not None:
            parsed_motd.extend(cls._parse_as_str(text, bedrock=bedrock))
        if (translate := item.get("translate")) is not None:
            parsed_motd.append(TranslationTag(translate))
        parsed_motd.append(Formatting.RESET)

        if "extra" in item:
            auto_add = list(filter(lambda e: type(e) is Formatting and e != Formatting.RESET, parsed_motd))

            for element in item["extra"]:
                parsed_motd.extend(
                    cls._parse_as_dict(element, auto_add=auto_add.copy())
                    if isinstance(element, dict)
                    else auto_add + cls._parse_as_str(element, bedrock=bedrock)
                )

        return parsed_motd

    @staticmethod
    def _parse_color(color: str) -> ParsedMotdComponent:
        """Parse a color string."""
        try:
            return MinecraftColor[color.upper()]
        except KeyError:
            if color == "reset":
                # Minecraft servers actually can't return {"reset": True}, instead, they treat
                # reset as a color and set {"color": "reset"}. However logically, reset is
                # a formatting, and it resets both color and other formatting, so we use
                # `Formatting.RESET` here.
                #
                # see https://wiki.vg/Chat#Shared_between_all_components, `color` field
                return Formatting.RESET

            # Last attempt: try parsing as HTML (hex rgb) color. Some servers use these to
            # achieve gradients.
            try:
                return WebColor.from_hex(color)
            except ValueError:
                raise ValueError(f"Unable to parse color: {color!r}, report this!")

    def simplify(self) -> Self:
        """Create new MOTD without unused elements.

        After parsing, the MOTD may contain some unused elements, like empty strings, or formattings/colors
        that don't apply to anything. This method is responsible for creating a new motd with all such elements
        removed, providing a much cleaner representation.

        :returns: New simplified MOTD, with any unused elements removed.
        """
        parsed = self.parsed.copy()
        old_parsed: list[ParsedMotdComponent] | None = None

        while parsed != old_parsed:
            old_parsed = parsed.copy()
            unused_elements = get_unused_elements(parsed)
            parsed = [el for index, el in enumerate(parsed) if index not in unused_elements]

        parsed = squash_nearby_strings(parsed)
        return __class__(parsed, self.raw, bedrock=self.bedrock)

    def to_plain(self) -> str:
        """Get plain text from a MOTD, without any colors/formatting.

        This is just a shortcut to :class:`~mcstatus.motd.transformers.PlainTransformer`.
        """
        return PlainTransformer().transform(self.parsed)

    def to_minecraft(self) -> str:
        """Get Minecraft variant from a MOTD.

        This is just a shortcut to :class:`~mcstatus.motd.transformers.MinecraftTransformer`.

        .. note:: This will always use ``§``, even if in original MOTD used ``&``.
        """
        return MinecraftTransformer().transform(self.parsed)

    def to_html(self) -> str:
        """Get HTML from a MOTD.

        This is just a shortcut to :class:`~mcstatus.motd.transformers.HtmlTransformer`.
        """
        return HtmlTransformer(bedrock=self.bedrock).transform(self.parsed)

    def to_ansi(self) -> str:
        """Get ANSI variant from a MOTD.

        This is just a shortcut to :class:`~mcstatus.motd.transformers.AnsiTransformer`.

        .. note:: We support only ANSI 24 bit colors, please implement your own transformer if you need other standards.

        .. seealso:: https://en.wikipedia.org/wiki/ANSI_escape_code
        """
        return AnsiTransformer().transform(self.parsed)
