"""Adaptive conformal prediction methods.

This module implements adaptive conformal prediction algorithms that adjust
to changing data distributions over time.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.adaptive.adaptive_cp import AdaptiveConformalPredictor, OnlineQuantileTracker

__all__ = [
    "AdaptiveConformalPredictor",
    "OnlineQuantileTracker",
]


def __getattr__(name: str) -> object:
    """Lazy import of adaptive classes."""
    if name == "AdaptiveConformalPredictor":
        from cdlf.adaptive.adaptive_cp import AdaptiveConformalPredictor
        return AdaptiveConformalPredictor
    elif name == "OnlineQuantileTracker":
        from cdlf.adaptive.adaptive_cp import OnlineQuantileTracker
        return OnlineQuantileTracker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
