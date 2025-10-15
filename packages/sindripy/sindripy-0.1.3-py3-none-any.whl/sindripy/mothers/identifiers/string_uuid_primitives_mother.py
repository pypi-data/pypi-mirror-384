from sindripy.mothers.object_mother import ObjectMother


class StringUuidPrimitivesMother(ObjectMother):
    """Generate string UUID primitive values for testing."""

    @classmethod
    def any(cls) -> str:
        """Generate any random UUID string value."""
        return cls._faker().uuid4()

    @classmethod
    def invalid(cls) -> str:
        """Generate an invalid UUID string."""
        valid_uuid = cls.any()
        return valid_uuid[:-4]
