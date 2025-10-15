from sindripy.mothers.object_mother import ObjectMother


class BooleanPrimitivesMother(ObjectMother):
    """Generate boolean primitive values for testing."""

    @classmethod
    def any(cls) -> bool:
        """Generate any random boolean value."""
        return cls._faker().boolean()

    @staticmethod
    def true() -> bool:
        """Generate True value."""
        return True

    @staticmethod
    def false() -> bool:
        """Generate False value."""
        return False
