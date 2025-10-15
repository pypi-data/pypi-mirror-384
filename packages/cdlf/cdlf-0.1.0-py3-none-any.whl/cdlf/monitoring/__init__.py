"""Monitoring and metrics for conformal prediction.

This module provides tools for monitoring conformal prediction performance including:
- Coverage metrics
- Efficiency metrics (prediction set size)
- Drift detection
- Performance tracking over time
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.monitoring.metrics import CoverageMetrics, EfficiencyMetrics

__all__ = [
    "CoverageMetrics",
    "EfficiencyMetrics",
]


def __getattr__(name: str) -> object:
    """Lazy import of monitoring classes."""
    if name == "CoverageMetrics":
        from cdlf.monitoring.metrics import CoverageMetrics
        return CoverageMetrics
    elif name == "EfficiencyMetrics":
        from cdlf.monitoring.metrics import EfficiencyMetrics
        return EfficiencyMetrics
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
