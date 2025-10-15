from abc import ABC, abstractmethod
from enum import Enum
from inspect import Parameter, _empty, signature
from typing import Any

from sindripy._compat import Self, override
from sindripy.value_objects.value_object import ValueObject


class Aggregate(ABC):
    """
    Abstract base class for implementing aggregates in domain-driven design.

    Aggregates are clusters of domain objects that can be treated as a single unit.
    They ensure consistency boundaries and encapsulate business rules across
    related entities and value objects.

    This class provides utilities for:
        - Converting aggregates to/from primitive dictionaries
        - Comparing aggregates for equality
        - String representation for debugging
        - Handling nested value objects and other aggregates

    Example:
        >>> class User(Aggregate):
        ...     def __init__(self, user_id: int, name: str, email: str):
        ...         self.user_id = user_id
        ...         self.name = name
        ...         self.email = email
        ...
        >>> user = User(1, "John Doe", "john@example.com")
        >>> user.to_primitives()
        {'user_id': 1, 'name': 'John Doe', 'email': 'john@example.com'}
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Initialize the aggregate.

        This method must be implemented by all concrete aggregate classes.
        It should set up the aggregate's state and ensure all invariants are met.

        Raises:
            NotImplementedError: Always raised as this is an abstract method.

        Example:
            >>> class Product(Aggregate):
            ...     def __init__(self, product_id: str, name: str, price: float):
            ...         self.product_id = product_id
            ...         self.name = name
            ...         self.price = price
            ...         if price < 0:
            ...             raise ValueError("Price cannot be negative")
        """
        raise NotImplementedError

    @override
    def __repr__(self) -> str:
        """
        Return a string representation suitable for debugging.

        Creates a string representation showing all non-private attributes
        in a constructor-like format.

        Returns:
            A string in the format "ClassName(attr1=value1, attr2=value2, ...)"

        Example:
            >>> class Order(Aggregate):
            ...     def __init__(self, order_id: str, customer_id: int, total: float):
            ...         self.order_id = order_id
            ...         self.customer_id = customer_id
            ...         self.total = total
            ...
            >>> order = Order("ORD-001", 123, 99.99)
            >>> repr(order)
            "Order(customer_id=123, order_id='ORD-001', total=99.99)"
        """
        attributes = []
        for key, value in self._to_dict().items():
            attributes.append(f"{key}={value!r}")

        return f"{self.__class__.__name__}({', '.join(attributes)})"

    @override
    def __eq__(self, other: Self) -> bool:
        """
        Check equality with another aggregate of the same type.

        Two aggregates are considered equal if they are of the same class
        and all their non-private attributes have equal values.

        Args:
            other: Another aggregate of the same type to compare with.

        Returns:
            True if both aggregates have equal attributes, False otherwise.
            NotImplemented if comparing with a different type.

        Example:
            >>> class Category(Aggregate):
            ...     def __init__(self, cat_id: int, name: str):
            ...         self.cat_id = cat_id
            ...         self.name = name
            ...
            >>> cat1 = Category(1, "Electronics")
            >>> cat2 = Category(1, "Electronics")
            >>> cat3 = Category(2, "Books")
            >>> cat1 == cat2
            True
            >>> cat1 == cat3
            False
        """
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self._to_dict() == other._to_dict()

    def _to_dict(self, *, ignore_private: bool = True) -> dict[str, Any]:
        """
        Convert the aggregate to a dictionary representation.

        Extracts all instance attributes and converts them to a dictionary,
        optionally filtering out private attributes (those starting with
        double underscore and class name).

        Args:
            ignore_private: Whether to exclude private attributes from the result.
                           Defaults to True.

        Returns:
            A dictionary mapping attribute names to their values.

        Example:
            >>> class Invoice(Aggregate):
            ...     def __init__(self, invoice_id: str, amount: float):
            ...         self.invoice_id = invoice_id
            ...         self.amount = amount
            ...         self._calculated_tax = amount * 0.1  # private attribute
            ...         self.__Invoice__secret = "hidden"    # name-mangled private
            ...
            >>> invoice = Invoice("INV-001", 100.0)
            >>> invoice._to_dict()
            {'invoice_id': 'INV-001', 'amount': 100.0, 'calculated_tax': 100.0}
            >>> invoice._to_dict(ignore_private=False)
            {'invoice_id': 'INV-001', 'amount': 100.0, 'calculated_tax': 100.0, 'secret': 'hidden'}
        """
        dictionary: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if ignore_private and key.startswith(f"_{self.__class__.__name__}__"):
                continue  # ignore private attributes

            key = key.replace(f"_{self.__class__.__name__}__", "")

            if key.startswith("_"):
                key = key[1:]

            dictionary[key] = value

        return dictionary

    @classmethod
    def from_primitives(cls, primitives: dict[str, Any]) -> Self:
        """
        Create an aggregate instance from a dictionary of primitive values.

        This factory method constructs an aggregate by mapping dictionary keys
        to constructor parameters. All required constructor parameters must be
        present in the primitives dictionary.

        Args:
            primitives: A dictionary mapping parameter names to their values.
                       Must contain all required constructor parameters.

        Returns:
            A new instance of the aggregate class.

        Raises:
            TypeError: If primitives is not a dictionary with string keys.
            ValueError: If required parameters are missing or extra parameters are provided.

        Example:
            >>> class Customer(Aggregate):
            ...     def __init__(self, customer_id: int, name: str, email: str = None):
            ...         self.customer_id = customer_id
            ...         self.name = name
            ...         self.email = email
            ...
            >>> data = {"customer_id": 42, "name": "Alice Smith"}
            >>> customer = Customer.from_primitives(data)
            >>> customer.name
            'Alice Smith'
            >>> customer.customer_id
            42
            >>>
            >>> # Missing required parameter
            >>> Customer.from_primitives({"name": "Bob"})  # Raises ValueError
            >>>
            >>> # Extra parameter
            >>> Customer.from_primitives({"customer_id": 1, "name": "Charlie", "age": 30})  # Raises ValueError
        """
        if not isinstance(primitives, dict) or not all(isinstance(key, str) for key in primitives):
            raise TypeError(f'{cls.__name__} primitives <<<{primitives}>>> must be a dictionary of strings. Got <<<{type(primitives).__name__}>>> type.')  # noqa: E501  # fmt: skip

        constructor_signature = signature(obj=cls.__init__)
        parameters: dict[str, Parameter] = {parameter.name: parameter for parameter in constructor_signature.parameters.values() if parameter.name != 'self'}  # noqa: E501  # fmt: skip
        missing = {name for name, parameter in parameters.items() if parameter.default is _empty and name not in primitives}  # noqa: E501  # fmt: skip
        extra = set(primitives) - parameters.keys()

        if missing or extra:
            cls._raise_value_constructor_parameters_mismatch(primitives=set(primitives), missing=missing, extra=extra)

        return cls(**primitives)

    @classmethod
    def _raise_value_constructor_parameters_mismatch(
        cls,
        primitives: set[str],
        missing: set[str],
        extra: set[str],
    ) -> None:
        """
        Raise a detailed ValueError for constructor parameter mismatches.

        This helper method generates informative error messages when the
        primitives dictionary doesn't match the constructor signature.

        Args:
            primitives: Set of parameter names provided in the primitives dict.
            missing: Set of required parameter names that are missing.
            extra: Set of parameter names that are not in the constructor.

        Raises:
            ValueError: Always raised with detailed information about the mismatch.

        Example:
            >>> class Item(Aggregate):
            ...     def __init__(self, item_id: str, name: str, price: float):
            ...         pass
            ...
            >>> # This would trigger the error method internally:
            >>> Item.from_primitives({"item_id": "123", "description": "test"})
            Traceback (most recent call last):
                ...
            ValueError: Item primitives <<<description, item_id>>> must contain all constructor parameters. Missing parameters: <<<name, price>>> and extra parameters: <<<description>>>.
        """
        primitives_names = ", ".join(sorted(primitives))
        missing_names = ", ".join(sorted(missing))
        extra_names = ", ".join(sorted(extra))

        raise ValueError(f'{cls.__name__} primitives <<<{primitives_names}>>> must contain all constructor parameters. Missing parameters: <<<{missing_names}>>> and extra parameters: <<<{extra_names}>>>.')  # noqa: E501  # fmt: skip

    def to_primitives(self) -> dict[str, Any]:
        """
        Convert the aggregate to a dictionary of primitive values.

        Recursively converts the aggregate and all nested objects (other aggregates,
        value objects, enums) to their primitive representations. This is useful
        for serialization to JSON, database storage, or API responses.

        Returns:
            A dictionary with primitive values (strings, numbers, booleans, etc.)
            where complex objects have been converted to their primitive forms.

        Example:
            >>> from enum import Enum
            >>>
            >>> class Status(Enum):
            ...     ACTIVE = "active"
            ...     INACTIVE = "inactive"
            ...
            >>> class UserId(ValueObject[int]):
            ...     pass
            ...
            >>> class Account(Aggregate):
            ...     def __init__(self, user_id: UserId, status: Status, balance: float):
            ...         self.user_id = user_id
            ...         self.status = status
            ...         self.balance = balance
            ...
            >>> account = Account(UserId(123), Status.ACTIVE, 1500.50)
            >>> account.to_primitives()
            {'user_id': 123, 'status': 'active', 'balance': 1500.5}
            >>>
            >>> # With nested aggregates
            >>> class Order(Aggregate):
            ...     def __init__(self, account: Account, item_count: int):
            ...         self.account = account
            ...         self.item_count = item_count
            ...
            >>> order = Order(account, 3)
            >>> order.to_primitives()
            {'account': {'user_id': 123, 'status': 'active', 'balance': 1500.5}, 'item_count': 3}
        """
        primitives = self._to_dict()
        for key, value in primitives.items():
            if isinstance(value, Aggregate) or hasattr(value, "to_primitives"):
                value = value.to_primitives()

            elif isinstance(value, Enum):
                value = value.value

            elif isinstance(value, ValueObject) or hasattr(value, "value"):
                value = value.value

                if isinstance(value, Enum):
                    value = value.value

            primitives[key] = value

        return primitives
