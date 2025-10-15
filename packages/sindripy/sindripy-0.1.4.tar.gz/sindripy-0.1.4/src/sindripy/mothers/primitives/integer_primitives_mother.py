from sindripy.mothers.object_mother import ObjectMother


class IntegerPrimitivesMother(ObjectMother):
    """Generate int primitive values for testing."""

    @classmethod
    def any(cls) -> int:
        """Generate any random int value."""
        return cls._faker().random_int()

    @classmethod
    def create(cls, is_positive: bool | None = None, min_value: int = -10000, max_value: int = 1000) -> int:
        """Generate an int value with specified constraints."""
        if is_positive:
            return cls._faker().random_int(min=1, max=abs(max_value))

        if is_positive is False:
            return cls._faker().random_int(min=-abs(min_value), max=-1)

        return cls._faker().random_int(min=min_value, max=max_value)

    @classmethod
    def positive(cls) -> int:
        """Generate a positive int value greater than zero."""
        return cls._faker().random_int(min=1)

    @classmethod
    def negative(cls) -> int:
        """Generate a negative int value less than zero."""
        return cls._faker().random_int(min=-(2**31), max=-1)

    @staticmethod
    def zero() -> int:
        """Generate zero as an int."""
        return 0
