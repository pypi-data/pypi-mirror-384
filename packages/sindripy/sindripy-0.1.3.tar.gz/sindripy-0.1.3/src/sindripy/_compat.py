"""Compatibility helpers for typing features across Python versions."""

from __future__ import annotations

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

try:
    from typing import override
except ImportError:
    from typing_extensions import override

__all__ = ["Self", "override"]
