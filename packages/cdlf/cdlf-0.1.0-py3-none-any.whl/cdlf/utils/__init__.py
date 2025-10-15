"""Utility functions and helpers for CDLF.

This module contains utility functions for:
- Data validation and preprocessing
- Nonconformity score calculations
- Statistical computations
- Helper functions for common operations
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.utils.helpers import (
        compute_quantile,
        validate_alpha,
        validate_calibration_data,
    )

__all__ = [
    "compute_quantile",
    "validate_alpha",
    "validate_calibration_data",
]


def __getattr__(name: str) -> object:
    """Lazy import of utility functions."""
    if name in ["compute_quantile", "validate_alpha", "validate_calibration_data"]:
        from cdlf.utils import helpers
        return getattr(helpers, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
