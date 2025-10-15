from abc import ABC
from collections.abc import Callable
from typing import Generic, TypeVar

from sindripy._compat import Self, override

T = TypeVar("T")


class ValueObject(ABC, Generic[T]):
    """
    Abstract base class for implementing value objects with immutability and validation.

    Value objects are immutable objects that represent a descriptive aspect of the domain
    with no conceptual identity. They are equal when their values are equal.

    Type Parameters:
        T: The type of the value being wrapped by this value object.

    Attributes:
        _value: The internal value stored by this value object.

    Example:
        ```python
        from sindripy import ValueObject

        class String(ValueObject[str]):
            pass

        string = String("Hello World")
        repr(email)  # String(_value='Hello World')
        ```
    """

    __slots__ = ("_value",)
    __match_args__ = ("_value",)

    _value: T

    def __init__(self, value: T) -> None:
        """
        Initialize the value object with the given value.

        The value is validated using all methods decorated with @validate before
        being stored. Once initialized, the value cannot be modified.

        Args:
            value: The value to be wrapped by this value object.

        Raises:
            Various validation errors depending on the specific value object implementation.

        Example:
            from sindripy import ValueObject

            class String(ValueObject[str]):
                pass

            string = String("Hello World")
            repr(email)  # String(_value='Hello World')
            ```
        """
        self._validate(value)
        object.__setattr__(self, "_value", value)

    def _validate(self, value: T) -> None:
        """
        Validates the given value using all methods decorated with @validate.

        This method collects all validator methods from the class hierarchy (in reverse MRO order)
        and executes them in the order specified by their _order attribute. All validators
        must pass for the value to be considered valid.

        Args:
            value: The value to validate.

        Raises:
            Various validation errors if any validator fails.

        Example:
            ```python
            class Username(ValueObject[str]):
                @validate(order=1)
                def _validate_not_empty(self, value: str) -> None:
                    if not value.strip():
                        raise ValueError("Username cannot be empty")

                @validate(order=2)
                def _validate_length(self, value: str) -> None:
                    if len(value) < 3:
                        raise ValueError("Username must be at least 3 characters")

            username = Username("john")  # Both validators pass
            username._validate("ab")  # Would raise ValueError for length
            ```
        """
        validators: list[Callable[[T], None]] = []
        for cls in reversed(self.__class__.__mro__):
            if cls is object:
                continue

            methods: list[tuple[int, Callable[[T], None]]] = []
            for name, member in cls.__dict__.items():
                if getattr(member, "_is_validator", False):
                    validators.append(getattr(self, name))
                    order: int = getattr(member, "_order", 0)
                    methods.append((order, getattr(self, name)))

            for _, method in sorted(methods, key=lambda item: item[0]):
                validators.append(method)

        for validator in validators:
            validator(value)

    @property
    def value(self) -> T:
        """
        Get the wrapped value.

        Returns:
            The value wrapped by this value object.

        Example:
            ```python
            class ProductName(ValueObject[str]):
                pass

            product = ProductName("iPhone 15")
            product.value  # 'iPhone 15'
            type(product.value)  # <class 'str'>
            ```
        """
        return self._value

    @override
    def __eq__(self, other: Self) -> bool:
        """
        Check equality with another value object of the same type.

        Two value objects are considered equal if their wrapped values are equal.

        Args:
            other: Another value object of the same type to compare with.

        Returns:
            True if both value objects have equal values, False otherwise.

        Example:
            ```python
            class UserId(ValueObject[int]):
                pass

            user1 = UserId(123)
            user2 = UserId(123)
            user3 = UserId(456)
            user1 == user2  # True
            user1 == user3  # False
            user1 == 123  # Different type, would raise error
            ```
        """
        if not isinstance(other, self.__class__):
            return False

        return self.value == other.value

    @override
    def __repr__(self) -> str:
        """
        Return a string representation suitable for debugging.

        Returns:
            A string in the format "ClassName(value)" that can be used to recreate the object.

        Example:
            ```python
            class OrderId(ValueObject[str]):
                pass

            order = OrderId("ORD-001")
            repr(order)  # "OrderId('ORD-001')"
            eval(repr(order))  # OrderId('ORD-001')
            ```
        """
        return f"{self.__class__.__name__}({self._value!r})"

    @override
    def __str__(self) -> str:
        """
        Return a human-readable string representation of the value.

        Returns:
            The string representation of the wrapped value.

        Example:
            ```python
            class Price(ValueObject[float]):
                pass

            price = Price(29.99)
            str(price)  # '29.99'
            print(f"Product costs ${price}")  # Product costs $29.99
            ```
        """
        return str(self._value)

    @override
    def __hash__(self) -> int:
        """
        Return the hash value of this value object.

        The hash is based on the wrapped value, making value objects suitable
        for use as dictionary keys or in sets.

        Returns:
            The hash value of the wrapped value.

        Example:
            ```python
            class CategoryId(ValueObject[str]):
                pass

            cat1 = CategoryId("electronics")
            cat2 = CategoryId("books")
            cat3 = CategoryId("electronics")

            categories = {cat1: "Electronics", cat2: "Books"}
            categories[cat3]  # 'Electronics'

            unique_categories = {cat1, cat2, cat3}
            len(unique_categories)  # 2
            ```
        """
        return hash(self._value)

    @override
    def __setattr__(self, name: str, value: T) -> None:
        """
        Prevent modification of the value after initialization.

        This method enforces immutability by raising an AttributeError for any
        attempt to modify the value or access non-existent attributes.

        Args:
            name: The name of the attribute being set.
            value: The value being assigned to the attribute.

        Raises:
            AttributeError: Always raised to prevent modification of the value object.

        Example:
            ```python
            class CustomerId(ValueObject[int]):
                pass

            customer = CustomerId(12345)
            customer._value = 54321  # Raises AttributeError

            customer.new_attribute = "test"  # Raises AttributeError
            ```
        """
        if name in self.__slots__:
            raise AttributeError("Cannot modify the value of a ValueObject")

        public_name = name.replace("_", "")
        public_slots = [slot.replace("_", "") for slot in self.__slots__]
        if public_name in public_slots:
            raise AttributeError("Cannot modify the value of a ValueObject")

        raise AttributeError(f"Class {self.__class__.__name__} object has no attribute '{name}'")
