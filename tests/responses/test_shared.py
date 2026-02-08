import pytest

from mcstatus.responses import BaseStatusResponse


class TestMCStatusResponse:
    def test_raises_not_implemented_error_on_build(self):
        with pytest.raises(NotImplementedError):
            BaseStatusResponse.build({"foo": "bar"})  # type: ignore[reportAbstractUsage]


def test_deprecated_import_path():
    with pytest.deprecated_call(match=r"mcstatus\.responses"):
        import mcstatus.status_response  # noqa: F401, PLC0415
