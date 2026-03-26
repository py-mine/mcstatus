from __future__ import annotations

import pytest

from mcstatus._protocol.io.base_io import from_twos_complement, to_twos_complement

TWOS_COMPLEMENT_CASES = [
    (-128, 8, 0x80),
    (-2, 8, 0xFE),
    (-1, 8, 0xFF),
    (0, 8, 0x00),
    (1, 8, 0x01),
    (127, 8, 0x7F),
    (-(2**15), 16, 0x8000),
    (-1, 16, 0xFFFF),
    ((2**15) - 1, 16, 0x7FFF),
    (-(2**31), 32, 0x80000000),
    (-1, 32, 0xFFFFFFFF),
    ((2**31) - 1, 32, 0x7FFFFFFF),
    (-(2**63), 64, 0x8000000000000000),
    (-9_876_543_210_123_456, 64, 0xFFDCE956165A0F40),
    (-1, 64, 0xFFFFFFFFFFFFFFFF),
    (0, 64, 0x0000000000000000),
    (9_876_543_210_123_456, 64, 0x002316A9E9A5F0C0),
    ((2**63) - 1, 64, 0x7FFFFFFFFFFFFFFF),
]


@pytest.mark.parametrize(
    ("number", "bits", "expected_twos"),
    TWOS_COMPLEMENT_CASES,
)
def test_to_twos_complement_matches_expected_values(number: int, bits: int, expected_twos: int):
    assert to_twos_complement(number, bits=bits) == expected_twos


@pytest.mark.parametrize(
    ("twos_value", "bits", "expected_number"),
    [(twos_value, bits, number) for number, bits, twos_value in TWOS_COMPLEMENT_CASES],
)
def test_from_twos_complement_matches_expected_values(twos_value: int, bits: int, expected_number: int):
    assert from_twos_complement(twos_value, bits=bits) == expected_number


@pytest.mark.parametrize(
    ("number", "bits"),
    [
        (-129, 8),
        (128, 8),
        (-(2**31) - 1, 32),
        (2**31, 32),
        (-(2**63) - 1, 64),
        (2**63, 64),
    ],
)
def test_to_twos_complement_rejects_out_of_range(number: int, bits: int):
    with pytest.raises(ValueError, match=r"out of range"):
        to_twos_complement(number, bits=bits)


@pytest.mark.parametrize(
    ("number", "bits"),
    [
        (-1, 8),
        (256, 8),
        (2**32, 32),
        (2**64, 64),
    ],
)
def test_from_twos_complement_rejects_out_of_range(number: int, bits: int):
    with pytest.raises(ValueError, match=r"out of range"):
        from_twos_complement(number, bits=bits)
