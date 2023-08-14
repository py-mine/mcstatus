from __future__ import annotations

import typing
from collections.abc import Callable

import pytest

from mcstatus.motd import Motd
from mcstatus.motd.transformers import AnsiTransformer, HtmlTransformer, MinecraftTransformer, PlainTransformer

if typing.TYPE_CHECKING:
    from mcstatus.responses import RawJavaResponseMotd


class TestMotdPlain:
    @pytest.fixture(scope="class", params=["attribute", "function"])
    def result(self, request) -> Callable[[str | RawJavaResponseMotd], str]:
        if request.param == "attribute":
            return lambda text: Motd.parse(text).to_plain()
        else:
            return lambda text: PlainTransformer().transform(Motd.parse(text).parsed)

    def test_plain_text(self, result):
        assert result("plain") == "plain"

    def test_removes_colors(self, result):
        assert result("&1&ltext") == "text"

    def test_skip_web_colors(self, result):
        assert result({"extra": [{"color": "#4000ff", "text": "colored text"}], "text": ""}) == "colored text"

    def test_skip_minecraft_colors(self, result):
        assert result({"extra": [{"color": "red", "text": "colored text"}], "text": ""}) == "colored text"


class TestMotdMinecraft:
    @pytest.fixture(scope="class", params=["attribute", "function"])
    def result(self, request) -> Callable[[str | RawJavaResponseMotd], str]:
        if request.param == "attribute":
            return lambda text: Motd.parse(text).to_minecraft()
        else:
            return lambda text: MinecraftTransformer().transform(Motd.parse(text).parsed)

    @pytest.mark.parametrize("motd", ["&1&2&3", "§123§5bc", "§1§2§3"])
    def test_return_the_same(self, motd: str, result):
        assert result(motd) == motd.replace("&", "§")

    def test_skip_web_colors(self, result):
        assert result({"extra": [{"color": "#4000ff", "text": "colored text"}], "text": ""}) == "§rcolored text§r"


class TestMotdHTML:
    @pytest.fixture(scope="class", params=["attribute", "class"])
    def result(self, request) -> Callable[[str, bool], str]:
        if request.param == "attribute":
            return lambda text, bedrock: Motd.parse(text, bedrock=bedrock).to_html()
        else:
            return lambda text, bedrock: HtmlTransformer(bedrock=bedrock).transform(Motd.parse(text, bedrock=bedrock).parsed)

    @pytest.mark.parametrize("bedrock", (True, False))
    def test_correct_output(self, result: Callable[["str | dict", bool], str], source, bedrock: bool):
        assert result(source, bedrock) == (
            "<p>top"
            "1<span style='color:rgb(179, 238, 255)'>2</span>"
            "<span style='color:rgb(0, 0, 0);text-shadow:0 0 1px rgb(0, 0, 0)'><span class=obfuscated>3</span>"
            "</span>"
            "<span style='color:rgb(0, 0, 170);text-shadow:0 0 1px rgb(0, 0, 42)'><b><s>4</span></b></s>"
            "<span style='color:rgb(0, 170, 0);text-shadow:0 0 1px rgb(0, 42, 0)'><i>5</span></i>"
            "<span style='color:rgb(0, 170, 170);text-shadow:0 0 1px rgb(0, 42, 42)'><u>6</span></u>"
            "<span style='color:rgb(0, 170, 170);text-shadow:0 0 1px rgb(0, 42, 42)'>7</span>"
            "<span style='color:rgb(170, 0, 0);text-shadow:0 0 1px rgb(42, 0, 0)'>8</span>"
            "<span style='color:rgb(170, 0, 170);text-shadow:0 0 1px rgb(42, 0, 42)'>9</span>"
            "<span style='color:rgb(255, 170, 0);text-shadow:0 0 1px rgb"
            + str((64, 42, 0) if bedrock else (42, 42, 0))
            + "'>10</span>"
            "<span style='color:rgb(170, 170, 170);text-shadow:0 0 1px rgb(42, 42, 42)'>11</span>"
            "<span style='color:rgb(85, 85, 85);text-shadow:0 0 1px rgb(21, 21, 21)'>12</span>"
            "<span style='color:rgb(85, 85, 255);text-shadow:0 0 1px rgb(21, 21, 63)'>13</span>"
            "<span style='color:rgb(85, 255, 85);text-shadow:0 0 1px rgb(21, 63, 21)'>14</span>"
            "<span style='color:rgb(85, 255, 255);text-shadow:0 0 1px rgb(21, 63, 63)'>15</span>"
            "<span style='color:rgb(255, 85, 85);text-shadow:0 0 1px rgb(63, 21, 21)'>16</span>"
            "<span style='color:rgb(255, 85, 255);text-shadow:0 0 1px rgb(63, 21, 63)'>17</span>"
            "<span style='color:rgb(255, 255, 85);text-shadow:0 0 1px rgb(63, 63, 21)'>18</span>"
            "<span style='color:rgb(255, 255, 255);text-shadow:0 0 1px rgb(63, 63, 63)'>19</span>"
            "<span style='color:rgb(221, 214, 5);text-shadow:0 0 1px rgb(55, 53, 1)'>20</span>"
            "21</p>"
        )


class TestMotdAnsi:
    @pytest.fixture(scope="class", params=[True, False])
    def bedrock(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def expected_result(self):
        return (
            "\033[0mtop\033[0m"
            "1\033[0m"
            "\033[38;2;179;238;255m2\033[0m\033[0m"
            "\033[38;2;0;0;0m\033[5m3\033[0m\033[0m"
            "\033[38;2;0;0;170m\033[1m\033[9m4\033[0m\033[0m"
            "\033[38;2;0;170;0m\033[3m5\033[0m\033[0m"
            "\033[38;2;0;170;170m\033[4m6\033[0m\033[0m"
            "\033[38;2;0;170;170m7\033[0m\033[0m"
            "\033[38;2;170;0;0m8\033[0m\033[0m"
            "\033[38;2;170;0;170m9\033[0m\033[0m"
            "\033[38;2;255;170;0m10\033[0m\033[0m"
            "\033[38;2;170;170;170m11\033[0m\033[0m"
            "\033[38;2;85;85;85m12\033[0m\033[0m"
            "\033[38;2;85;85;255m13\033[0m\033[0m"
            "\033[38;2;85;255;85m14\033[0m\033[0m"
            "\033[38;2;85;255;255m15\033[0m\033[0m"
            "\033[38;2;255;85;85m16\033[0m\033[0m"
            "\033[38;2;255;85;255m17\033[0m\033[0m"
            "\033[38;2;255;255;85m18\033[0m\033[0m"
            "\033[38;2;255;255;255m19\033[0m\033[0m"
            "\033[38;2;221;214;5m20\033[0m\033[0m"
            "21\033[0m"
            "\033[0m\033[0m"
        )

    @pytest.fixture(scope="class", params=["attribute", "class"])
    def result(self, request) -> Callable[[str, bool], str]:
        if request.param == "attribute":
            return lambda text, bedrock: Motd.parse(text, bedrock=bedrock).to_ansi()
        else:
            return lambda text, bedrock: AnsiTransformer().transform(Motd.parse(text, bedrock=bedrock).parsed)

    def test_correct_output(self, result: Callable[[str | dict, bool], str], source, bedrock, expected_result):
        assert result(source, bedrock) == expected_result
