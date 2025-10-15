"""Core conformal prediction methods.

This module provides base classes and implementations for various
conformal prediction algorithms including split, full, and cross-conformal methods.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.core.base import BaseConformalPredictor
    from cdlf.core.split_cp import SplitConformalPredictor
    from cdlf.core.full_cp import FullConformalPredictor
    from cdlf.core.cross_cp import CrossConformalPredictor

__all__ = [
    "BaseConformalPredictor",
    "SplitConformalPredictor",
    "FullConformalPredictor",
    "CrossConformalPredictor",
]


def __getattr__(name: str) -> object:
    """Lazy import of core classes."""
    if name == "BaseConformalPredictor":
        from cdlf.core.base import BaseConformalPredictor
        return BaseConformalPredictor
    elif name == "SplitConformalPredictor":
        from cdlf.core.split_cp import SplitConformalPredictor
        return SplitConformalPredictor
    elif name == "FullConformalPredictor":
        from cdlf.core.full_cp import FullConformalPredictor
        return FullConformalPredictor
    elif name == "CrossConformalPredictor":
        from cdlf.core.cross_cp import CrossConformalPredictor
        return CrossConformalPredictor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
