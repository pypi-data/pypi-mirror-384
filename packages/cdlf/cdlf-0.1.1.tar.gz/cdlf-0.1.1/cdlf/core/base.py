"""Base classes for conformal prediction.

This module defines the abstract base class for all conformal predictors,
establishing the common interface and shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import numpy as np
import numpy.typing as npt


class BaseConformalPredictor(ABC):
    """Abstract base class for conformal predictors.

    All conformal prediction methods should inherit from this class and
    implement the required abstract methods.

    Attributes:
        alpha: Significance level (1 - confidence level). Must be in (0, 1).
        is_calibrated: Whether the predictor has been calibrated.
    """

    def __init__(self, alpha: float = 0.1) -> None:
        """Initialize the base conformal predictor.

        Args:
            alpha: Significance level. Default is 0.1 (90% confidence).

        Raises:
            ValueError: If alpha is not in (0, 1).
        """
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")

        self.alpha = alpha
        self.is_calibrated = False

    @abstractmethod
    def calibrate(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any],
    ) -> None:
        """Calibrate the conformal predictor on calibration data.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,) or (n_samples, n_outputs).
        """
        pass

    @abstractmethod
    def predict(
        self,
        X: npt.NDArray[np.floating[Any]],
    ) -> Union[npt.NDArray[Any], tuple[npt.NDArray[Any], npt.NDArray[Any]]]:
        """Generate conformal predictions for new data.

        Args:
            X: Test features of shape (n_samples, n_features).

        Returns:
            Prediction sets or intervals. Format depends on the task:
            - For regression: tuple of (lower_bounds, upper_bounds)
            - For classification: array of prediction sets
        """
        pass

    def set_alpha(self, alpha: float) -> None:
        """Update the significance level.

        Args:
            alpha: New significance level.

        Raises:
            ValueError: If alpha is not in (0, 1).
        """
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")
        self.alpha = alpha

    def get_params(self) -> dict[str, Any]:
        """Get parameters of the conformal predictor.

        Returns:
            Dictionary of parameter names to values.
        """
        return {
            "alpha": self.alpha,
            "is_calibrated": self.is_calibrated,
        }
