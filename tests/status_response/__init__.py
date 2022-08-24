from contextlib import contextmanager
from typing import Iterable

__all__ = ["does_not_raise"]


@contextmanager  # type: ignore # iterable type is valid for contextmanager, don't know what wrong with pyright
def does_not_raise() -> Iterable[None]:
    """Uses in parameterized tests to ensure that the test does not raise an exception."""
    yield
