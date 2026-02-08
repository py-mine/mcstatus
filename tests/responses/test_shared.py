import importlib

import pytest

from mcstatus.responses import BaseStatusResponse


class TestMCStatusResponse:
    def test_raises_not_implemented_error_on_build(self):
        with pytest.raises(NotImplementedError):
            BaseStatusResponse.build({"foo": "bar"})  # pyright: ignore[reportAbstractUsage]


@pytest.mark.parametrize(
    ("module", "msg_pattern"),
    [
        ("mcstatus._compat.status_response", r"use mcstatus\.responses instead"),
        ("mcstatus._compat.forge_data", r"use mcstatus\.responses\.forge instead"),
        ("mcstatus._compat.motd_transformers", r"MOTD Transformers are no longer a part of mcstatus public API"),
    ],
)
def test_deprecated_import_path(module: str, msg_pattern: str):
    """Test that the compatibility shims emit deprecation warnings at import time.

    Note that this does NOT test the actual inclusion of the compatibility modules into
    the source tree at build time. This test intentionally only uses the _compat imports,
    as the shim files are only included on build time, which means testing those would
    fail.

    This is intentional, however, it should be noted that the build-time inclusion of
    these modules not unit-tested at all.
    """
    with pytest.deprecated_call(match=msg_pattern):
        importlib.import_module(module)
