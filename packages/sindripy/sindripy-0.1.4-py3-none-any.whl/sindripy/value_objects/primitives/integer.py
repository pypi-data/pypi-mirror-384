from sindripy.value_objects.decorators.validation import validate
from sindripy.value_objects.errors.incorrect_value_type_error import IncorrectValueTypeError
from sindripy.value_objects.errors.required_value_error import RequiredValueError
from sindripy.value_objects.value_object import ValueObject


class Integer(ValueObject[int]):
    """
    A value object that wraps integer values with validation.

    This class provides a base implementation for creating value objects that
    represent integer values in the domain. It ensures that the wrapped value
    is a valid integer and not None.

    The class includes built-in validation for:
    - Required value (not None)
    - Type checking (must be an integer)

    Inherits all functionality from ValueObject including immutability,
    equality comparison, string representation, and hashing.

    Example:
        ```python
        class Age(Integer):
            @validate
            def _validate_positive(self, value: int) -> None:
                if value < 0:
                    raise ValueError("Age cannot be negative")

        age = Age(25)
        age.value  # 25
        str(age)  # '25'
        ```
    """

    @validate
    def _ensure_has_value(self, value: int) -> None:
        if value is None:
            raise RequiredValueError

    @validate
    def _ensure_value_is_integer(self, value: int) -> None:
        if not isinstance(value, int):
            raise IncorrectValueTypeError(value, int)
