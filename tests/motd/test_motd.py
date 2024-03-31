from __future__ import annotations

import pytest

from mcstatus.motd import Motd
from mcstatus.motd.components import Formatting, MinecraftColor, TranslationTag, WebColor
from mcstatus.responses import RawJavaResponseMotdWhenDict


class TestMotdParse:
    def test_correct_result(self, source):
        assert Motd.parse(source) == Motd(
            [
                "top", Formatting.RESET,
                "1", Formatting.RESET,
                WebColor.from_hex(hex="#b3eeff"), "2", Formatting.RESET,
                MinecraftColor.BLACK, Formatting.OBFUSCATED, "3", Formatting.RESET,
                MinecraftColor.DARK_BLUE, Formatting.BOLD, Formatting.STRIKETHROUGH, "4", Formatting.RESET,
                MinecraftColor.DARK_GREEN, Formatting.ITALIC, "5", Formatting.RESET,
                MinecraftColor.DARK_AQUA, Formatting.UNDERLINED, "6", Formatting.RESET,
                MinecraftColor.DARK_AQUA, "7", Formatting.RESET,
                MinecraftColor.DARK_RED, "8", Formatting.RESET,
                MinecraftColor.DARK_PURPLE, "9", Formatting.RESET,
                MinecraftColor.GOLD, "10", Formatting.RESET,
                MinecraftColor.GRAY, "11", Formatting.RESET,
                MinecraftColor.DARK_GRAY, "12", Formatting.RESET,
                MinecraftColor.BLUE, "13", Formatting.RESET,
                MinecraftColor.GREEN, "14", Formatting.RESET,
                MinecraftColor.AQUA, "15", Formatting.RESET,
                MinecraftColor.RED, "16", Formatting.RESET,
                MinecraftColor.LIGHT_PURPLE, "17", Formatting.RESET,
                MinecraftColor.YELLOW, "18", Formatting.RESET,
                MinecraftColor.WHITE, "19", Formatting.RESET,
                MinecraftColor.MINECOIN_GOLD, "20", Formatting.RESET,
                Formatting.RESET, "21", Formatting.RESET,
                TranslationTag("some.random.string"), Formatting.RESET,
            ],
            raw=source,
        )  # fmt: skip

    @pytest.mark.parametrize("bedrock", (True, False))
    def test_bedrock_parameter_nothing_changes(self, bedrock: bool):
        assert Motd.parse([{"color": "minecoin_gold", "text": " "}], bedrock=bedrock).parsed == [
            Formatting.RESET,
            MinecraftColor.MINECOIN_GOLD,
            " ",
            Formatting.RESET,
        ]

    @pytest.mark.parametrize("bedrock,expected", ((True, MinecraftColor.MINECOIN_GOLD), (False, "&g")))
    def test_parse_as_str_ignore_minecoin_gold_on_java(self, bedrock: bool, expected):
        assert Motd.parse("&g", bedrock=bedrock).parsed == [expected]

    def test_parse_incorrect_color_passes(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r985084188`_."""
        assert Motd.parse("&j").parsed == ["&j"]

    def test_parse_uppercase_passes(self):
        assert Motd.parse("&A").parsed == ["", MinecraftColor.GREEN, ""]

    @pytest.mark.parametrize(
        "input,expected", [("", [""]), ([], [Formatting.RESET]), ({"extra": [], "text": ""}, ["", Formatting.RESET])]
    )
    def test_empty_input_also_empty_raw(self, input, expected):
        assert Motd.parse(input).parsed == expected

    def test_top_level_formatting_applies_to_all_in_extra(self) -> None:
        """As described `here <https://wiki.vg/Chat#Inheritance>`_."""
        assert Motd.parse({"text": "top", "bold": True, "extra": [{"color": "red", "text": "not top"}]}).parsed == [
            Formatting.BOLD,
            "top",
            Formatting.RESET,
            Formatting.BOLD,
            MinecraftColor.RED,
            "not top",
            Formatting.RESET,
        ]

    def test_top_level_formatting_can_be_overwrote(self) -> None:
        """As described `here <https://wiki.vg/Chat#Inheritance>`_."""
        assert Motd.parse(
            {"text": "bold", "bold": True, "extra": [{"color": "red", "bold": False, "text": "not bold"}]}
        ).parsed == [
            Formatting.BOLD,
            "bold",
            Formatting.RESET,
            MinecraftColor.RED,
            "not bold",
            Formatting.RESET,
        ]

    def test_top_level_formatting_applies_to_string_inside_extra(self) -> None:
        """Although, it is probably a bug in some modded cores, Minecraft supports it, and we should as well.

        See `#711 <https://github.com/py-mine/mcstatus/issues/711>`_.
        """
        assert Motd.parse({"text": "top", "bold": True, "extra": ["not top"]}).parsed == [
            Formatting.BOLD,
            "top",
            Formatting.RESET,
            Formatting.BOLD,
            "not top",
        ]

    def test_formatting_key_set_to_false_here_without_it_being_set_to_true_before(self) -> None:
        """Some servers set the formatting keys to false here, even without it ever being set to true before.

        See `https://github.com/py-mine/mcstatus/pull/335#discussion_r985086953`_.
        """
        assert Motd.parse({"color": "red", "bold": False, "text": "not bold"}).parsed == [
            MinecraftColor.RED,
            "not bold",
            Formatting.RESET,
        ]

    def test_translate_string(self):
        assert Motd.parse(RawJavaResponseMotdWhenDict(translate="the key")).parsed == [
            TranslationTag("the key"),
            Formatting.RESET,
        ]

    def test_short_text_is_not_considered_as_color(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r984535349`_."""
        assert Motd.parse("a").parsed == ["a"]

    def test_text_field_contains_formatting(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#issuecomment-1264191303`_."""
        assert Motd.parse({"text": "&aHello!"}).parsed == ["", MinecraftColor.GREEN, "Hello!", Formatting.RESET]

    def test_invalid_raw_input(self):
        with pytest.raises(TypeError):
            Motd.parse(object())  # type: ignore

    def test_invalid_color(self):
        with pytest.raises(ValueError):
            Motd._parse_color("a")

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
            Formatting.RESET, Formatting.RESET, Formatting.RESET,
            "1",
            Formatting.RESET, Formatting.RESET,
            "2",
            Formatting.RESET, Formatting.RESET,
            "3",
            Formatting.RESET, Formatting.RESET, Formatting.RESET,
            "4",
            Formatting.RESET, Formatting.RESET,
            "5",
            Formatting.RESET, Formatting.RESET,
            "6",
            Formatting.RESET, Formatting.RESET, Formatting.RESET,
            "7",
            Formatting.RESET, Formatting.RESET,
            "8",
            Formatting.RESET, Formatting.RESET,
            "9",
            Formatting.RESET,
        ]  # fmt: skip

    def test_raw_attribute(self, source):
        motd = Motd.parse(source)
        assert motd.raw == source
