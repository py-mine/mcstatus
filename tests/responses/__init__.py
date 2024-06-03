from __future__ import annotations

import abc
from typing import Any, TypeVar, cast

from mcstatus.responses import BaseStatusResponse

__all__ = ["BaseResponseTest"]
_T = TypeVar("_T", bound="type[BaseResponseTest]")


class BaseResponseTest(abc.ABC):
    EXPECTED_VALUES: list[tuple[str, Any]] | None = None
    EXPECTED_TYPES: list[tuple[str, type]] | None = None
    ATTRIBUTES_IN: list[str] | None = None
    # if we don't specify item in raw answer, target field will be None
    # a first element is a list with fields to remove, and attribute that
    # must be None. a dict is a raw answer to pass into `build` method
    OPTIONAL_FIELDS: tuple[list[tuple[str, str]], dict[str, Any]] | None = None

    def _validate(self) -> None:
        """Perform checks to validate the class."""
        if self.EXPECTED_TYPES is not None and self.EXPECTED_VALUES is not None:
            expected_values_keys = list(dict(self.EXPECTED_VALUES).keys())

            for key in dict(self.EXPECTED_TYPES).keys():
                if key in expected_values_keys:
                    raise ValueError("You can't test the type of attribute, if already testing its value.")

        if self.ATTRIBUTES_IN is not None and (self.EXPECTED_VALUES is not None or self.EXPECTED_TYPES is not None):
            if self.EXPECTED_VALUES and self.EXPECTED_TYPES:
                to_dict = self.EXPECTED_VALUES.copy()
                to_dict.extend(self.EXPECTED_TYPES)
                already_checked_attributes = dict(to_dict).keys()
            else:
                already_checked_attributes = dict(self.EXPECTED_VALUES or self.EXPECTED_TYPES).keys()  # type: ignore

            for attribute_name in self.ATTRIBUTES_IN:
                if attribute_name in already_checked_attributes:
                    raise ValueError("You can't test the type availability, if already testing its value/type.")

    @abc.abstractmethod
    def build(self) -> Any:  # noqa: ANN401
        ...

    # implementations for tests

    def test_values_of_attributes(self, build: BaseStatusResponse, field: str, value: Any) -> None:  # noqa: ANN401
        assert getattr(build, field) == value

    def test_types_of_attributes(self, build: BaseStatusResponse, field: str, type_: type) -> None:
        assert isinstance(getattr(build, field), type_)

    def test_attribute_in(self, build: BaseStatusResponse, field: str) -> None:
        assert hasattr(build, field)

    def test_optional_field_turns_into_none(self, build: BaseStatusResponse, to_remove: str, attribute_name: str) -> None:
        raw = cast(tuple, self.OPTIONAL_FIELDS)[1]
        del raw[to_remove]
        assert getattr(type(build).build(raw), attribute_name) is None  # type: ignore # build is abstract

    def _dependency_table(self) -> dict[str, bool]:
        # a key in the dict must be a name of a test implementation.
        # and a value of the dict is a bool. if it's false - we
        # "delete" a test from the class.
        return {
            "test_values_of_attributes": self.EXPECTED_VALUES is not None,
            "test_types_of_attributes": self.EXPECTED_TYPES is not None,
            "test_attribute_in": self.ATTRIBUTES_IN is not None,
            "test_optional_field_turns_into_none": self.OPTIONAL_FIELDS is not None,
        }

    def _marks_table(self) -> dict[str, tuple[str, tuple[Any, ...]]]:
        # hooks in conftest.py parses this table

        # a key in the dict must be a name of a test implementation.
        # and a value of the dict is a tuple, where first element is
        # a name of mark to apply to the test, and second element is
        # positional arguments, which passed to the mark
        return {
            "test_values_of_attributes": ("parametrize", ("field,value", self.EXPECTED_VALUES)),
            "test_types_of_attributes": ("parametrize", ("field,type_", self.EXPECTED_TYPES)),
            "test_attribute_in": ("parametrize", ("field", self.ATTRIBUTES_IN)),
            "test_optional_field_turns_into_none": (
                "parametrize",
                ("to_remove,attribute_name", self.OPTIONAL_FIELDS[0] if self.OPTIONAL_FIELDS is not None else ()),
            ),
        }

    @staticmethod
    def construct(class_: _T) -> _T:
        instance: BaseResponseTest = class_()  # type: ignore
        instance._validate()
        for implementation_name, meet_dependencies in instance._dependency_table().items():
            if not meet_dependencies:
                # delattr works only with initialized classes,
                # hopefully overwriting with None doesn't have this limitation
                setattr(class_, implementation_name, None)

        return class_
