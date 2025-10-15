"""Top level package for the value-crafter library.

This module exposes the most common entry points so the public API is
available through the ``sindripy`` namespace when the library is
installed as a dependency.
"""

from sindripy import mothers, value_objects

__all__ = ["mothers", "value_objects"]
__version__ = "0.1.4"
