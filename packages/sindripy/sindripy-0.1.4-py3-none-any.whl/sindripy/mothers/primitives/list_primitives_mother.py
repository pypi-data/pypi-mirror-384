from sindripy.mothers.object_mother import ObjectMother


class ListPrimitivesMother(ObjectMother):
    """Generate list primitive values for testing."""

    @staticmethod
    def empty() -> list:
        """Generate an empty list."""
        return []
