"""Specialized conformal prediction algorithms.

This module contains specialized conformal prediction methods for advanced use cases:

1. Conformalized Quantile Regression (CQR)
   - Use case: Regression with heteroscedastic (non-constant) noise
   - Key feature: Adaptive-width intervals based on local uncertainty
   - Reference: Romano et al. (2019) - "Conformalized Quantile Regression"

2. Mondrian Conformal Prediction
   - Use case: Classification with imbalanced classes or heterogeneous groups
   - Key feature: Class-conditional coverage guarantees
   - Reference: Vovk et al. (2005) - "Algorithmic Learning in a Random World"

3. Adaptive Prediction Sets (APS/RAPS)
   - Use case: Multi-class classification requiring efficient prediction sets
   - Key feature: Smallest average prediction sets with coverage guarantee
   - Reference: Romano et al. (2020) - "Classification with Valid and Adaptive Coverage"
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.specialized.cqr import ConformizedQuantileRegression
    from cdlf.specialized.mondrian import MondrianConformalPredictor
    from cdlf.specialized.aps import AdaptivePredictionSets

__all__ = [
    "ConformizedQuantileRegression",
    "MondrianConformalPredictor",
    "AdaptivePredictionSets",
]


def __getattr__(name: str) -> object:
    """Lazy import of specialized classes."""
    if name == "ConformizedQuantileRegression":
        from cdlf.specialized.cqr import ConformizedQuantileRegression
        return ConformizedQuantileRegression
    elif name == "MondrianConformalPredictor":
        from cdlf.specialized.mondrian import MondrianConformalPredictor
        return MondrianConformalPredictor
    elif name == "AdaptivePredictionSets":
        from cdlf.specialized.aps import AdaptivePredictionSets
        return AdaptivePredictionSets
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
