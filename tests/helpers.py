import collections.abc as c
import importlib.metadata
from contextlib import contextmanager
from functools import wraps
from unittest.mock import patch

from mcstatus._utils.deprecation import LIB_NAME, _get_project_version


@contextmanager
def patch_project_version(version: str | None) -> c.Generator[None]:
    """Patch the project version reported by ``importlib.metadata.version``.

    This is used to simulate different project versions for testing purposes.
    If ``version`` is ``None``, a :exc:`PackageNotFoundError` will be raised
    when trying to get the project version.
    """
    orig_version_func = importlib.metadata.version

    @wraps(orig_version_func)
    def patched_version_func(distribution_name: str) -> str:
        if distribution_name == LIB_NAME:
            if version is None:
                raise importlib.metadata.PackageNotFoundError
            return version
        return orig_version_func(distribution_name)

    _get_project_version.cache_clear()
    with patch.object(importlib.metadata, "version", new=patched_version_func):
        try:
            yield
        finally:
            _get_project_version.cache_clear()
