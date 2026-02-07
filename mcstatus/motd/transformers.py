from __future__ import annotations

import abc
import typing as t
from collections.abc import Callable, Sequence

from mcstatus.motd.components import Formatting, MinecraftColor, ParsedMotdComponent, TranslationTag, WebColor
from mcstatus.utils import deprecation_warn

_HOOK_RETURN_TYPE = t.TypeVar("_HOOK_RETURN_TYPE")
_END_RESULT_TYPE = t.TypeVar("_END_RESULT_TYPE")

# MinecraftColor: (foreground, background)
_SHARED_MINECRAFT_COLOR_TO_RGB = {
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
}

MINECRAFT_COLOR_TO_RGB_JAVA = _SHARED_MINECRAFT_COLOR_TO_RGB.copy()
MINECRAFT_COLOR_TO_RGB_JAVA[MinecraftColor.GRAY] = ((170, 170, 170), (42, 42, 42))

MINECRAFT_COLOR_TO_RGB_BEDROCK = _SHARED_MINECRAFT_COLOR_TO_RGB.copy()
MINECRAFT_COLOR_TO_RGB_BEDROCK.update(
    {
        MinecraftColor.GRAY: ((198, 198, 198), (49, 49, 49)),
        MinecraftColor.MINECOIN_GOLD: ((221, 214, 5), (55, 53, 1)),
        MinecraftColor.MATERIAL_QUARTZ: ((227, 212, 209), (56, 53, 52)),
        MinecraftColor.MATERIAL_IRON: ((206, 202, 202), (51, 50, 50)),
        MinecraftColor.MATERIAL_NETHERITE: ((68, 58, 59), (17, 14, 14)),
        MinecraftColor.MATERIAL_REDSTONE: ((151, 22, 7), (37, 5, 1)),
        MinecraftColor.MATERIAL_COPPER: ((180, 104, 77), (45, 26, 19)),
        MinecraftColor.MATERIAL_GOLD: ((222, 177, 45), (55, 44, 11)),
        MinecraftColor.MATERIAL_EMERALD: ((17, 159, 54), (4, 40, 13)),
        MinecraftColor.MATERIAL_DIAMOND: ((44, 186, 168), (11, 46, 42)),
        MinecraftColor.MATERIAL_LAPIS: ((33, 73, 123), (8, 18, 30)),
        MinecraftColor.MATERIAL_AMETHYST: ((154, 92, 198), (38, 23, 49)),
        MinecraftColor.MATERIAL_RESIN: ((235, 114, 20), (59, 29, 5)),
    }
)


class BaseTransformer(abc.ABC, t.Generic[_HOOK_RETURN_TYPE, _END_RESULT_TYPE]):
    """Base MOTD transformer class.

    Transformers are responsible for providing a way to generate an alternative
    representation of MOTD, for example, as HTML.

    The methods ``_handle_*`` handle each
    :type:`~mcstatus.motd.components.ParsedMotdComponent` individually.
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
    def __init__(self, *, _is_called_directly: bool = True) -> None:
        if _is_called_directly:
            deprecation_warn(
                obj_name="Calling PlainTransformer directly",
                removal_version="13.0.0",
                extra_msg="Transformers are no longer a part of public API",
            )

    def _handle_str(self, element: str, /) -> str:
        return element


class MinecraftTransformer(PlainTransformer):
    def __init__(self, _is_called_directly: bool = True) -> None:
        if _is_called_directly:
            deprecation_warn(
                obj_name="Calling MinecraftTransformer directly",
                removal_version="13.0.0",
                extra_msg="Transformers are no longer a part of public API",
            )

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
    FORMATTING_TO_HTML_TAGS = {
        Formatting.BOLD: "b",
        Formatting.STRIKETHROUGH: "s",
        Formatting.ITALIC: "i",
        Formatting.UNDERLINED: "u",
    }

    def __init__(self, *, bedrock: bool = False, _is_called_directly: bool = True) -> None:
        if _is_called_directly:
            # NOTE: don't forget to remove the default value for `bedrock` argument
            deprecation_warn(
                obj_name="Calling HtmlTransformer directly",
                removal_version="13.0.0",
                extra_msg="Transformers are no longer a part of public API",
            )

        self.bedrock = bedrock
        self.on_reset: list[str] = []

    def transform(self, motd_components: Sequence[ParsedMotdComponent]) -> str:
        self.on_reset = []
        return super().transform(motd_components)

    def _format_output(self, results: list[str]) -> str:
        return "<p>" + super()._format_output(results) + "".join(self.on_reset) + "</p>"

    def _handle_str(self, element: str, /) -> str:
        return element.replace("\n", "<br>")

    def _handle_minecraft_color(self, element: MinecraftColor, /) -> str:
        color_map = MINECRAFT_COLOR_TO_RGB_BEDROCK if self.bedrock else MINECRAFT_COLOR_TO_RGB_JAVA
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
    MINECRAFT_COLOR_TO_RGB_JAVA = {key: foreground for key, (foreground, _background) in MINECRAFT_COLOR_TO_RGB_JAVA.items()}
    MINECRAFT_COLOR_TO_RGB_BEDROCK = {
        key: foreground for key, (foreground, _background) in MINECRAFT_COLOR_TO_RGB_BEDROCK.items()
    }

    def __init__(self, *, bedrock: bool = True, _is_called_directly: bool = True) -> None:
        if _is_called_directly:
            # NOTE: don't forget to remove the default value for `bedrock` argument
            deprecation_warn(
                obj_name="Calling AnsiTransformer directly",
                removal_version="13.0.0",
                extra_msg="Transformers are no longer a part of public API",
            )

        self.bedrock = bedrock

    def ansi_color(self, color: tuple[int, int, int] | MinecraftColor) -> str:
        """Transform RGB color to ANSI color code."""
        if isinstance(color, MinecraftColor):
            color_to_rgb = self.MINECRAFT_COLOR_TO_RGB_BEDROCK if self.bedrock else self.MINECRAFT_COLOR_TO_RGB_JAVA
            color = color_to_rgb[color]

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
