from sindripy.value_objects.decorators.validation import validate
from sindripy.value_objects.errors.incorrect_value_type_error import IncorrectValueTypeError
from sindripy.value_objects.errors.required_value_error import RequiredValueError
from sindripy.value_objects.value_object import ValueObject


class String(ValueObject[str]):
    """
    A value object that wraps string values with validation.

    This class provides a base implementation for creating value objects that
    represent string values in the domain. It ensures that the wrapped value
    is a valid string and not None.

    The class includes built-in validation for:
    - Required value (not None)
    - Type checking (must be a string)

    Inherits all functionality from ValueObject including immutability,
    equality comparison, string representation, and hashing.

    Example:
        ```python
        class Email(String):
            @validate
            def _validate_email_format(self, value: str) -> None:
                if "@" not in value:
                    raise ValueError("Invalid email format")

        email = Email("user@example.com")
        email.value  # 'user@example.com'
        ```
    """

    @validate
    def _ensure_has_value(self, value: str) -> None:
        if value is None:
            raise RequiredValueError

    @validate
    def _ensure_is_string(self, value: str) -> None:
        if not isinstance(value, str):
            raise IncorrectValueTypeError(value, str)
