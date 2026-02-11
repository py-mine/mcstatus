from __future__ import annotations

import pytest

from mcstatus.motd.components import WebColor


class TestWebColor:
    @pytest.mark.parametrize(
        ("hex_", "rgb"),
        [
            ("#bfff00", (191, 255, 0)),
            ("#00ff80", (0, 255, 128)),
            ("#4000ff", (64, 0, 255)),
        ],
    )
    def test_hex_to_rgb_correct(self, hex_, rgb):
        assert WebColor.from_hex(hex=hex_).rgb == rgb

    @pytest.mark.parametrize(
        ("hex_", "rgb"),
        [
            ("#bfff00", (191, 255, 0)),
            ("#00ff80", (0, 255, 128)),
            ("#4000ff", (64, 0, 255)),
        ],
    )
    def test_rgb_to_hex_correct(self, hex_, rgb):
        assert WebColor.from_rgb(rgb=rgb).hex == hex_

    def test_hex_in_output_has_number_sign(self):
        assert WebColor.from_hex(hex="#bfff00").hex == "#bfff00"
        assert WebColor.from_hex(hex="4000ff").hex == "#4000ff"

    def test_fail_on_incorrect_hex(self):
        with pytest.raises(ValueError, match=r"^Got too long/short hex color: '#abcd'$"):
            WebColor.from_hex(hex="abcd")

    @pytest.mark.parametrize("length", [0, 1, 2, 4, 5, 7, 8, 9, 10])
    def test_fail_on_too_long_or_too_short_hex(self, length: int):
        color = "a" * length
        with pytest.raises(ValueError, match=f"^Got too long/short hex color: '#{color}'$"):
            WebColor.from_hex(hex="a" * length)

    def test_fail_on_incorrect_rgb(self):
        with pytest.raises(ValueError, match=r"^RGB color byte out of its 8-bit range \(0-255\) for red \(value=-23\)$"):
            WebColor.from_rgb(rgb=(-23, 699, 1000))

    def test_3_symbols_hex(self):
        assert WebColor.from_hex("a1b").hex == "#aa11bb"
