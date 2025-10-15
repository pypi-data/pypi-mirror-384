"""Model serving capabilities for conformal predictors.

This module provides tools for deploying conformal prediction models including:
- REST API server with FastAPI
- Batch prediction endpoints
- Model versioning and management
- Health checks and monitoring
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cdlf.serving.server import ConformalPredictionServer

__all__ = [
    "ConformalPredictionServer",
]


def __getattr__(name: str) -> object:
    """Lazy import of serving classes."""
    if name == "ConformalPredictionServer":
        from cdlf.serving.server import ConformalPredictionServer
        return ConformalPredictionServer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
