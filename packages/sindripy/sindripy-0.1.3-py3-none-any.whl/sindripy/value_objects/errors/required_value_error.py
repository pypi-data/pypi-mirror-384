from sindripy.value_objects.errors.sindri_validation_error import SindriValidationError


class RequiredValueError(SindriValidationError):
    def __init__(self) -> None:
        super().__init__(
            message="Value is required, can't be None",
        )
