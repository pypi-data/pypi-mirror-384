"""TensorFlow integration utilities.

This module provides seamless integration with TensorFlow including:
- Custom Keras layers for conformal prediction
- Model wrappers for existing TensorFlow models
- Training callbacks for online calibration
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.tf_integration.layers import ConformalLayer
    from cdlf.tf_integration.wrappers import ConformalModelWrapper
    from cdlf.tf_integration.callbacks import CalibrationCallback

__all__ = [
    "ConformalLayer",
    "ConformalModelWrapper",
    "CalibrationCallback",
]


def __getattr__(name: str) -> object:
    """Lazy import of TensorFlow integration classes."""
    if name == "ConformalLayer":
        from cdlf.tf_integration.layers import ConformalLayer
        return ConformalLayer
    elif name == "ConformalModelWrapper":
        from cdlf.tf_integration.wrappers import ConformalModelWrapper
        return ConformalModelWrapper
    elif name == "CalibrationCallback":
        from cdlf.tf_integration.callbacks import CalibrationCallback
        return CalibrationCallback
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
