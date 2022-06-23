from contextlib import ExitStack
from types import GeneratorType
from unittest import mock

import pytest

from mcstatus.motd import Formatting, MinecraftColor, Motd, MotdSimplifies, TranslateString, WebColor


@pytest.fixture(scope="session")
def source():
    """Returns ultimate dict with almost all possible aspects, which we should support.

    If attribute can handle all from this dict, it's fully tested.
    Parser should have more tests, on additional features.
    """
    return {
        "extra": [
            {"text": "1"},
            {"color": "#b3eeff", "text": "2"},
            {"obfuscated": True, "color": "black", "text": "3"},
            {"bold": True, "strikethrough": True, "color": "dark_blue", "text": "4"},
            {"italic": True, "color": "dark_green", "text": "5"},
            {"underlined": True, "color": "dark_aqua", "text": "6"},
            {"color": "dark_aqua", "text": "7"},
            {"color": "dark_red", "text": "8"},
            {"color": "dark_purple", "text": "9"},
            {"color": "gold", "text": "10"},
            {"color": "gray", "text": "11"},
            {"color": "dark_gray", "text": "12"},
            {"color": "blue", "text": "13"},
            {"color": "green", "text": "14"},
            {"color": "aqua", "text": "15"},
            {"color": "red", "text": "16"},
            {"color": "light_purple", "text": "17"},
            {"color": "yellow", "text": "18"},
            {"color": "white", "text": "19"},
            {"color": "minecoin_gold", "text": "20"},
            {"translate": "some.random.string"},
        ],
        "text": "top",
    }


class TestWebColor:
    @pytest.mark.parametrize(
        "hex,rgb",
        [
            ("#bfff00", (191, 255, 0)),
            ("#00ff80", (0, 255, 128)),
            ("#4000ff", (64, 0, 255)),
        ],
    )
    def test_hex_to_rgb_correct(self, hex, rgb):
        assert WebColor.parse(hex=hex).rgb == rgb

    @pytest.mark.parametrize(
        "hex,rgb",
        [
            ("#bfff00", (191, 255, 0)),
            ("#00ff80", (0, 255, 128)),
            ("#4000ff", (64, 0, 255)),
        ],
    )
    def test_rgb_to_hex_correct(self, hex, rgb):
        assert WebColor.parse(rgb=rgb).hex == hex

    def test_hex_in_output_has_number_sign(self):
        assert WebColor.parse(hex="#bfff00").hex == "#bfff00"
        assert WebColor.parse(hex="4000ff").hex == "#4000ff"

    def test_fail_on_incorrect_hex(self):
        with pytest.raises(ValueError):
            WebColor.parse(hex="abcd")

    def test_fail_on_incorrect_rgb(self):
        with pytest.raises(ValueError):
            WebColor.parse(rgb=(-23, 699, 1000))

    def test_fail_on_both_none(self):
        with pytest.raises(TypeError):
            WebColor.parse(hex=None, rgb=None)  # type: ignore[assignment]


class TestMotdParse:
    def test_correct_result(self, source):
        assert Motd.parse(source) == Motd(
            [
                # fmt: off
                "top", Formatting.RESET,
                "1", Formatting.RESET,
                WebColor.parse(hex="#b3eeff"), "2", Formatting.RESET,
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
                TranslateString("some.random.string"), Formatting.RESET,
                # fmt: on
            ]
        )

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

    @pytest.mark.parametrize(
        "input,expected", [("", [""]), ([], [Formatting.RESET]), ({"extra": [], "text": ""}, ["", Formatting.RESET])]
    )
    def test_empty_input_also_empty_raw(self, input, expected):
        assert Motd.parse(input).parsed == expected

    def test_top_level_formatting_applies_to_all_in_extra(self) -> None:
        """As described here https://wiki.vg/Chat#Inheritance."""
        assert Motd.parse({"text": "top", "bold": True, "extra": [{"color": "red", "text": "not top"}]}).parsed == [
            Formatting.BOLD,
            "top",
            Formatting.RESET,
            Formatting.BOLD,
            MinecraftColor.RED,
            "not top",
            Formatting.RESET,
        ]

    @pytest.mark.parametrize("false", (False, "false"))
    def test_top_level_formatting_can_be_overwrited(self, false) -> None:
        """As described here https://wiki.vg/Chat#Inheritance."""
        assert Motd.parse(
            {"text": "bold", "bold": True, "extra": [{"color": "red", "bold": false, "text": "not bold"}]}
        ).parsed == [
            Formatting.BOLD,
            "bold",
            Formatting.RESET,
            MinecraftColor.RED,
            "not bold",
            Formatting.RESET,
        ]

    def test_translate_string(self):
        assert Motd.parse({"translate": "the key"}).parsed == [TranslateString("the key"), Formatting.RESET]


