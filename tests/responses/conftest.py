from __future__ import annotations

import typing

import pytest
from _pytest.python import Function, Metafunc

from tests.responses import BaseResponseTest


def pytest_generate_tests(metafunc: Metafunc) -> None:
    if issubclass(typing.cast(type, metafunc.cls), BaseResponseTest):
        instance = typing.cast(type, metafunc.cls)()
        if metafunc.definition.name not in instance._marks_table().keys():
            return

        marker_name, args = instance._marks_table()[metafunc.definition.name]
        if marker_name != "parametrize":
            return  # other markers will be handled in `pytest_collection_modifyitems`
        metafunc.parametrize(*args)


def pytest_collection_modifyitems(items: list[Function]) -> None:
    for item in items:
        if isinstance(item.instance, BaseResponseTest):
            if item.obj.__name__ not in item.instance._marks_table().keys():
                continue

            marker_name, args = item.instance._marks_table()[item.obj.__name__]
            if marker_name == "parametrize":
                continue
            item.add_marker(getattr(pytest.mark, marker_name)(*args))
