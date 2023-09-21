from __future__ import annotations

from contextlib import ExitStack
from unittest import mock

import pytest

from mcstatus.motd import Motd
from mcstatus.motd.components import Formatting, MinecraftColor, TranslationTag, WebColor
from mcstatus.motd.simplifies import (
    get_double_colors,
    get_double_items,
    get_empty_text,
    get_end_non_text,
    get_formatting_before_color,
    get_unused_elements,
)


class TestMotdSimplifies:
    def test_get_unused_elements_call_every_simplifier(self):
        with ExitStack() as stack:
            mocked = []
            for simplifier in [
                get_double_items.__name__,
                get_double_colors.__name__,
                get_formatting_before_color.__name__,
                get_empty_text.__name__,
                get_end_non_text.__name__,
            ]:
                mocked.append(stack.enter_context(mock.patch("mcstatus.motd.simplifies." + simplifier)))

            get_unused_elements([])

            for simplifier in mocked:
                simplifier.assert_called()

    def test_simplify_returns_new_instance(self):
        parsed = ["", Formatting.RESET]
        obj = Motd(parsed.copy(), raw="")
        assert obj.simplify().parsed == []
        assert obj.parsed == parsed

    def test_simplifies_work(self):
        get_unused_elements(["a", "b", "c"])

    def test_simplify_runs_few_times(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r1051658497`_."""
        obj = Motd([Formatting.BOLD, "", Formatting.RESET, "", MinecraftColor.RED, ""], raw="")
        assert obj.simplify() == Motd([], raw="")

    @pytest.mark.parametrize("first", (MinecraftColor.RED, WebColor.from_hex(hex="#ff0000")))
    @pytest.mark.parametrize("second", (MinecraftColor.BLUE, WebColor.from_hex(hex="#dd0220")))
    def test_get_double_colors(self, first, second):
        assert get_double_colors([first, second]) == {0}

    @pytest.mark.parametrize("first", (MinecraftColor.RED, WebColor.from_hex(hex="#ff0000")))
    @pytest.mark.parametrize("second", (MinecraftColor.BLUE, WebColor.from_hex(hex="#dd0220")))
    @pytest.mark.parametrize("third", (MinecraftColor.BLUE, WebColor.from_hex(hex="dd0220")))
    def test_get_double_colors_with_three_items(self, first, second, third):
        assert get_double_colors([first, second, third]) == {0, 1}

    @pytest.mark.parametrize("first", (MinecraftColor.RED, WebColor.from_hex(hex="#ff0000")))
    @pytest.mark.parametrize("second", (MinecraftColor.BLUE, WebColor.from_hex(hex="#dd0220")))
    def test_get_double_colors_with_no_double_colors(self, first, second):
        assert get_double_colors([first, "", second]) == set()

    @pytest.mark.parametrize("last_item", (MinecraftColor.RED, WebColor.from_hex(hex="#ff0000")))
    def test_get_formatting_before_color(self, last_item):
        assert get_formatting_before_color([Formatting.BOLD, last_item]) == {0}

    @pytest.mark.parametrize("first_item", (Formatting.RESET, MinecraftColor.RED, WebColor.from_hex(hex="#ff0000"), "abc"))
    def test_get_formatting_before_color_without_formatting_before_color(self, first_item):
        assert get_formatting_before_color([first_item, "abc", MinecraftColor.WHITE]) == set()

    def test_skip_get_formatting_before_color(self):
        assert get_formatting_before_color(["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi"]) == set()

    @pytest.mark.parametrize("last_item", (MinecraftColor.RED, WebColor.from_hex(hex="#ff0000")))
    def test_get_formatting_before_color_if_space_between(self, last_item):
        assert get_formatting_before_color([Formatting.BOLD, " ", last_item]) == {0}

    def test_get_empty_text_removes_empty_string(self):
        assert get_empty_text([Formatting.BOLD, "", Formatting.RESET, "", MinecraftColor.RED, ""]) == {1, 3, 5}

    def test_two_formattings_before_minecraft_color(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r1048476090`_."""
        assert get_formatting_before_color([Formatting.BOLD, Formatting.ITALIC, MinecraftColor.RED]) == {0, 1}

    def test_two_formattings_one_by_one(self):
        obj = Motd([Formatting.BOLD, Formatting.ITALIC], raw="")
        assert obj.simplify().parsed == []

    @pytest.mark.parametrize("item", (Formatting.RESET, MinecraftColor.RED, WebColor.from_hex(hex="#ff1234")))
    def test_dont_remove_empty_text(self, item):
        assert get_empty_text([item]) == set()

    @pytest.mark.parametrize("last_item", (Formatting.RESET, MinecraftColor.RED, WebColor.from_hex(hex="#ff0000")))
    def test_non_text_in_the_end(self, last_item):
        assert get_end_non_text(["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi", last_item]) == {5}

    def test_translation_tag_in_the_end(self):
        assert get_end_non_text(["abc", Formatting.BOLD, "def", Formatting.RESET, "ghi", TranslationTag("key")]) == set()

    def test_no_conflict_on_poping_items(self):
        """See `https://github.com/py-mine/mcstatus/pull/335#discussion_r1045303652`_."""
        obj = Motd(["0", "1"], raw="")
        call_count = 0

        def remove_first_element(*_, **__):
            nonlocal call_count
            call_count += 1
            if call_count in (1, 2):
                return {0}
            return set()

        with ExitStack() as stack:
            for simplifier in [
                get_double_items.__name__,
                get_double_colors.__name__,
                get_formatting_before_color.__name__,
                get_empty_text.__name__,
                get_end_non_text.__name__,
            ]:
                stack.enter_context(mock.patch("mcstatus.motd.simplifies." + simplifier, remove_first_element))
            assert obj.simplify().parsed == ["1"]

    def test_simplify_function_provides_the_same_raw(self):
        obj = object()
        assert Motd([], raw=obj).simplify().raw is obj  # type: ignore # Invalid argument type

    def test_simplify_do_not_remove_string_contains_only_spaces(self):
        """Those can be used as delimiters."""
        assert Motd([" " * 20], raw="").simplify().parsed == [" " * 20]

    def test_simplify_meaningless_resets_and_colors(self):
        assert Motd.parse("&a1&a2&a3").simplify().parsed == [MinecraftColor.GREEN, "123"]

    def test_remove_formatting_reset_if_there_was_no_color_or_formatting(self):
        motd = Motd.parse({"text": "123", "extra": [{"text": "123"}]})
        assert motd.parsed == ["123", Formatting.RESET, "123", Formatting.RESET]
        assert motd.simplify().parsed == ["123123"]

    def test_squash_nearby_strings(self):
        assert Motd(["123", "123", "123"], raw="").simplify().parsed == ["123123123"]
