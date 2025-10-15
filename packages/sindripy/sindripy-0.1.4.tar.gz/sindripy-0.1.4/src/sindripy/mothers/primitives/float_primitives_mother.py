from sindripy.mothers.object_mother import ObjectMother


class FloatPrimitivesMother(ObjectMother):
    """Generate float primitive values for testing."""

    @classmethod
    def any(cls) -> float:
        """Generate any random float value."""
        return cls._faker().pyfloat()

    @classmethod
    def create(cls, is_positive: bool | None = None, min_value: float = -1000.0, max_value: float = 10000.0) -> float:
        """Generate a float value with specified constraints."""
        return cls._faker().pyfloat(positive=is_positive, min_value=min_value, max_value=max_value)

    @classmethod
    def positive(cls) -> float:
        """Generate a positive float value greater than zero."""
        return cls._faker().pyfloat(positive=True, min_value=0.1)

    @classmethod
    def negative(cls) -> float:
        """Generate a negative float value less than zero."""
        return cls._faker().pyfloat(positive=False, max_value=-0.1)

    @staticmethod
    def zero() -> float:
        """Generate zero as a float."""
        return 0.0
