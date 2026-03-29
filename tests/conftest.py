import collections.abc as c
import importlib.metadata
from functools import wraps

import pytest

from mcstatus._utils.deprecation import LIB_NAME, _get_project_version


@pytest.fixture
def patch_project_version(monkeypatch: pytest.MonkeyPatch) -> c.Callable[[str | None], None]:
    """Patch the project version reported by ``importlib.metadata.version``.

    This is used to simulate different project versions for testing purposes.
    If ``version`` is ``None``, a :exc:`PackageNotFoundError` will be raised
    when trying to get the project version.
    """
    orig_version_func = importlib.metadata.version

    def fixture(version: str | None) -> None:
        @wraps(orig_version_func)
        def patched_version_func(distribution_name: str) -> str:
            if distribution_name == LIB_NAME:
                if version is None:
                    raise importlib.metadata.PackageNotFoundError
                return version
            return orig_version_func(distribution_name)

        _get_project_version.cache_clear()
        monkeypatch.setattr(importlib.metadata, "version", patched_version_func)

    return fixture
