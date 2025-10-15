from uuid import UUID

from sindripy.value_objects.decorators.validation import validate
from sindripy.value_objects.errors.incorrect_value_type_error import IncorrectValueTypeError
from sindripy.value_objects.errors.invalid_id_format_error import InvalidIdFormatError
from sindripy.value_objects.errors.required_value_error import RequiredValueError
from sindripy.value_objects.value_object import ValueObject


class StringUuid(ValueObject[str]):
    """
    A value object that wraps UUID (Universally Unique Identifier) string values with validation.

    This class provides a specialized implementation for creating value objects that
    represent UUID values in the domain. It ensures that the wrapped value is a
    valid UUID string format and not None.

    The class includes built-in validation for:
    - Required value (not None)
    - Type checking (must be a string)
    - UUID format validation (must be a valid UUID format)

    Inherits all functionality from ValueObject including immutability,
    equality comparison, string representation, and hashing.

    Example:
        ```python
        class UserId(StringUuid):
            @validate
            def _validate_version(self, value: str) -> None:
                parsed_uuid = UUID(value)
                if parsed_uuid.version != 4:
                    raise ValueError("Only UUID version 4 allowed")

        user_id = UserId("123e4567-e89b-12d3-a456-426614174000")
        user_id.value  # '123e4567-e89b-12d3-a456-426614174000'
        ```
    """

    @validate
    def _ensure_has_value(self, value: str) -> None:
        if value is None:
            raise RequiredValueError

    @validate
    def _ensure_value_is_string(self, value: str) -> None:
        if not isinstance(value, str):
            raise IncorrectValueTypeError(value, str)

    @validate
    def _ensure_value_has_valid_uuid_format(self, value: str) -> None:
        try:
            UUID(value)
        except ValueError as error:
            raise InvalidIdFormatError from error