class TestMotdSimplifies:
    def test_simplifies_return_generator(self):
        obj = MotdSimplifies([])
        assert isinstance(obj.simplifies, GeneratorType)

    def test_simplifies_list_have_all_functions(self):
        obj = MotdSimplifies([])
        assert list(obj.simplifies) == [
            getattr(obj, item) for item in dir(obj) if callable(getattr(obj, item)) and not item.startswith("_")
        ]

    def test_method_call_every_simplifier(self):
        with ExitStack() as stack:
            mocked = []
            obj = MotdSimplifies([])
            for simplifier in [item for item in dir(obj) if callable(getattr(obj, item)) and not item.startswith("_")]:
                mocked.append(stack.enter_context(mock.patch("mcstatus.motd.MotdSimplifies." + simplifier)))

            Motd([""]).simplify()

            for simplifier in mocked:
                simplifier.assert_called()

    def test_simplify_returns_self_and_modify_motd(self):
        obj = Motd(["", Formatting.RESET])
        assert obj.simplify() == obj
        assert obj.parsed == []

    def test_simplifies_dont_crash_on_end_or_start(self):
        obj = MotdSimplifies(["a", "b", "c"])
        for simplifier in obj.simplifies:
            simplifier("a", 0)
            simplifier("c", 2)

    def test_remove_double_items(self):
        obj = MotdSimplifies(["a", "a", "b"])
        obj.remove_double_items("a", 0)
        assert obj.parsed == ["a", "b"]

    @pytest.mark.parametrize("first", (MinecraftColor.RED, WebColor.parse(hex="#ff0000")))
    @pytest.mark.parametrize("second", (MinecraftColor.BLUE, WebColor.parse(hex="#dd0220")))
    def test_remove_double_colors(self, first, second):
        obj = MotdSimplifies([first, second])
        obj.remove_double_colors(first, 0)
        assert obj.parsed == [second]

    @pytest.mark.parametrize("first", (MinecraftColor.RED, WebColor.parse(hex="#ff0000")))
    @pytest.mark.parametrize("second", (MinecraftColor.BLUE, WebColor.parse(hex="#dd0220")))
    def test_dont_remove_double_colors(self, first, second):
        obj = MotdSimplifies([first, "", second])
        obj.remove_double_colors(first, 0)
        obj.remove_double_colors("", 1)
        obj.remove_double_colors(second, 2)
        assert obj.parsed == [first, "", second]

    @pytest.mark.parametrize("last_item", (MinecraftColor.RED, WebColor.parse(hex="#ff0000")))
    def test_remove_unused_formatting_before_color(self, last_item):
        obj = MotdSimplifies([Formatting.BOLD, last_item])
        obj.remove_unused_formatting_before_color(Formatting.BOLD, 0)
        assert obj.parsed == [last_item]

    @pytest.mark.parametrize("first_item", (Formatting.RESET, MinecraftColor.RED, WebColor.parse(hex="#ff0000"), "abc"))
    def test_dont_remove_unused_formatting_before_color(self, first_item):
        obj = MotdSimplifies([first_item, "abc", MinecraftColor.WHITE])
        obj.remove_unused_formatting_before_color(first_item, 0)
        assert obj.parsed == [first_item, "abc", MinecraftColor.WHITE]

    @pytest.mark.parametrize("last_item", (Formatting.RESET, MinecraftColor.RED, WebColor.parse(hex="#ff0000")))
    def test_remove_non_text_in_the_end(self, last_item):
        obj = MotdSimplifies(["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi", last_item])
        obj.remove_non_text_in_the_end(last_item, 5)
        assert obj.parsed == ["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi"]

    def test_skip_remove_non_text_in_the_end(self):
        obj = MotdSimplifies(["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi"])
        obj.remove_non_text_in_the_end("ghi", 4)
        assert obj.parsed == ["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi"]

    def test_remove_false_values_removes_empty_string(self):
        obj = MotdSimplifies([""])
        obj.remove_false_values("", 0)
        assert obj.parsed == []

    @pytest.mark.parametrize("item", (Formatting.RESET, MinecraftColor.RED, WebColor.parse(hex="#ff1234")))
    def test_dont_remove_false_values(self, item):
        obj = MotdSimplifies([item])
        obj.remove_false_values(item, 0)
        assert obj.parsed == [item]


