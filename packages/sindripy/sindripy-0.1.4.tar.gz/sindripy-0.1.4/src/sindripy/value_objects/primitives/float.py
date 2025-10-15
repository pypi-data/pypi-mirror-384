from sindripy.value_objects.decorators.validation import validate
from sindripy.value_objects.errors.incorrect_value_type_error import IncorrectValueTypeError
from sindripy.value_objects.errors.required_value_error import RequiredValueError
from sindripy.value_objects.value_object import ValueObject


class Float(ValueObject[float]):
    """
    A value object that wraps float values with validation.

    This class provides a base implementation for creating value objects that
    represent float values in the domain. It ensures that the wrapped value
    is a valid float and not None. It accepts both positive and negative values.

    The class includes built-in validation for:
    - Required value (not None)
    - Type checking (must be a float)

    Inherits all functionality from ValueObject including immutability,
    equality comparison, string representation, and hashing.

    Example:
        ```python
        class Price(Float):
            @validate
            def _validate_positive(self, value: float) -> None:
                if value < 0:
                    raise ValueError("Price cannot be negative")

        price = Price(29.99)
        price.value  # 29.99
        str(price)  # '29.99'
        ```
    """

    @validate
    def _ensure_has_value(self, value: float) -> None:
        if value is None:
            raise RequiredValueError

    @validate
    def _ensure_value_is_float(self, value: float) -> None:
        if not isinstance(value, float):
            raise IncorrectValueTypeError(value, float)
