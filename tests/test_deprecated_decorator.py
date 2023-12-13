import warnings
from typing import Any

import pytest

from mcstatus.utils import deprecated


def test_deprecated_function_produces_warning():
    f = deprecated()(lambda: None)

    with warnings.catch_warnings(record=True) as w:
        f()
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message).lower()


def test_deprecated_class_produces_warning():
    test_cls: Any = type("TestCls", (), {"foo": lambda: None})  # https://github.com/microsoft/pyright/discussions/3438
    dep_cls = deprecated(methods=["foo"])(test_cls)

    with warnings.catch_warnings(record=True) as w:
        dep_cls.foo()
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message).lower()


def test_deprecated_function_return_result():
    f = deprecated()(lambda x: x)

    with warnings.catch_warnings(record=True):
        result = f(10)

    assert result == 10


def test_deprecated_class_return_result():
    test_cls: Any = type("TestCls", (), {"foo": lambda x: x})  # https://github.com/microsoft/pyright/discussions/3438
    dep_cls = deprecated(methods=["foo"])(test_cls)

    with warnings.catch_warnings(record=True):
        result = dep_cls.foo(10)

    assert result == 10


def test_deprecated_function_with_methods():
    with pytest.raises(ValueError):
        deprecated(methods=["__str__"])(lambda: None)


def test_deprecated_class_without_methods():
    test_cls: Any = type("TestCls", (), {"foo": lambda x: x})  # https://github.com/microsoft/pyright/discussions/3438
    with pytest.raises(ValueError):
        deprecated()(test_cls)


@pytest.mark.parametrize(
    "arguments",
    [
        {"replacement": "library.newfunction"},
        {"version": "4.8.1"},
        {"date": "2022-06"},
        {"msg": "Why would you still use this?"},
        {"replacement": "new_function", "version": "0.1.2", "msg": "Function got renamed"},
        {"replacement": "new_function", "date": "2022-11", "msg": "Function got renamed"},
    ],
)
def test_deprecated_arguments(arguments):
    f = deprecated(**arguments)(lambda: None)

    with warnings.catch_warnings(record=True) as w:
        f()
        warning_message = str(w[-1].message)

        for value in arguments.values():
            assert value in warning_message


def test_deprecated_no_call_decorator():
    """This makes sure deprecated decorator can run directly on a function without first being called.

    Usually we use deprecated decorator with arguments like ``@deprecated(msg='hi')``, however this means
    that using it normally would usually require doing ``@deprecated()``, but since all of the arguments
    are optional, we can also support using ``@deprecated``, without calling it first. This tests that
    this behavior is in fact working.
    """
    f = deprecated(lambda x: x)

    with warnings.catch_warnings(record=True) as w:
        result = f(10)
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message).lower()

    assert result == 10
