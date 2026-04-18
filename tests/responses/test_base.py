import pytest

from mcstatus.responses import BaseStatusResponse


class TestMCStatusResponse:
    def test_raises_not_implemented_error_on_build(self):
        with pytest.raises(NotImplementedError):
            _ = BaseStatusResponse.build({"foo": "bar"})  # pyright: ignore[reportAbstractUsage]
