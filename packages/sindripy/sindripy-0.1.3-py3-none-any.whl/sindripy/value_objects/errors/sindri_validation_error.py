class SindriValidationError(Exception):
    """Base class for all controlled errors during validation of value objects."""

    def __init__(self, message: str) -> None:
        self._message = message
        super().__init__(self._message)

    @property
    def message(self) -> str:
        return self._message
