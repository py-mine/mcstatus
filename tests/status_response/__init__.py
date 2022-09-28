from __future__ import annotations

import abc
from typing import Any, Optional, TypeVar, Union, cast

import pytest

__all__ = ["BaseStatusResponseTest"]
_T = TypeVar("_T", bound="type[BaseStatusResponseTest]")


class BaseStatusResponseTest(abc.ABC):
    EXPECTED_VALUES: Optional[list[tuple[str, Any]]] = None
    EXPECTED_TYPES: Optional[list[tuple[str, type]]] = None
    ATTRIBUTES_IN: Optional[list[str]] = None
    # if we don't specify item in raw answer, target field will be None
    # first element is a list with fields to remove, and attribute that
    # must be None. a dict is a raw answer to pass into `build` method
    OPTIONAL_FIELDS: Optional[tuple[list[tuple[str, str]], dict]] = None
    # there will be a ValueError, if we exclude the field from input
    # and a TypeError, if specify incorrect type
    # second item in tuple is an additional items to test their types,
    # but they aren't required. third item in tuple is a raw answer dict
    BUILD_METHOD_VALIDATION: Optional[tuple[list[str], list[str], dict]] = None

    # TODO Delete attributes for deprecations tests after 2022-08
    # note: for deprecations tests you should set
    # pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
    DEPRECATED_FIELDS: Optional[list[str]] = None
    # tuple will be unpacked with `*` and dict with `**`
    DEPRECATED_OLD_INIT_PASSED_ARGS: Optional[Union[tuple, dict]] = None
    DEPRECATED_NEW_INIT_PASSED_ARGS: Optional[Union[tuple, dict]] = None
    # very same to `EXPECTED_TYPES` but this is much stricter than `EXPECTED_TYPES`
    DEPRECATED_NESTED_CLASSES_USED: Optional[list[tuple[str, type]]] = None
    # is nested classes types can be accessed with built object?
    # default - copy values from `DEPRECATED_NESTED_CLASSES_USED`
    DEPRECATED_NESTED_CLASSES_ARE_IN_BUILD: Optional[list[type]] = None
    # first element is new object type, and second element is kwargs passed to the object
    DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE: Optional[tuple[type, dict]] = None
    # we don't need Iterable here, so better to use just None
    DEPRECATED_CLASS_REPR_MUST_START_WITH: Optional[str] = None

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

        if self.BUILD_METHOD_VALIDATION is not None:
            for do_required_item in self.BUILD_METHOD_VALIDATION[1]:
                if do_required_item in self.BUILD_METHOD_VALIDATION[0]:
                    raise ValueError(
                        "You must specify only required fields, in first tuple's item."
                        f" Found '{do_required_item}' in first and second items."
                    )

    @abc.abstractmethod
    def build(self) -> Any:
        ...

    # implementations for tests

    def test_values_of_attributes(self, build, field, value):
        assert getattr(build, field) == value

    def test_types_of_attributes(self, build, field, type_):
        assert isinstance(getattr(build, field), type_)

    def test_attribute_in(self, build, field):
        assert hasattr(build, field)

    def test_optional_field_turns_into_none(self, build, to_remove, attribute_name):
        raw = cast(tuple, self.OPTIONAL_FIELDS)[1]
        del raw[to_remove]
        assert getattr(type(build).build(raw), attribute_name) is None

    def test_value_validating(self, build, exclude_field):
        raw = cast(list, self.BUILD_METHOD_VALIDATION)[2].copy()
        raw.pop(exclude_field)
        with pytest.raises(ValueError):
            type(build).build(raw)

    def test_type_validating(self, build, to_change_field):
        raw = cast(list, self.BUILD_METHOD_VALIDATION)[2].copy()
        raw[to_change_field] = object()
        with pytest.raises(TypeError):
            type(build).build(raw)

    # TODO Delete these implementations for deprecations after 2022-08

    def test_deprecated_fields_raise_warning(self, build, field):
        with pytest.deprecated_call():
            getattr(build, field)

    def test_init_old_signature_raises_warning(self, build):
        with pytest.deprecated_call():
            # cant make it in one line, because of syntax error
            if isinstance(self.DEPRECATED_OLD_INIT_PASSED_ARGS, tuple):
                type(build)(*self.DEPRECATED_OLD_INIT_PASSED_ARGS)
            else:
                type(build)(**self.DEPRECATED_OLD_INIT_PASSED_ARGS)

    def test_init_new_signature_does_not_raise_warning(self, build):
        # cant make it in one line, because of syntax error
        if isinstance(tuple, type(self.DEPRECATED_NEW_INIT_PASSED_ARGS)):
            type(build)(*self.DEPRECATED_NEW_INIT_PASSED_ARGS)
        else:
            type(build)(**self.DEPRECATED_NEW_INIT_PASSED_ARGS)

    def test_deprecated_nested_classes_used(self, build, field, type_):
        assert type(getattr(build, field)) is type_

    def test_nested_classes_are_in_build(self, build, class_):
        assert getattr(build, class_.__name__) is class_

    def test_deprecated_object_can_be_compared_to_new_one(self, build):
        """If we forgot overwrite `__eq__` method in deprecated class, it will fail."""
        new_class, new_kwargs = cast(tuple, self.DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE)
        assert build == new_class(**new_kwargs)

    def test_repr_returns_correct_class(self, build):
        """If we forgot overwrite `__repr__` method in child class,

        it will output `DeprecatedClass(...)` instead of `NewClass(...)`.
        """
        assert repr(build).startswith(cast(str, self.DEPRECATED_CLASS_REPR_MUST_START_WITH))

    def _dependency_table(self) -> dict[str, bool]:
        # a key in the dict must be a name of a test implementation.
        # and a value of the dict is a bool. if it's false - we
        # "delete" a test from the class.
        return {
            "test_values_of_attributes": self.EXPECTED_VALUES is not None,
            "test_types_of_attributes": self.EXPECTED_TYPES is not None,
            "test_attribute_in": self.ATTRIBUTES_IN is not None,
            "test_optional_field_turns_into_none": self.OPTIONAL_FIELDS is not None,
            "test_value_validating": self.BUILD_METHOD_VALIDATION is not None,
            "test_type_validating": self.BUILD_METHOD_VALIDATION is not None,
            # TODO Delete these implementations for deprecations after 2022-08
            "test_deprecated_fields_raise_warning": self.DEPRECATED_FIELDS is not None,
            "test_init_old_signature_raises_warning": self.DEPRECATED_OLD_INIT_PASSED_ARGS is not None,
            "test_init_new_signature_does_not_raise_warning": self.DEPRECATED_NEW_INIT_PASSED_ARGS is not None,
            "test_deprecated_nested_classes_used": self.DEPRECATED_NESTED_CLASSES_USED is not None,
            "test_nested_classes_are_in_build": self.DEPRECATED_NESTED_CLASSES_USED is not None
            or self.DEPRECATED_NESTED_CLASSES_ARE_IN_BUILD is not None,  # noqa: W503 # black
            "test_deprecated_object_can_be_compared_to_new_one": self.DEPRECATED_OBJECT_CAN_BE_COMPARED_TO_NEW_ONE is not None,
            "test_repr_returns_correct_class": self.DEPRECATED_CLASS_REPR_MUST_START_WITH is not None,
        }

    def _marks_table(self) -> dict[str, tuple[str, tuple[Any, ...]]]:
        # hooks in conftest.py parses this table
        if self.BUILD_METHOD_VALIDATION is not None:
            build_method_validation_args = self.BUILD_METHOD_VALIDATION[0].copy()
            build_method_validation_args.extend(self.BUILD_METHOD_VALIDATION[1])
        else:
            build_method_validation_args = []

        if self.DEPRECATED_NESTED_CLASSES_ARE_IN_BUILD is not None or self.DEPRECATED_NESTED_CLASSES_USED is not None:
            if self.DEPRECATED_NESTED_CLASSES_ARE_IN_BUILD is None:
                nested_classes_are_in_build_args = [type_ for field, type_ in cast(list, self.DEPRECATED_NESTED_CLASSES_USED)]
            else:
                nested_classes_are_in_build_args = self.DEPRECATED_NESTED_CLASSES_ARE_IN_BUILD
        else:
            nested_classes_are_in_build_args = []

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
            "test_value_validating": (
                "parametrize",
                ("exclude_field", self.BUILD_METHOD_VALIDATION[0] if self.BUILD_METHOD_VALIDATION is not None else ()),
            ),
            "test_type_validating": ("parametrize", ("to_change_field", build_method_validation_args)),
            # TODO Delete these implementations for deprecations after 2022-08
            "test_deprecated_fields_raise_warning": ("parametrize", ("field", self.DEPRECATED_FIELDS)),
            "test_init_new_signature_does_not_raise_warning": ("filterwarnings", ("error",)),
            "test_deprecated_nested_classes_used": ("parametrize", ("field,type_", self.DEPRECATED_NESTED_CLASSES_USED)),
            "test_nested_classes_are_in_build": ("parametrize", ("class_", nested_classes_are_in_build_args)),
        }

    @staticmethod
    def construct(class_: _T) -> _T:
        instance: BaseStatusResponseTest = class_()  # type: ignore
        instance._validate()
        for implementation_name, meet_dependencies in instance._dependency_table().items():
            if not meet_dependencies:
                # delattr works only with initialized classes,
                # hopefully overwriting with None doesn't have this limitation
                setattr(class_, implementation_name, None)

        return class_
