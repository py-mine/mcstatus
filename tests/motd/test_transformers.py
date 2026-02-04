from __future__ import annotations

import typing
from collections.abc import Callable

import pytest

from mcstatus.motd import Motd
from mcstatus.motd.transformers import AnsiTransformer, HtmlTransformer, MinecraftTransformer, PlainTransformer

if typing.TYPE_CHECKING:
    from mcstatus.responses import RawJavaResponseMotd


class TestMotdPlain:
    @pytest.fixture(scope="class")
    def result(self) -> Callable[[str | RawJavaResponseMotd], str]:
        return lambda text: Motd.parse(text).to_plain()

    def test_plain_text(self, result):
        assert result("plain") == "plain"

    def test_removes_colors(self, result):
        assert result("&1&ltext") == "text"

    def test_skip_web_colors(self, result):
        assert result({"extra": [{"color": "#4000ff", "text": "colored text"}], "text": ""}) == "colored text"

    def test_skip_minecraft_colors(self, result):
        assert result({"extra": [{"color": "red", "text": "colored text"}], "text": ""}) == "colored text"


class TestMotdMinecraft:
    @pytest.fixture(scope="class")
    def result(self) -> Callable[[str | RawJavaResponseMotd], str]:
        return lambda text: Motd.parse(text).to_minecraft()

    @pytest.mark.parametrize("motd", ["&1&2&3", "§123§5bc", "§1§2§3"])
    def test_return_the_same(self, motd: str, result):
        assert result(motd) == motd.replace("&", "§")

    def test_skip_web_colors(self, result):
        assert result({"extra": [{"color": "#4000ff", "text": "colored text"}], "text": ""}) == "§rcolored text§r"


class TestMotdHTML:
    @pytest.fixture(scope="class")
    def result(self) -> Callable[[str, bool], str]:
        return lambda text, bedrock: Motd.parse(text, bedrock=bedrock).to_html()

    def test_correct_output_java(self, result: Callable[["str | dict", bool], str], source_java):
        assert result(source_java, False) == (
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
            "<span style='color:rgb(255, 170, 0);text-shadow:0 0 1px rgb(64, 42, 0)'>10</span>"
            "<span style='color:rgb(170, 170, 170);text-shadow:0 0 1px rgb(42, 42, 42)'>11</span>"
            "<span style='color:rgb(85, 85, 85);text-shadow:0 0 1px rgb(21, 21, 21)'>12</span>"
            "<span style='color:rgb(85, 85, 255);text-shadow:0 0 1px rgb(21, 21, 63)'>13</span>"
            "<span style='color:rgb(85, 255, 85);text-shadow:0 0 1px rgb(21, 63, 21)'>14</span>"
            "<span style='color:rgb(85, 255, 255);text-shadow:0 0 1px rgb(21, 63, 63)'>15</span>"
            "<span style='color:rgb(255, 85, 85);text-shadow:0 0 1px rgb(63, 21, 21)'>16</span>"
            "<span style='color:rgb(255, 85, 255);text-shadow:0 0 1px rgb(63, 21, 63)'>17</span>"
            "<span style='color:rgb(255, 255, 85);text-shadow:0 0 1px rgb(63, 63, 21)'>18</span>"
            "<span style='color:rgb(255, 255, 255);text-shadow:0 0 1px rgb(63, 63, 63)'>19</span>"
            "20</p>"
        )

    def test_correct_output_bedrock(self, result: Callable[["str | dict", bool], str], source_bedrock):
        assert result(source_bedrock, True) == (
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
            "<span style='color:rgb(255, 170, 0);text-shadow:0 0 1px rgb(64, 42, 0)'>10</span>"
            "<span style='color:rgb(198, 198, 198);text-shadow:0 0 1px rgb(49, 49, 49)'>11</span>"
            "<span style='color:rgb(85, 85, 85);text-shadow:0 0 1px rgb(21, 21, 21)'>12</span>"
            "<span style='color:rgb(85, 85, 255);text-shadow:0 0 1px rgb(21, 21, 63)'>13</span>"
            "<span style='color:rgb(85, 255, 85);text-shadow:0 0 1px rgb(21, 63, 21)'>14</span>"
            "<span style='color:rgb(85, 255, 255);text-shadow:0 0 1px rgb(21, 63, 63)'>15</span>"
            "<span style='color:rgb(255, 85, 85);text-shadow:0 0 1px rgb(63, 21, 21)'>16</span>"
            "<span style='color:rgb(255, 85, 255);text-shadow:0 0 1px rgb(63, 21, 63)'>17</span>"
            "<span style='color:rgb(255, 255, 85);text-shadow:0 0 1px rgb(63, 63, 21)'>18</span>"
            "<span style='color:rgb(255, 255, 255);text-shadow:0 0 1px rgb(63, 63, 63)'>19</span>"
            "<span style='color:rgb(221, 214, 5);text-shadow:0 0 1px rgb(55, 53, 1)'>20</span>"
            "<span style='color:rgb(227, 212, 209);text-shadow:0 0 1px rgb(56, 53, 52)'>21</span>"
            "<span style='color:rgb(206, 202, 202);text-shadow:0 0 1px rgb(51, 50, 50)'>22</span>"
            "<span style='color:rgb(68, 58, 59);text-shadow:0 0 1px rgb(17, 14, 14)'>23</span>"
            "<span style='color:rgb(151, 22, 7);text-shadow:0 0 1px rgb(37, 5, 1)'>24</span>"
            "<span style='color:rgb(180, 104, 77);text-shadow:0 0 1px rgb(45, 26, 19)'>25</span>"
            "<span style='color:rgb(222, 177, 45);text-shadow:0 0 1px rgb(55, 44, 11)'>26</span>"
            "<span style='color:rgb(17, 159, 54);text-shadow:0 0 1px rgb(4, 40, 13)'>27</span>"
            "<span style='color:rgb(44, 186, 168);text-shadow:0 0 1px rgb(11, 46, 42)'>28</span>"
            "<span style='color:rgb(33, 73, 123);text-shadow:0 0 1px rgb(8, 18, 30)'>29</span>"
            "<span style='color:rgb(154, 92, 198);text-shadow:0 0 1px rgb(38, 23, 49)'>30</span>"
            "<span style='color:rgb(235, 114, 20);text-shadow:0 0 1px rgb(59, 29, 5)'>31</span>"
            "32</p>"
        )

    def test_new_line_is_br_tag(self):
        motd = Motd.parse("Some cool\ntext")
        assert motd.to_html() == "<p>Some cool<br>text</p>"


