"""Conformal Deep Learning Framework (CDLF).

A production-ready framework for conformal prediction with TensorFlow integration.
"""

from typing import TYPE_CHECKING

__version__ = "0.1.0"
__author__ = "CDLF Team"
__license__ = "MIT"

# Import main classes for convenient access
if TYPE_CHECKING:
    from cdlf.core.base import BaseConformalPredictor
    from cdlf.core.split_cp import SplitConformalPredictor
    from cdlf.core.full_cp import FullConformalPredictor
    from cdlf.core.cross_cp import CrossConformalPredictor
    from cdlf.adaptive.adaptive_cp import AdaptiveConformalPredictor
    from cdlf.specialized.cqr import ConformizedQuantileRegression
    from cdlf.specialized.mondrian import MondrianConformalPredictor
    from cdlf.specialized.aps import AdaptivePredictionSets

# Lazy imports to avoid loading heavy dependencies on package import
__all__ = [
    "__version__",
    "BaseConformalPredictor",
    "SplitConformalPredictor",
    "FullConformalPredictor",
    "CrossConformalPredictor",
    "AdaptiveConformalPredictor",
    "ConformizedQuantileRegression",
    "MondrianConformalPredictor",
    "AdaptivePredictionSets",
]


def __getattr__(name: str) -> object:
    """Lazy import of main classes."""
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
    elif name == "AdaptiveConformalPredictor":
        from cdlf.adaptive.adaptive_cp import AdaptiveConformalPredictor
        return AdaptiveConformalPredictor
    elif name == "ConformizedQuantileRegression":
        from cdlf.specialized.cqr import ConformizedQuantileRegression
        return ConformizedQuantileRegression
    elif name == "MondrianConformalPredictor":
        from cdlf.specialized.mondrian import MondrianConformalPredictor
        return MondrianConformalPredictor
    elif name == "AdaptivePredictionSets":
        from cdlf.specialized.aps import AdaptivePredictionSets
        return AdaptivePredictionSets
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
