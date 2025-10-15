"""Adaptive Conformal Prediction for Distribution Shift.

This module implements adaptive conformal prediction methods that automatically
adjust coverage to maintain validity when data distribution changes over time.

References:
    - Gibbs & Candès (2021): "Adaptive Conformal Inference Under Distribution Shift"
    - Zaffran et al. (2022): "Adaptive Conformal Predictions for Time Series"
    - Barber et al. (2023): "Conformal Prediction Beyond Exchangeability"
"""

from typing import Any, Callable, Literal, Optional, Union
from collections import deque
import warnings

import numpy as np
import numpy.typing as npt

from cdlf.core.base import BaseConformalPredictor


class AdaptiveConformalPredictor(BaseConformalPredictor):
    """Adaptive Conformal Prediction with multiple adaptation strategies.

    Implements three key adaptive CP algorithms:
    1. Adaptive Conformal Inference (ACI): Gradient-based α adjustment
    2. Fully Adaptive Conformal Inference (FACI): EWMA-based fast adaptation
    3. Quantile Tracking: Sliding window quantile updates

    The predictor maintains validity under distribution shift by dynamically
    adjusting the miscoverage level α_t based on recent performance.

    Attributes:
        base_cp: Base conformal predictor to adapt
        alpha_target: Target significance level (1 - desired coverage)
        adaptation_method: Strategy for adaptation ('aci', 'faci', 'quantile')
        learning_rate: Learning rate γ for gradient updates
        beta: Exponential weighting factor for FACI
        window_size: Size of sliding window for quantile tracking
        alpha_history: History of α values over time
        coverage_history: History of empirical coverage rates
        error_history: History of miscoverage errors
    """

    def __init__(
        self,
        base_cp: BaseConformalPredictor,
        alpha_target: float = 0.1,
        adaptation_method: Literal['aci', 'faci', 'quantile'] = 'aci',
        learning_rate: float = 0.005,
        beta: float = 0.95,
        window_size: int = 100,
        min_alpha: float = 0.001,
        max_alpha: float = 0.5,
    ) -> None:
        """Initialize Adaptive Conformal Predictor.

        Args:
            base_cp: Base conformal predictor to adapt (e.g., SplitCP)
            alpha_target: Target significance level (default 0.1 for 90% coverage)
            adaptation_method: Adaptation strategy - 'aci', 'faci', or 'quantile'
            learning_rate: Learning rate γ for gradient updates (typically 0.001-0.01)
            beta: EWMA weighting factor for FACI (0 < β < 1, larger = more history)
            window_size: Buffer size for quantile tracking method
            min_alpha: Minimum allowed α to prevent numerical issues
            max_alpha: Maximum allowed α to maintain meaningful predictions

        Raises:
            ValueError: If parameters are out of valid ranges
        """
        super().__init__(alpha=alpha_target)

        # Validate parameters
        if not 0 < alpha_target < 1:
            raise ValueError(f"alpha_target must be in (0, 1), got {alpha_target}")
        if not 0 < learning_rate < 1:
            raise ValueError(f"learning_rate must be in (0, 1), got {learning_rate}")
        if not 0 < beta < 1:
            raise ValueError(f"beta must be in (0, 1), got {beta}")
        if window_size < 10:
            raise ValueError(f"window_size must be at least 10, got {window_size}")
        if not 0 < min_alpha < max_alpha < 1:
            raise ValueError(f"Invalid alpha bounds: min={min_alpha}, max={max_alpha}")
        if adaptation_method not in ['aci', 'faci', 'quantile']:
            raise ValueError(f"Invalid adaptation_method: {adaptation_method}")

        self.base_cp = base_cp
        self.alpha_target = alpha_target
        self.adaptation_method = adaptation_method
        self.learning_rate = learning_rate
        self.beta = beta
        self.window_size = window_size
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha

        # Adaptive state variables
        self.alpha_t = alpha_target  # Current adaptive α
        self.ewma_error = 0.0  # Exponentially weighted moving average error
        self.nonconformity_buffer = deque(maxlen=window_size)

        # History tracking
        self.alpha_history: list[float] = []
        self.coverage_history: list[float] = []
        self.error_history: list[float] = []
        self.update_count = 0

    def calibrate(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any],
    ) -> None:
        """Calibrate the adaptive conformal predictor.

        Performs initial calibration using the base CP method and initializes
        adaptive components based on calibration data.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features)
            y_cal: Calibration labels of shape (n_samples,) or (n_samples, n_outputs)
        """
        # Calibrate base predictor
        self.base_cp.calibrate(X_cal, y_cal)
        self.is_calibrated = True

        # Initialize adaptive state based on calibration data
        if hasattr(self.base_cp, 'calibration_scores'):
            # For quantile tracking, initialize buffer with calibration scores
            if self.adaptation_method == 'quantile':
                cal_scores = self.base_cp.calibration_scores
                if len(cal_scores) > 0:
                    # Sample initial scores for buffer
                    n_init = min(len(cal_scores), self.window_size // 2)
                    init_scores = np.random.choice(cal_scores, n_init, replace=False)
                    self.nonconformity_buffer.extend(init_scores)

        # Reset histories
        self.alpha_history = [self.alpha_t]
        self.coverage_history = []
        self.error_history = []
        self.update_count = 0

    def predict(
        self,
        X: npt.NDArray[np.floating[Any]],
    ) -> Union[npt.NDArray[Any], tuple[npt.NDArray[Any], npt.NDArray[Any]]]:
        """Generate adaptive conformal predictions.

        Uses the current adaptive α_t to generate prediction sets/intervals
        that adapt to distribution shift.

        Args:
            X: Test features of shape (n_samples, n_features)

        Returns:
            Prediction sets or intervals depending on task:
            - Regression: tuple of (lower_bounds, upper_bounds)
            - Classification: array of prediction sets

        Raises:
            RuntimeError: If predictor has not been calibrated
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before making predictions")

        # Update base predictor's alpha with current adaptive value
        original_alpha = self.base_cp.alpha
        self.base_cp.set_alpha(self.alpha_t)

        # For quantile tracking, update quantile if buffer has data
        if self.adaptation_method == 'quantile' and len(self.nonconformity_buffer) > 0:
            # Compute adjusted quantile from buffer
            q_level = np.ceil((1 - self.alpha_t) * (len(self.nonconformity_buffer) + 1))
            q_level = min(q_level, len(self.nonconformity_buffer))
            sorted_scores = np.sort(list(self.nonconformity_buffer))
            new_quantile = sorted_scores[int(q_level) - 1]

            # Update base predictor's quantile if it has this attribute
            if hasattr(self.base_cp, 'quantile'):
                self.base_cp.quantile = new_quantile

        # Generate predictions with adapted parameters
        predictions = self.base_cp.predict(X)

        # Restore original alpha
        self.base_cp.set_alpha(original_alpha)

        return predictions

    def update(
        self,
        y_true: npt.NDArray[Any],
        prediction_sets: Union[npt.NDArray[Any], tuple[npt.NDArray[Any], npt.NDArray[Any]]],
    ) -> None:
        """Update adaptive parameters based on observed outcomes.

        Implements online adaptation using the specified method:
        - ACI: α_t = α_{t-1} + γ * (α_target - err_t)
        - FACI: Uses EWMA error for smoother updates
        - Quantile: Updates sliding window of nonconformity scores

        Args:
            y_true: True labels for recent predictions
            prediction_sets: Previous predictions (intervals or sets)
        """
        # Compute coverage errors
        if isinstance(prediction_sets, tuple):
            # Regression: check if true values fall in intervals
            lower, upper = prediction_sets
            covered = (y_true >= lower) & (y_true <= upper)
        else:
            # Classification: check if true labels are in prediction sets
            covered = np.array([y in pred_set for y, pred_set in zip(y_true, prediction_sets)])

        # Compute miscoverage rate
        coverage_rate = np.mean(covered)
        error_t = 1.0 - coverage_rate  # Miscoverage error

        # Store history
        self.coverage_history.append(coverage_rate)
        self.error_history.append(error_t)

        # Update α based on adaptation method
        if self.adaptation_method == 'aci':
            # Adaptive Conformal Inference (Gibbs & Candès 2021)
            # α_t = α_{t-1} + γ * (α_target - err_t)
            self.alpha_t = self.alpha_t + self.learning_rate * (self.alpha_target - error_t)

        elif self.adaptation_method == 'faci':
            # Fully Adaptive Conformal Inference with EWMA
            # e_t = β * err_t + (1-β) * e_{t-1}
            # α_t = α_{t-1} + γ * (α_target - e_t)
            if self.update_count == 0:
                self.ewma_error = error_t
            else:
                self.ewma_error = self.beta * error_t + (1 - self.beta) * self.ewma_error

            self.alpha_t = self.alpha_t + self.learning_rate * (self.alpha_target - self.ewma_error)

        elif self.adaptation_method == 'quantile':
            # Quantile Tracking with sliding window
            # For quantile tracking, we store coverage indicators directly
            # and adjust α based on empirical coverage in the window

            # Store coverage information in buffer (1 if covered, 0 if not)
            if isinstance(prediction_sets, tuple):
                # Regression case
                lower, upper = prediction_sets
                batch_covered = ((y_true >= lower) & (y_true <= upper)).astype(float)
            else:
                # Classification case
                batch_covered = covered.astype(float)

            # Update buffer with coverage indicators
            self.nonconformity_buffer.extend(batch_covered)

            # Adjust α based on empirical coverage in window
            if len(self.nonconformity_buffer) >= 10:
                # Calculate recent empirical coverage
                recent_coverage = np.mean(list(self.nonconformity_buffer))
                # Update α to maintain target coverage
                self.alpha_t = self.alpha_t + self.learning_rate * (self.alpha_target - (1 - recent_coverage))

        # Clip α to valid range
        self.alpha_t = np.clip(self.alpha_t, self.min_alpha, self.max_alpha)

        # Store updated α
        self.alpha_history.append(self.alpha_t)
        self.update_count += 1

    def get_alpha_history(self) -> npt.NDArray[np.floating[Any]]:
        """Get the history of adaptive α values over time.

        Returns:
            Array of α values from initialization to current time
        """
        return np.array(self.alpha_history)

    def get_coverage_history(self) -> npt.NDArray[np.floating[Any]]:
        """Get the history of empirical coverage rates.

        Returns:
            Array of coverage rates for each update
        """
        return np.array(self.coverage_history)

    def get_error_history(self) -> npt.NDArray[np.floating[Any]]:
        """Get the history of miscoverage errors.

        Returns:
            Array of miscoverage errors for each update
        """
        return np.array(self.error_history)

    def reset_adaptation(self) -> None:
        """Reset adaptive state to initial values.

        Useful for handling regime changes or restarting adaptation.
        """
        self.alpha_t = self.alpha_target
        self.ewma_error = 0.0
        self.nonconformity_buffer.clear()
        self.alpha_history = [self.alpha_t]
        self.coverage_history = []
        self.error_history = []
        self.update_count = 0

    def get_params(self) -> dict[str, Any]:
        """Get all parameters of the adaptive conformal predictor.

        Returns:
            Dictionary containing all configuration parameters and current state
        """
        params = super().get_params()
        params.update({
            'alpha_target': self.alpha_target,
            'alpha_current': self.alpha_t,
            'adaptation_method': self.adaptation_method,
            'learning_rate': self.learning_rate,
            'beta': self.beta,
            'window_size': self.window_size,
            'min_alpha': self.min_alpha,
            'max_alpha': self.max_alpha,
            'update_count': self.update_count,
            'ewma_error': self.ewma_error,
            'buffer_size': len(self.nonconformity_buffer),
        })
        return params

    def __repr__(self) -> str:
        """String representation of the adaptive conformal predictor."""
        return (
            f"AdaptiveConformalPredictor("
            f"method={self.adaptation_method}, "
            f"α_target={self.alpha_target:.3f}, "
            f"α_current={self.alpha_t:.3f}, "
            f"γ={self.learning_rate:.4f}, "
            f"updates={self.update_count})"
        )


class OnlineQuantileTracker:
    """Efficient online quantile tracking using rolling statistics.

    Maintains a sliding window of values and efficiently computes
    quantiles as new observations arrive, without full re-sorting.

    This is a helper class for the quantile tracking method.
    """

    def __init__(self, window_size: int = 100, quantile_level: float = 0.9):
        """Initialize the online quantile tracker.

        Args:
            window_size: Size of the sliding window
            quantile_level: Quantile level to track (e.g., 0.9 for 90th percentile)
        """
        self.window_size = window_size
        self.quantile_level = quantile_level
        self.buffer = deque(maxlen=window_size)
        self._sorted_buffer: Optional[list[float]] = None
        self._needs_update = True

    def update(self, value: float) -> None:
        """Add a new value and update the buffer.

        Args:
            value: New observation to add
        """
        self.buffer.append(value)
        self._needs_update = True

    def get_quantile(self) -> float:
        """Get the current quantile estimate.

        Returns:
            Estimated quantile value
        """
        if len(self.buffer) == 0:
            return 0.0

        if self._needs_update:
            self._sorted_buffer = sorted(self.buffer)
            self._needs_update = False

        # Compute quantile index
        n = len(self._sorted_buffer)
        k = int(np.ceil(self.quantile_level * n)) - 1
        k = max(0, min(k, n - 1))

        return self._sorted_buffer[k]

    def get_all_quantiles(self, levels: list[float]) -> dict[float, float]:
        """Get multiple quantiles at once.

        Args:
            levels: List of quantile levels to compute

        Returns:
            Dictionary mapping levels to quantile values
        """
        if len(self.buffer) == 0:
            return {level: 0.0 for level in levels}

        if self._needs_update:
            self._sorted_buffer = sorted(self.buffer)
            self._needs_update = False

        n = len(self._sorted_buffer)
        quantiles = {}

        for level in levels:
            k = int(np.ceil(level * n)) - 1
            k = max(0, min(k, n - 1))
            quantiles[level] = self._sorted_buffer[k]

        return quantiles