class TestMotdAnsi:
    @pytest.fixture(scope="class")
    def result(self) -> Callable[[str, bool], str]:
        return lambda text, bedrock: Motd.parse(text, bedrock=bedrock).to_ansi()

    def test_correct_output_java(self, result: Callable[[str | dict, bool], str], source_java):
        assert result(source_java, False) == (
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
            "20\033[0m"
            "\033[0m\033[0m"
        )

    def test_correct_output_bedrock(self, result: Callable[[str | dict, bool], str], source_bedrock):
        assert result(source_bedrock, True) == (
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
            "\033[38;2;198;198;198m11\033[0m\033[0m"
            "\033[38;2;85;85;85m12\033[0m\033[0m"
            "\033[38;2;85;85;255m13\033[0m\033[0m"
            "\033[38;2;85;255;85m14\033[0m\033[0m"
            "\033[38;2;85;255;255m15\033[0m\033[0m"
            "\033[38;2;255;85;85m16\033[0m\033[0m"
            "\033[38;2;255;85;255m17\033[0m\033[0m"
            "\033[38;2;255;255;85m18\033[0m\033[0m"
            "\033[38;2;255;255;255m19\033[0m\033[0m"
            "\033[38;2;221;214;5m20\033[0m\033[0m"
            "\033[38;2;227;212;209m21\033[0m\033[0m"
            "\033[38;2;206;202;202m22\033[0m\033[0m"
            "\033[38;2;68;58;59m23\033[0m\033[0m"
            "\033[38;2;151;22;7m24\033[0m\033[0m"
            "\033[38;2;180;104;77m25\033[0m\033[0m"
            "\033[38;2;222;177;45m26\033[0m\033[0m"
            "\033[38;2;17;159;54m27\033[0m\033[0m"
            "\033[38;2;44;186;168m28\033[0m\033[0m"
            "\033[38;2;33;73;123m29\033[0m\033[0m"
            "\033[38;2;154;92;198m30\033[0m\033[0m"
            "\033[38;2;235;114;20m31\033[0m\033[0m"
            "32\033[0m"
            "\033[0m\033[0m"
        )

    def test_no_bedrock_argument_deprecation(self):
        with pytest.deprecated_call(match="without an argument is deprecated"):
            AnsiTransformer(_is_called_directly=False)


@pytest.mark.parametrize("transformer", [PlainTransformer, MinecraftTransformer, HtmlTransformer, AnsiTransformer])
def test_is_calling_directly(transformer: type):
    kwargs = {}
    # avoid another deprecation warning
    if transformer in (HtmlTransformer, AnsiTransformer):
        kwargs["bedrock"] = True

    with pytest.deprecated_call(match="Calling transformers directly is deprecated"):
        transformer(**kwargs)
