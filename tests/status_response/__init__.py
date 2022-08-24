from contextlib import contextmanager
from typing import Iterator

__all__ = ["does_not_raise"]


@contextmanager
def does_not_raise() -> Iterator[None]:
    """Uses in parameterized tests to ensure that the test does not raise an exception."""
    yield
