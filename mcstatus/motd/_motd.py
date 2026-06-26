from __future__ import annotations

import re
import typing as t
from dataclasses import dataclass

from mcstatus.motd._simplifies import get_unused_elements, squash_nearby_strings
from mcstatus.motd._transformers import AnsiTransformer, HtmlTransformer, MinecraftTransformer, PlainTransformer
from mcstatus.motd.components import (
    BedrockFormatting,
    BedrockMinecraftColor,
    InvalidFormatting,
    JavaFormatting,
    JavaMinecraftColor,
    ParsedMotdComponent,
    TranslationTag,
    WebColor,
)

if t.TYPE_CHECKING:
    from typing_extensions import Self

    from mcstatus.responses._raw import RawJavaResponseMotd, RawJavaResponseMotdWhenDict

__all__ = ["Motd"]

_MOTD_COLORS_RE = re.compile(r"([\xA7|&][0-9A-Z])", re.IGNORECASE)


@dataclass(frozen=True)
class Motd:
    """Represents parsed MOTD."""

    parsed: list[ParsedMotdComponent]
    """Parsed MOTD, which then will be transformed.

    Bases on this attribute, you can easily write your own MOTD-to-something parser.
    """
    raw: RawJavaResponseMotd
    """MOTD in raw format, returning back the received server response unmodified."""
    bedrock: bool = False
    """Is the server Bedrock Edition?"""

    @classmethod
    def parse(
        cls,
        raw: RawJavaResponseMotd,  # pyright: ignore[reportRedeclaration] # later, we overwrite the type
        *,
        bedrock: bool = False,
    ) -> Self:
        """Parse a raw MOTD to less raw MOTD (:attr:`.parsed` attribute).

        :param raw: Raw MOTD, directly from server.
        :param bedrock: Is server Bedrock Edition? Nothing changes here, just sets attribute.
        :returns: New :class:`.Motd` instance.
        """
        original_raw: RawJavaResponseMotd
        if isinstance(raw, str):
            original_raw = raw
        elif hasattr(raw, "copy"):
            original_raw = raw.copy()
        else:  # pragma: no cover
            # we should never reach this, unless the type expectation wasn't met.
            # in that case, the isinstance checks below will fail and this will end
            # in a TypeError
            original_raw = raw

        if isinstance(raw, list):
            raw: RawJavaResponseMotdWhenDict = {"extra": raw}

        if isinstance(raw, str):
            parsed = cls._parse_as_str(raw, bedrock=bedrock)
        elif isinstance(raw, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            parsed = cls._parse_as_dict(raw, bedrock=bedrock)
        else:
            raise TypeError(f"Expected list, string or dict data, got {raw.__class__!r} ({raw!r}), report this!")

        return cls(parsed, original_raw, bedrock)

    @staticmethod
    def _parse_as_str(raw: str, *, bedrock: bool = False) -> list[ParsedMotdComponent]:
        """Parse a MOTD when it's string.

        .. note::

            This method may return a lot of unnecessary noise, like extra
            :attr:`Formatting.RESET`. Use :meth:`Motd.simplify` to remove it.

        :param raw: Raw MOTD, directly from server.
        :param bedrock: Is server Bedrock Edition?
            If it isn't, ignores any color that starts with ``MATERIAL`` or
            :attr:`MinecraftColor.MINECOIN_GOLD`.
        :returns: :obj:`ParsedMotdComponent` list, which need to be passed to ``__init__``.
        """
        parsed_motd: list[ParsedMotdComponent] = []

        color_enum = BedrockMinecraftColor if bedrock else JavaMinecraftColor
        formatting_enum = BedrockFormatting if bedrock else JavaFormatting

        split_raw = _MOTD_COLORS_RE.split(raw)
        for element in split_raw:
            if not element:
                continue

            clean_element = element.lstrip("&§").lower()
            standardized_element = element.replace("&", "§").lower()

            if standardized_element.startswith("§"):
                try:
                    parsed_motd.append(color_enum(clean_element))
                except ValueError:
                    try:
                        parsed_motd.append(formatting_enum(clean_element))
                    except ValueError:
                        parsed_motd.append(InvalidFormatting(clean_element))
            else:
                parsed_motd.append(element)

        return parsed_motd

    @classmethod
    def _parse_as_dict(
        cls,
        item: RawJavaResponseMotdWhenDict,
        *,
        bedrock: bool,
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
        formatting_enum = BedrockFormatting if bedrock else JavaFormatting
        parsed_motd: list[ParsedMotdComponent] = auto_add if auto_add is not None else []

        if (color := item.get("color")) is not None:
            parsed_motd.append(cls._parse_color(color, bedrock=bedrock))

        for style_key, style_val in formatting_enum.__members__.items():
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
        parsed_motd.append(formatting_enum.RESET)

        if "extra" in item:
            auto_add = list(filter(lambda e: type(e) is formatting_enum and e != formatting_enum.RESET, parsed_motd))

            for element in item["extra"]:
                parsed_motd.extend(
                    cls._parse_as_dict(element, bedrock=bedrock, auto_add=auto_add.copy())
                    if isinstance(element, dict)
                    else auto_add + cls._parse_as_str(element, bedrock=bedrock)
                )

        return parsed_motd

    @staticmethod
    def _parse_color(color: str, *, bedrock: bool) -> ParsedMotdComponent:
        """Parse a color string."""
        color_enum = BedrockMinecraftColor if bedrock else JavaMinecraftColor
        formatting_enum = BedrockFormatting if bedrock else JavaFormatting
        try:
            return color_enum[color.upper()]
        except KeyError:
            if color == "reset":
                # Minecraft servers actually can't return {"reset": True}, instead, they treat
                # reset as a color and set {"color": "reset"}. However logically, reset is
                # a formatting, and it resets both color and other formatting, so we use
                # `Formatting.RESET` here.
                #
                # see `color` field in
                # https://minecraft.wiki/w/Java_Edition_protocol/Chat?oldid=2763811#Shared_between_all_components
                return formatting_enum.RESET

            # Last attempt: try parsing as HTML (hex rgb) color. Some servers use these to
            # achieve gradients.
            try:
                return WebColor.from_hex(color)
            except ValueError as e:
                raise ValueError(f"Unable to parse color: {color!r}, report this!") from e

    def simplify(self) -> Self:
        """Create new MOTD without unused elements.

        After parsing, the MOTD may contain some unused elements, like empty strings, or formatting/colors
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
        return self.__class__(parsed, self.raw, bedrock=self.bedrock)

    def to_plain(self) -> str:
        """Get plain text from a MOTD, without any colors/formatting.

        Example:
            ``&0Hello &oWorld`` turns into ``Hello World``.
        """
        return PlainTransformer(bedrock=self.bedrock).transform(self.parsed)

    def to_minecraft(self) -> str:
        """Transform MOTD to the Minecraft representation.

        .. note:: This will always use ``§``, even if in original MOTD used ``&``.

        Example:
            .. code-block:: python

                >>> Motd.parse("&0Hello &oWorld")
                "§0Hello §oWorld"
        """
        return MinecraftTransformer(bedrock=self.bedrock).transform(self.parsed)

    def to_html(self) -> str:
        """Transform MOTD to the HTML format.

        The result is always wrapped in a ``<p>`` tag, if you need to remove it,
        just do ``result.removeprefix("<p>").removesuffix("</p>")``.

        .. note::
            You should implement the "obfuscated" CSS class yourself using this snippet:

            .. code-block:: javascript

                const obfuscatedCharacters =
                  "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`~!@#$%^&*()-_=+[]\\"';:<>,./?";
                const obfuscatedElems = document.querySelectorAll(".obfuscated");

                if (obfuscatedElems !== undefined) {
                  const render = () => {
                    obfuscatedElems.forEach((elem) => {
                      let value = "";

                      for (let i = 0, l = elem.innerText.length; i < l; i++) {
                        value += obfuscatedCharacters.charAt(
                          Math.floor(Math.random() * obfuscatedCharacters.length),
                        );
                      }

                      elem.innerText = value;
                    });
                    setTimeout(render, 50);
                  };
                  render();
                }

            Also do note that this formatting does not make sense with
            non-monospace fonts.

        Example:
            ``&6Hello&o from &rAnother &kWorld`` turns into

            .. code-block:: html

                <!-- there are no new lines in the actual output, those are added for readability -->
                <p>
                 <span style='color:rgb(255, 170, 0);text-shadow:0 0 1px rgb(42, 42, 0)'>
                  Hello<i> from </span></i>
                  Another <span class=obfuscated>World</span>
                </p>
        """  # noqa: D301 # Use `r"""` if any backslashes in a docstring
        return HtmlTransformer(bedrock=self.bedrock).transform(self.parsed)

    def to_ansi(self) -> str:
        """Transform MOTD to the ANSI 24-bit format.

        ANSI is mostly used for printing colored text in the terminal.

        "Obfuscated" formatting (``&k``) is shown as a blinking one.

        .. seealso:: https://en.wikipedia.org/wiki/ANSI_escape_code.
        """
        return AnsiTransformer(bedrock=self.bedrock).transform(self.parsed)
