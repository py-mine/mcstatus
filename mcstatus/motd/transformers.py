from __future__ import annotations

import abc
import typing as t
from collections.abc import Callable, Sequence

from mcstatus.motd.components import Formatting, MinecraftColor, ParsedMotdComponent, TranslationTag, WebColor

_HOOK_RETURN_TYPE = t.TypeVar("_HOOK_RETURN_TYPE")
_END_RESULT_TYPE = t.TypeVar("_END_RESULT_TYPE")


class BaseTransformer(abc.ABC, t.Generic[_HOOK_RETURN_TYPE, _END_RESULT_TYPE]):
    """Base motd transformer class.

    Motd transformer is responsible for providing a way to generate an alternative representation
    of motd, such as one that is able to be printed in the terminal.
    """

    def transform(self, motd_components: Sequence[ParsedMotdComponent]) -> _END_RESULT_TYPE:
        return self._format_output([handled for component in motd_components for handled in self._handle_component(component)])

    @abc.abstractmethod
    def _format_output(self, results: list[_HOOK_RETURN_TYPE]) -> _END_RESULT_TYPE: ...

    def _handle_component(
        self, component: ParsedMotdComponent
    ) -> tuple[_HOOK_RETURN_TYPE, _HOOK_RETURN_TYPE] | tuple[_HOOK_RETURN_TYPE]:
        handler: Callable[[ParsedMotdComponent], _HOOK_RETURN_TYPE] = {
            MinecraftColor: self._handle_minecraft_color,
            WebColor: self._handle_web_color,
            Formatting: self._handle_formatting,
            TranslationTag: self._handle_translation_tag,
            str: self._handle_str,
        }[type(component)]

        additional = None
        if isinstance(component, MinecraftColor):
            additional = self._handle_formatting(Formatting.RESET)

        return (additional, handler(component)) if additional is not None else (handler(component),)

    @abc.abstractmethod
    def _handle_str(self, element: str, /) -> _HOOK_RETURN_TYPE: ...

    @abc.abstractmethod
    def _handle_translation_tag(self, _: TranslationTag, /) -> _HOOK_RETURN_TYPE: ...

    @abc.abstractmethod
    def _handle_web_color(self, element: WebColor, /) -> _HOOK_RETURN_TYPE: ...

    @abc.abstractmethod
    def _handle_formatting(self, element: Formatting, /) -> _HOOK_RETURN_TYPE: ...

    @abc.abstractmethod
    def _handle_minecraft_color(self, element: MinecraftColor, /) -> _HOOK_RETURN_TYPE: ...


class NothingTransformer(BaseTransformer[str, str]):
    """Transformer that transforms all elements into empty strings.

    This transformer acts as a base for other transformers with string result type.
    """

    def _format_output(self, results: list[str]) -> str:
        return "".join(results)

    def _handle_str(self, element: str, /) -> str:
        return ""

    def _handle_minecraft_color(self, element: MinecraftColor, /) -> str:
        return ""

    def _handle_web_color(self, element: WebColor, /) -> str:
        return ""

    def _handle_formatting(self, element: Formatting, /) -> str:
        return ""

    def _handle_translation_tag(self, element: TranslationTag, /) -> str:
        return ""


class PlainTransformer(NothingTransformer):
    def _handle_str(self, element: str, /) -> str:
        return element


class MinecraftTransformer(PlainTransformer):
    def _handle_component(self, component: ParsedMotdComponent) -> tuple[str, str] | tuple[str]:
        result = super()._handle_component(component)
        if len(result) == 2:
            return (result[1],)
        return result

    def _handle_minecraft_color(self, element: MinecraftColor, /) -> str:
        return "§" + element.value

    def _handle_formatting(self, element: Formatting, /) -> str:
        return "§" + element.value


