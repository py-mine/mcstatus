import typing

import pytest
from _pytest.python import Function, Metafunc

from tests.status_response import BaseStatusResponseTest


def pytest_generate_tests(metafunc: Metafunc) -> None:
    if issubclass(typing.cast(type, metafunc.cls), BaseStatusResponseTest):
        instance = typing.cast(type, metafunc.cls)()
        if metafunc.definition.name not in instance._marks_table().keys():
            return

        marker_name, args = instance._marks_table()[metafunc.definition.name]
        if marker_name != "parametrize":
            return
        metafunc.parametrize(*args)


def pytest_collection_modifyitems(items: list[Function]) -> None:
    for item in items:
        if isinstance(item.instance, BaseStatusResponseTest):
            if item.obj.__name__ not in item.instance._marks_table().keys():
                continue

            marker_name, args = item.instance._marks_table()[item.obj.__name__]
            if marker_name == "parametrize":
                continue
            item.add_marker(getattr(pytest.mark, marker_name)(*args))
