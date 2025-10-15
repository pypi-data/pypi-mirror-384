"""Public facade for value object implementations.

This module re-exports the most common value objects so they can be
imported directly from :mod:`sindripy.value_object`.
"""

from sindripy.value_objects.aggregate import Aggregate
from sindripy.value_objects.decorators.validation import validate
from sindripy.value_objects.errors.sindri_validation_error import SindriValidationError
from sindripy.value_objects.identifiers.string_uuid import StringUuid
from sindripy.value_objects.primitives.boolean import Boolean
from sindripy.value_objects.primitives.float import Float
from sindripy.value_objects.primitives.integer import Integer
from sindripy.value_objects.primitives.list import List
from sindripy.value_objects.primitives.string import String
from sindripy.value_objects.value_object import ValueObject

__all__ = [
    "Aggregate",
    "validate",
    "StringUuid",
    "Boolean",
    "Float",
    "Integer",
    "List",
    "String",
    "ValueObject",
    "SindriValidationError",
]
