from collections.abc import Iterator
from typing import Any, Generic, TypeVar, get_args, get_origin

from sindripy._compat import Self, override
from sindripy.value_objects.decorators.validation import validate
from sindripy.value_objects.errors.incorrect_value_type_error import IncorrectValueTypeError
from sindripy.value_objects.errors.required_value_error import RequiredValueError
from sindripy.value_objects.value_object import ValueObject

T = TypeVar("T")


class List(ValueObject[list[T]], Generic[T]):
    @override
    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize subclass with proper type parameter validation.

        This method ensures that any subclass of List is properly parameterized
        with a type argument and extracts the element type for validation purposes. It
        is run automatically when a subclass is created, at definition time.
        """
        super().__init_subclass__(**kwargs)

        cls._validate_class_has_type_parameters()
        list_base = cls._find_parameterized_list_base()
        element_type = cls._extract_element_type_from_base(list_base)
        cls._validate_and_store_element_type(element_type)

    @classmethod
    def from_primitives(cls, value: list[Any]) -> Self:
        elements = []

        for primitive in value:
            if cls._element_is_an_aggregate_instance():
                elements.append(cls._element_type.from_primitives(primitive))
            elif cls._element_is_a_value_object_instance():
                elements.append(cls._element_type(primitive))
            else:
                elements.append(primitive)
        return cls(elements)

    @validate
    def _ensure_has_value(self, value: list[T]) -> None:
        if value is None:
            raise RequiredValueError

    @validate
    def _ensure_is_list(self, value: list[T]) -> None:
        if not isinstance(value, list):
            raise IncorrectValueTypeError(value, type[Any])

    @validate
    def _ensure_list_elements_have_expected_type(self, value: list[T]) -> None:
        cls = self.__class__

        if not hasattr(cls, "_element_type"):
            return

        element_type = cls._element_type

        if isinstance(element_type, TypeVar):
            return

        if not isinstance(element_type, type):
            return

        if cls._element_is_a_value_object_instance() or cls._element_is_a_primitive_type():
            for item in value:
                if not isinstance(item, element_type):
                    raise IncorrectValueTypeError(item, list)

    def __contains__(self, item: Any) -> bool:
        """
        Check if an item is present in the list.

        Args:
            item: The item to check for membership in the list.

        Returns:
            True if the item is in the list, False otherwise.

        Example:
            ```python
            numbers = IntList([1, 2, 3, 4, 5])
            3 in numbers  # True
            6 in numbers  # False
            ```
        """
        return item in self._value

    def __iter__(self) -> Iterator[T]:
        """
        Return an iterator over the list elements.

        Returns:
            An iterator that yields each element in the list.

        Example:
            ```python
            numbers = IntList([1, 2, 3])
            list(numbers)  # [1, 2, 3]
            for num in numbers:
                print(num)
            # 1
            # 2
            # 3
            ```
        """
        return iter(self._value)

    def __len__(self) -> int:
        """
        Return the number of elements in the list.

        Returns:
            The length of the wrapped list.

        Example:
            ```python
            numbers = IntList([1, 2, 3, 4, 5])
            len(numbers)  # 5
            ```
        """
        return len(self._value)

    def __reversed__(self) -> Iterator[T]:
        """
        Return a reverse iterator over the list elements.

        Returns:
            A reverse iterator that yields elements from the end to the beginning.

        Example:
            ```python
            numbers = IntList([1, 2, 3])
            list(reversed(numbers))  # [3, 2, 1]
            ```
        """
        return reversed(self._value)

    @override
    def __hash__(self) -> int:
        """
        Return the hash value of this value object.

        Since lists are unhashable in Python, we convert the list to a tuple
        for hashing purposes while maintaining the original list value.

        Returns:
            The hash value based on the tuple representation of the list.
        """
        return hash(tuple(self._value))

    @override
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another List value object.

        Args:
            other: The other object to compare against.

        Returns:
            True if both are List instances with the same element type and values, False otherwise.

        Example:
            ```python
            list1 = IntList([1, 2, 3])
            list2 = IntList([1, 2, 3])
            list3 = IntList([4, 5, 6])
            list1 == list2  # True
            list1 == list3  # False
            ```
        """
        if not isinstance(other, List):
            return False

        if self._element_type != other._element_type:
            return False

        return self._value == other._value

    @override
    def __repr__(self) -> str:
        """
        Return a string representation suitable for debugging.

        Returns:
            A string showing the class name and the wrapped list value.

        Example:
            ```python
            numbers = IntList([1, 2, 3])
            repr(numbers)  # 'IntList(_value=[1, 2, 3])'
            ```
        """
        return f"{self.__class__.__name__}(_value={self._value!r})"

    @override
    def __str__(self) -> str:
        """
        Return a human-readable string representation.

        Returns:
            The string representation of the wrapped list.

        Example:
            ```python
            numbers = IntList([1, 2, 3])
            str(numbers)  # '[1, 2, 3]'
            ```
        """
        return str(self._value)

    @classmethod
    def _validate_class_has_type_parameters(cls) -> None:
        """
        Validate that the class has type parameters defined.

        Raises:
            TypeError: If the class doesn't have __orig_bases__ or it's empty.
        """
        if not hasattr(cls, "__orig_bases__") or not getattr(cls, "__orig_bases__", None):
            raise TypeError(f"Class {cls.__name__} must be parameterized with a type argument")

    @classmethod
    def _find_parameterized_list_base(cls) -> Any:
        """
        Find the parameterized List base class in the inheritance chain.

        Returns:
            The parameterized List base class.

        Raises:
            TypeError: If no parameterized List base is found.
        """
        orig_bases = getattr(cls, "__orig_bases__", ())
        for base in orig_bases:
            if get_origin(base) is List:
                return base

        raise TypeError(f"Class {cls.__name__} must inherit from List[T] with a type parameter")

    @classmethod
    def _extract_element_type_from_base(cls, list_base: Any) -> Any:
        """
        Extract the element type from the parameterized List base.

        Args:
            list_base: The parameterized List base class.

        Returns:
            The element type parameter.
        """
        element_type, *_ = get_args(list_base)
        return element_type

    @classmethod
    def _validate_and_store_element_type(cls, element_type: Any) -> None:
        """
        Validate the element type and store it in the class.

        This method handles different types of type parameters:
        - TypeVar instances for generic types
        - Concrete types like int, str, etc.
        - Generic types like list[int], dict[str, int], etc.

        Args:
            element_type: The element type to validate and store.

        Raises:
            TypeError: If the element type is not a valid type parameter.
        """
        # Handle TypeVar cases: If the type is a generic type, store it directly
        if isinstance(element_type, TypeVar):
            cls._element_type = element_type
            return

        # Validate concrete types: Ensure the type parameter is actually a valid type
        if isinstance(element_type, type):
            cls._element_type = element_type
            return

        # Handle generic types like list[int], dict[str, int], etc.
        if hasattr(element_type, "__origin__") or get_origin(element_type) is not None:
            cls._element_type = element_type
            return

        raise TypeError(f"Type parameter must be a valid type, not a primitive value: {element_type}")

    @classmethod
    def _element_is_an_aggregate_instance(cls) -> bool:
        return hasattr(cls._element_type, "from_primitives")

    @classmethod
    def _element_is_a_value_object_instance(cls) -> bool:
        try:
            return isinstance(cls._element_type, type) and issubclass(cls._element_type, ValueObject)
        except TypeError:
            return False

    @classmethod
    def _element_is_a_primitive_type(cls) -> bool:
        try:
            return isinstance(cls._element_type, type) and not issubclass(cls._element_type, ValueObject)
        except TypeError:
            return False
