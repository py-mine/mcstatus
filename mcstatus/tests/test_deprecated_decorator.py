import warnings

import pytest

from mcstatus.utils import deprecated


def test_deprecated_function_produces_warning():
    f = deprecated(lambda: None)

    with warnings.catch_warnings(record=True) as w:
        f()
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message).lower()


def test_deprecated_class_produces_warning():
    dep_cls = deprecated(type("TestCls", (), {"foo": lambda: None}), methods=["foo"])

    with warnings.catch_warnings(record=True) as w:
        dep_cls.foo()
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message).lower()


def test_deprecated_function_return_result():
    f = deprecated(lambda x: x)

    with warnings.catch_warnings():
        result = f(10)

    assert result == 10


def test_deprecated_class_return_result():
    dep_cls = deprecated(type("TestCls", (), {"foo": lambda x: x}), methods=["foo"])

    with warnings.catch_warnings():
        result = dep_cls.foo(10)

    assert result == 10


def test_deprecated_function_with_methods():
    with pytest.raises(ValueError):
        deprecated(lambda: None, methods=["__str__"])


def test_deprecated_class_without_methods():
    with pytest.raises(ValueError):
        deprecated(type("TestCls", (), {"foo": lambda x: x}))


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
    f = deprecated(lambda: None, **arguments)

    with warnings.catch_warnings(record=True) as w:
        f()
        warning_message = str(w[-1].message)

        for value in arguments.values():
            assert value in warning_message
