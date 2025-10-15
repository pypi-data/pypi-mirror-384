from typing import Any, TypeVar

from sindripy.value_objects.errors.sindri_validation_error import SindriValidationError

T = TypeVar("T")


class IncorrectValueTypeError(SindriValidationError):
    def __init__(self, value: T, expected_type: type[Any]) -> None:
        super().__init__(
            message=f"Value '{value}' is not of type {expected_type.__name__}",
        )
