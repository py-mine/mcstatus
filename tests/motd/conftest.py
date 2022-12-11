import pytest


@pytest.fixture(scope="session")
def source() -> dict:
    """Returns ultimate dict with almost all possible aspects, which we should support.

    If feature can handle all from this dict, it's fully tested.
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
            {"color": "reset", "text": "21"},
            {"translate": "some.random.string"},
        ],
        "text": "top",
    }