class HtmlTransformer(PlainTransformer):
    """Formatter for HTML variant of a MOTD.

    .. warning::
        You should implement obfuscated CSS class yourself (name - ``obfuscated``).
        See `this answer <https://stackoverflow.com/a/30313558>`_ as example.
    """

    FORMATTING_TO_HTML_TAGS = {
        Formatting.BOLD: "b",
        Formatting.STRIKETHROUGH: "s",
        Formatting.ITALIC: "i",
        Formatting.UNDERLINED: "u",
    }
    MINECRAFT_COLOR_TO_RGB_BEDROCK = {
        MinecraftColor.BLACK: ((0, 0, 0), (0, 0, 0)),
        MinecraftColor.DARK_BLUE: ((0, 0, 170), (0, 0, 42)),
        MinecraftColor.DARK_GREEN: ((0, 170, 0), (0, 42, 0)),
        MinecraftColor.DARK_AQUA: ((0, 170, 170), (0, 42, 42)),
        MinecraftColor.DARK_RED: ((170, 0, 0), (42, 0, 0)),
        MinecraftColor.DARK_PURPLE: ((170, 0, 170), (42, 0, 42)),
        MinecraftColor.GOLD: ((255, 170, 0), (64, 42, 0)),
        MinecraftColor.GRAY: ((170, 170, 170), (42, 42, 42)),
        MinecraftColor.DARK_GRAY: ((85, 85, 85), (21, 21, 21)),
        MinecraftColor.BLUE: ((85, 85, 255), (21, 21, 63)),
        MinecraftColor.GREEN: ((85, 255, 85), (21, 63, 21)),
        MinecraftColor.AQUA: ((85, 255, 255), (21, 63, 63)),
        MinecraftColor.RED: ((255, 85, 85), (63, 21, 21)),
        MinecraftColor.LIGHT_PURPLE: ((255, 85, 255), (63, 21, 63)),
        MinecraftColor.YELLOW: ((255, 255, 85), (63, 63, 21)),
        MinecraftColor.WHITE: ((255, 255, 255), (63, 63, 63)),
        MinecraftColor.MINECOIN_GOLD: ((221, 214, 5), (55, 53, 1)),
    }
    MINECRAFT_COLOR_TO_RGB_JAVA = MINECRAFT_COLOR_TO_RGB_BEDROCK.copy()
    MINECRAFT_COLOR_TO_RGB_JAVA[MinecraftColor.GOLD] = ((255, 170, 0), (42, 42, 0))

    def __init__(self, *, bedrock: bool = False) -> None:
        self.bedrock = bedrock
        self.on_reset: list[str] = []

    def transform(self, motd_components: Sequence[ParsedMotdComponent]) -> str:
        self.on_reset = []
        return super().transform(motd_components)

    def _format_output(self, results: list[str]) -> str:
        return "<p>" + super()._format_output(results) + "".join(self.on_reset) + "</p>"

    def _handle_minecraft_color(self, element: MinecraftColor, /) -> str:
        color_map = self.MINECRAFT_COLOR_TO_RGB_BEDROCK if self.bedrock else self.MINECRAFT_COLOR_TO_RGB_JAVA
        fg_color, bg_color = color_map[element]

        self.on_reset.append("</span>")
        return f"<span style='color:rgb{fg_color};text-shadow:0 0 1px rgb{bg_color}'>"

    def _handle_web_color(self, element: WebColor, /) -> str:
        self.on_reset.append("</span>")
        return f"<span style='color:rgb{element.rgb}'>"

    def _handle_formatting(self, element: Formatting, /) -> str:
        if element is Formatting.RESET:
            to_return = "".join(self.on_reset)
            self.on_reset = []
            return to_return

        if element is Formatting.OBFUSCATED:
            self.on_reset.append("</span>")
            return "<span class=obfuscated>"

        tag_name = self.FORMATTING_TO_HTML_TAGS[element]
        self.on_reset.append(f"</{tag_name}>")
        return f"<{tag_name}>"


class AnsiTransformer(PlainTransformer):
    FORMATTING_TO_ANSI_TAGS = {
        Formatting.BOLD: "1",
        Formatting.STRIKETHROUGH: "9",
        Formatting.ITALIC: "3",
        Formatting.UNDERLINED: "4",
        Formatting.OBFUSCATED: "5",
    }
    MINECRAFT_COLOR_TO_RGB = {
        MinecraftColor.BLACK: (0, 0, 0),
        MinecraftColor.DARK_BLUE: (0, 0, 170),
        MinecraftColor.DARK_GREEN: (0, 170, 0),
        MinecraftColor.DARK_AQUA: (0, 170, 170),
        MinecraftColor.DARK_RED: (170, 0, 0),
        MinecraftColor.DARK_PURPLE: (170, 0, 170),
        MinecraftColor.GOLD: (255, 170, 0),
        MinecraftColor.GRAY: (170, 170, 170),
        MinecraftColor.DARK_GRAY: (85, 85, 85),
        MinecraftColor.BLUE: (85, 85, 255),
        MinecraftColor.GREEN: (85, 255, 85),
        MinecraftColor.AQUA: (85, 255, 255),
        MinecraftColor.RED: (255, 85, 85),
        MinecraftColor.LIGHT_PURPLE: (255, 85, 255),
        MinecraftColor.YELLOW: (255, 255, 85),
        MinecraftColor.WHITE: (255, 255, 255),
        MinecraftColor.MINECOIN_GOLD: (221, 214, 5),
    }

    def ansi_color(self, color: tuple[int, int, int] | MinecraftColor) -> str:
        """Transform RGB color to ANSI color code."""
        if isinstance(color, MinecraftColor):
            color = self.MINECRAFT_COLOR_TO_RGB[color]

        return "\033[38;2;{0};{1};{2}m".format(*color)

    def _format_output(self, results: list[str]) -> str:
        return "\033[0m" + super()._format_output(results) + "\033[0m"

    def _handle_minecraft_color(self, element: MinecraftColor, /) -> str:
        return self.ansi_color(element)

    def _handle_web_color(self, element: WebColor, /) -> str:
        return self.ansi_color(element.rgb)

    def _handle_formatting(self, element: Formatting, /) -> str:
        if element is Formatting.RESET:
            return "\033[0m"
        return "\033[" + self.FORMATTING_TO_ANSI_TAGS[element] + "m"
