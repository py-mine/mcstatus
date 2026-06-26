from __future__ import annotations

import pytest

from mcstatus.motd import Motd
from mcstatus.motd.components import (
    BedrockFormatting,
    BedrockMinecraftColor,
    JavaFormatting,
    JavaMinecraftColor,
    ParsedMotdComponent,
    TranslationTag,
)
from mcstatus.responses._raw import RawJavaResponseMotd, RawJavaResponseMotdWhenDict


class TestMotdParse:
    def test_correct_result_bedrock(self, source_bedrock: RawJavaResponseMotd):
        assert Motd.parse(source_bedrock, bedrock=True) == Motd(
            [
                "1",
                BedrockMinecraftColor.BLACK, BedrockFormatting.OBFUSCATED, "2",
                BedrockMinecraftColor.DARK_BLUE, BedrockFormatting.BOLD, "3",
                BedrockMinecraftColor.DARK_GREEN, BedrockFormatting.ITALIC, "4",
                BedrockMinecraftColor.DARK_AQUA, "5",
                BedrockMinecraftColor.DARK_RED, "6",
                BedrockMinecraftColor.DARK_PURPLE, "7",
                BedrockMinecraftColor.GOLD, "8",
                BedrockMinecraftColor.GRAY, "9",
                BedrockMinecraftColor.DARK_GRAY, "10",
                BedrockMinecraftColor.BLUE, "11",
                BedrockMinecraftColor.GREEN, "12",
                BedrockMinecraftColor.AQUA, "13",
                BedrockMinecraftColor.RED, "14",
                BedrockMinecraftColor.LIGHT_PURPLE, "15",
                BedrockMinecraftColor.YELLOW, "16",
                BedrockMinecraftColor.WHITE, "17",
                BedrockMinecraftColor.MINECOIN_GOLD, "18",
                BedrockMinecraftColor.MATERIAL_QUARTZ, "19",
                BedrockMinecraftColor.MATERIAL_IRON, "20",
                BedrockMinecraftColor.MATERIAL_NETHERITE, "21",
                BedrockMinecraftColor.MATERIAL_REDSTONE, "22",
                BedrockMinecraftColor.MATERIAL_COPPER, "23",
                BedrockMinecraftColor.MATERIAL_GOLD, "24",
                BedrockMinecraftColor.MATERIAL_EMERALD, "25",
                BedrockMinecraftColor.MATERIAL_DIAMOND, "26",
                BedrockMinecraftColor.MATERIAL_LAPIS, "27",
                BedrockMinecraftColor.MATERIAL_AMETHYST, "28",
                BedrockMinecraftColor.MATERIAL_RESIN, "29",
                BedrockFormatting.RESET, "30",
            ],
            bedrock=True,
            raw=source_bedrock,
        )  # fmt: skip

    @pytest.mark.parametrize(("bedrock", "expected"), [(True, BedrockMinecraftColor.MINECOIN_GOLD), (False, "&g")])
    def test_parse_as_str_ignore_minecoin_gold_on_java(self, bedrock: bool, expected: ParsedMotdComponent):
        assert Motd.parse("&g", bedrock=bedrock).parsed == [expected]

    @pytest.mark.parametrize(("bedrock", "expected"), [(True, BedrockMinecraftColor.MATERIAL_IRON), (False, "&i")])
    def test_parse_as_str_ignore_material_colors_on_java(self, bedrock: bool, expected: ParsedMotdComponent):
        assert Motd.parse("&i", bedrock=bedrock).parsed == [expected]

    @pytest.mark.parametrize(
        ("bedrock", "expected"), [(True, BedrockMinecraftColor.MATERIAL_COPPER), (False, JavaFormatting.UNDERLINED)]
    )
    def test_parse_as_str_underlined_on_java(self, bedrock: bool, expected: ParsedMotdComponent):
        assert Motd.parse("&n", bedrock=bedrock).parsed == [expected]

    def test_parse_incorrect_color_passes(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r985084188`_."""
        assert Motd.parse("&z").parsed == ["&z"]

    def test_parse_uppercase_passes(self):
        assert Motd.parse("&A").parsed == [JavaMinecraftColor.GREEN]

    @pytest.mark.parametrize(
        ("input_", "expected"),
        [("", []), ([], [JavaFormatting.RESET]), ({"extra": [], "text": ""}, [JavaFormatting.RESET])],
    )
    def test_empty_input_also_empty_raw(self, input_: RawJavaResponseMotd, expected: list[ParsedMotdComponent]):
        assert Motd.parse(input_).parsed == expected

    def test_top_level_formatting_applies_to_all_in_extra(self) -> None:
        """As described `here <https://minecraft.wiki/w/Java_Edition_protocol/Chat?direction=prev&oldid=2763844#Inheritance>`_."""
        assert Motd.parse({"text": "top", "bold": True, "extra": [{"color": "red", "text": "not top"}]}).parsed == [
            JavaFormatting.BOLD,
            "top",
            JavaFormatting.RESET,
            JavaFormatting.BOLD,
            JavaMinecraftColor.RED,
            "not top",
            JavaFormatting.RESET,
        ]

    def test_top_level_formatting_can_be_overwrote(self) -> None:
        """As described `here <https://minecraft.wiki/w/Java_Edition_protocol/Chat?direction=prev&oldid=2763844#Inheritance>`_."""
        assert Motd.parse(
            {"text": "bold", "bold": True, "extra": [{"color": "red", "bold": False, "text": "not bold"}]}
        ).parsed == [
            JavaFormatting.BOLD,
            "bold",
            JavaFormatting.RESET,
            JavaMinecraftColor.RED,
            "not bold",
            JavaFormatting.RESET,
        ]

    def test_top_level_formatting_applies_to_string_inside_extra(self) -> None:
        """Although, it is probably a bug in some modded cores, Minecraft supports it, and we should as well.

        See `#711 <https://github.com/py-mine/mcstatus/issues/711>`_.
        """
        assert Motd.parse({"text": "top", "bold": True, "extra": ["not top"]}).parsed == [
            JavaFormatting.BOLD,
            "top",
            JavaFormatting.RESET,
            JavaFormatting.BOLD,
            "not top",
        ]

    def test_formatting_key_set_to_false_here_without_it_being_set_to_true_before(self) -> None:
        """Some servers set the formatting keys to false here, even without it ever being set to true before.

        See `https://github.com/py-mine/mcstatus/pull/335#discussion_r985086953`_.
        """
        assert Motd.parse({"color": "red", "bold": False, "text": "not bold"}).parsed == [
            JavaMinecraftColor.RED,
            "not bold",
            JavaFormatting.RESET,
        ]

    def test_translate_string(self):
        assert Motd.parse(RawJavaResponseMotdWhenDict(translate="the key")).parsed == [
            TranslationTag("the key"),
            JavaFormatting.RESET,
        ]

    def test_short_text_is_not_considered_as_color(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r984535349`_."""
        assert Motd.parse("a").parsed == ["a"]

    def test_text_field_contains_formatting(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#issuecomment-1264191303`_."""
        assert Motd.parse({"text": "&aHello!"}).parsed == [JavaMinecraftColor.GREEN, "Hello!", JavaFormatting.RESET]

    def test_invalid_raw_input(self):
        obj = object()
        with pytest.raises(
            TypeError,
            match=f"^Expected list, string or dict data, got <class 'object'> \\({obj!r}\\), report this!$",
        ):
            _ = Motd.parse(obj)  # pyright: ignore[reportArgumentType]

    def test_parse_invalid_color(self):
        with pytest.raises(ValueError, match=r"^Unable to parse color: 'a', report this!$"):
            _ = Motd._parse_color("a", bedrock=False)

    def test_multiple_times_nested_extras(self):
        """See `https://discord.com/channels/936788458939224094/938591600160956446/1062860329597534258`_."""
        motd = Motd.parse(
            {
                "extra": [
                    {
                        "extra": [
                            {"extra": [{"text": "1"}]},
                            {"extra": [{"text": "2"}]},
                            {"extra": [{"text": "3"}]},
                        ]
                    },
                    {
                        "extra": [
                            {"extra": [{"text": "4"}]},
                            {"extra": [{"text": "5"}]},
                            {"extra": [{"text": "6"}]},
                        ]
                    },
                    {
                        "extra": [
                            {"extra": [{"text": "7"}]},
                            {"extra": [{"text": "8"}]},
                            {"extra": [{"text": "9"}]},
                        ]
                    },
                ]
            }
        )
        assert motd.parsed == [
            JavaFormatting.RESET, JavaFormatting.RESET, JavaFormatting.RESET,
            "1",
            JavaFormatting.RESET, JavaFormatting.RESET,
            "2",
            JavaFormatting.RESET, JavaFormatting.RESET,
            "3",
            JavaFormatting.RESET, JavaFormatting.RESET, JavaFormatting.RESET,
            "4",
            JavaFormatting.RESET, JavaFormatting.RESET,
            "5",
            JavaFormatting.RESET, JavaFormatting.RESET,
            "6",
            JavaFormatting.RESET, JavaFormatting.RESET, JavaFormatting.RESET,
            "7",
            JavaFormatting.RESET, JavaFormatting.RESET,
            "8",
            JavaFormatting.RESET, JavaFormatting.RESET,
            "9",
            JavaFormatting.RESET,
        ]  # fmt: skip

    def test_raw_attribute(self, source_bedrock: RawJavaResponseMotd):
        motd = Motd.parse(source_bedrock, bedrock=True)
        assert motd.raw == source_bedrock