class TestMotdPlain:
    def test_plain_text(self):
        assert Motd.parse("plain").plain == "plain"

    def test_removes_colors(self):
        assert Motd.parse("&1&ltext").plain == "text"

    def test_skip_web_colors(self):
        assert Motd.parse({"extra": [{"color": "#4000ff", "text": "colored text"}], "text": ""}).plain == "colored text"

    def test_skip_minecraft_colors(self):
        assert Motd.parse({"extra": [{"color": "red", "text": "colored text"}], "text": ""}).plain == "colored text"


class TestMotdMinecraft:
    @pytest.mark.parametrize("motd", ["&1&2&3", "§123§5bc", "§1§2§3"])
    def test_return_the_same(self, motd: str):
        assert Motd.parse(motd).minecraft == motd.replace("&", "§")

    def test_skip_web_colors(self):
        assert (
            Motd.parse({"extra": [{"color": "#4000ff", "text": "colored text"}], "text": ""}).minecraft == "§rcolored text§r"
        )


class TestMotdHTML:
    @pytest.mark.parametrize("bedrock", (True, False))
    def test_correct_output(self, source, bedrock: bool):
        assert Motd.parse(source, bedrock=bedrock).html == (
            "<p>top"
            "1<span style='color:#b3eeff'>2</span>"
            "<span style='color:#000000;text-shadow:0 0 1px #000000'><span class=obfuscated>3</span></span>"
            "<span style='color:#0000AA;text-shadow:0 0 1px #00002A'><b><s>4</span></b></s>"
            "<span style='color:#00AA00;text-shadow:0 0 1px #002A00'><i>5</span></i>"
            "<span style='color:#00AAAA;text-shadow:0 0 1px #002A2A'><u>6</span></u>"
            "<span style='color:#00AAAA;text-shadow:0 0 1px #002A2A'>7</span>"
            "<span style='color:#AA0000;text-shadow:0 0 1px #AA0000'>8</span>"
            "<span style='color:#AA00AA;text-shadow:0 0 1px #2A002A'>9</span>"
            "<span style='color:#FFAA00;text-shadow:0 0 1px #" + ("402A00" if bedrock else "2A2A00") + "'>10</span>"
            "<span style='color:#AAAAAA;text-shadow:0 0 1px #2A2A2A'>11</span>"
            "<span style='color:#555555;text-shadow:0 0 1px #151515'>12</span>"
            "<span style='color:#5555FF;text-shadow:0 0 1px #15153F'>13</span>"
            "<span style='color:#55FF55;text-shadow:0 0 1px #153F15'>14</span>"
            "<span style='color:#55FFFF;text-shadow:0 0 1px #153F3F'>15</span>"
            "<span style='color:#FF5555;text-shadow:0 0 1px #3F1515'>16</span>"
            "<span style='color:#FF55FF;text-shadow:0 0 1px #3F153F'>17</span>"
            "<span style='color:#FFFF55;text-shadow:0 0 1px #3F3F15'>18</span>"
            "<span style='color:#FFFFFF;text-shadow:0 0 1px #3F3F3F'>19</span>"
            "<span style='color:#DDD605;text-shadow:0 0 1px #373501'>20</span>"
            "</p>"
        )


