from sindripy.mothers.object_mother import ObjectMother


class StringPrimitivesMother(ObjectMother):
    """Generate string primitive values for testing."""

    @classmethod
    def any(cls) -> str:
        """Generate any random string value."""
        return cls._faker().word()

    @staticmethod
    def empty() -> str:
        return ""

    @classmethod
    def containing_character(cls, character: str) -> str:
        """Generate a string containing a specific character in a random position (not at beginning or end)."""
        base_word = cls._faker().word()

        if len(base_word) < 3:
            base_word = cls._faker().word() + cls._faker().word()

        character_position = cls._faker().random_int(min=1, max=len(base_word) - 1)

        return base_word[:character_position] + character + base_word[character_position + 1 :]

    @classmethod
    def ending_with(cls, character: str) -> str:
        """Generate a string ending with a specific character."""
        return cls._faker().word() + character

    @classmethod
    def beginning_with(cls, character: str) -> str:
        """Generate a string beginning with a specific character."""
        return character + cls._faker().word()

    @classmethod
    def with_length(cls, length: int) -> str:
        """Generate a string with specific length. If length is less than or equal to 0, return an empty string."""
        if length <= 0:
            return ""
        return cls._faker().pystr(min_chars=length, max_chars=length)

    @classmethod
    def text(cls) -> str:
        """Generate a text string (can contain spaces and punctuation)."""
        return cls._faker().text(max_nb_chars=200)
