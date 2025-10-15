from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def validate(func: F | None = None, *, order: int = 0) -> Callable[[F], F] | F:
    """Mark a method as a validator for ValueObject validation.

    Arguments:
        func: the function to decorate.
        order: order in which this validator should run relative to other validators in the same class. Lower numbers run first.
    """  # noqa: E501

    def wrapper(fn: F) -> F:
        if not isinstance(order, int):
            raise TypeError(f"Validation order {order} must be an integer. Got {type(order).__name__} type.")
        if order < 0:
            raise ValueError(f"Validation order {order} must be a positive value.")

        fn._is_validator = True
        fn._order = order
        return fn

    if func is not None:
        return wrapper(func)

    return wrapper
