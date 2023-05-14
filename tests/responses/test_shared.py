from pytest import raises

from mcstatus.responses import BaseStatusResponse


class TestMCStatusResponse:
    def test_raises_not_implemented_error_on_build(self):
        with raises(NotImplementedError):
            BaseStatusResponse.build({"foo": "bar"})  # type: ignore # method is abstract