class TestMotdXTerm256:
    @pytest.mark.parametrize("bedrock", (True, False))
    def test_correct_output(self, source, bedrock: bool):
        assert Motd.parse(source, bedrock=bedrock).xterm_256 == (
            r"\e[0mtop\e[0m"
            r"1\e[0m"
            r"\x1b[38;2;179;238;255m2\e[0m"
            r"\x1b[38;2;0;0;0m\x1b[48;2;0;0;0m\e[5m3\e[0m"
            r"\x1b[38;2;0;0;170m\x1b[48;2;0;0;42m\e[1m\e[9m4\e[0m"
            r"\x1b[38;2;0;170;0m\x1b[48;2;0;42;0m\e[3m5\e[0m"
            r"\x1b[38;2;0;170;170m\x1b[48;2;0;42;42m\e[4m6\e[0m"
            r"\x1b[38;2;0;170;170m\x1b[48;2;0;42;42m7\e[0m"
            r"\x1b[38;2;170;0;0m\x1b[48;2;170;0;0m8\e[0m"
            r"\x1b[38;2;170;0;170m\x1b[48;2;42;0;42m9\e[0m"
            r"\x1b[38;2;255;170;0m\x1b[48;2;" + ("64;42;0" if bedrock else "42;42;0") + r"m10\e[0m"
            r"\x1b[38;2;170;170;170m\x1b[48;2;42;42;42m11\e[0m"
            r"\x1b[38;2;85;85;85m\x1b[48;2;21;21;21m12\e[0m"
            r"\x1b[38;2;85;85;255m\x1b[48;2;21;21;63m13\e[0m"
            r"\x1b[38;2;85;255;85m\x1b[48;2;21;63;21m14\e[0m"
            r"\x1b[38;2;85;255;255m\x1b[48;2;21;63;63m15\e[0m"
            r"\x1b[38;2;255;85;85m\x1b[48;2;63;21;21m16\e[0m"
            r"\x1b[38;2;255;85;255m\x1b[48;2;63;21;63m17\e[0m"
            r"\x1b[38;2;255;255;85m\x1b[48;2;63;63;21m18\e[0m"
            r"\x1b[38;2;255;255;255m\x1b[48;2;63;63;63m19\e[0m"
            r"\x1b[38;2;221;214;5m\x1b[48;2;55;53;1m20\e[0m"
            r"\e[0m\e[0m"
        )


class TestMotdANSI:
    def test_correct_output(self, source):
        assert Motd.parse(source).ansi == (
            r"\e[0mtop\e[0m"
            r"1\e[0m"
            r"\x1b[38;2;179;238;255m2\e[0m"
            r"\e[0;30m\e[5m3\e[0m"
            r"\e[0;34m\e[1m\e[9m4\e[0m"
            r"\e[0;32m\e[3m5\e[0m"
            r"\e[0;36m\e[4m6\e[0m"
            r"\e[0;36m7\e[0m"
            r"\e[0;31m8\e[0m"
            r"\e[0;35m9\e[0m"
            r"\e[0;33m10\e[0m"
            r"\e[0;37m11\e[0m"
            r"\e[0;90m12\e[0m"
            r"\e[0;94m13\e[0m"
            r"\e[0;92m14\e[0m"
            r"\e[0;96m15\e[0m"
            r"\e[0;91m16\e[0m"
            r"\e[0;95m17\e[0m"
            r"\e[0;93m18\e[0m"
            r"\e[0;97m19\e[0m"
            r"\e[0;33m20\e[0m"
            r"\e[0m\e[0m"
        )
