import pytest

from mcstatus._utils.general import or_none


@pytest.mark.parametrize(
    ("a", "b", "result"),
    [
        (None, None, None),
        (None, "", ""),
        ("", None, ""),
        ("a", "b", "a"),
    ],
)
def test_or_none(a, b, result):
    assert or_none(a, b) == result


def test_or_none_many_arguments():
    assert or_none(*([None] * 100 + ["value"])) == "value"
