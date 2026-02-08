from typing import TypeVar

__all__ = ["or_none"]


T = TypeVar("T")


def or_none(*args: T) -> T | None:
    """Return the first non-None argument.

    This function is similar to the standard inline ``or`` operator, while
    treating falsey values (such as ``0``, ``''``, or ``False``) as valid
    results rather than skipping them. It only skips ``None`` values.

    This is useful when selecting between optional values that may be empty
    but still meaningful.

    Example:
        .. code-block:: py
            >>> or_none("", 0, "fallback")
            ''
            >>> or_none(None, None, "value")
            'value'
            >>> or_none(None, None)
            None

        This is often useful when working with dict.get, e.g.:

        .. code-block:: py
            >>> mydict = {"a": ""}
            >>> mydict.get("a") or mydict.get("b")
            None  # expected ''!
            >>> or_none(mydict.get("a"), mydict.get("b"))
            ''
    """
    for arg in args:
        if arg is not None:
            return arg
    return None
