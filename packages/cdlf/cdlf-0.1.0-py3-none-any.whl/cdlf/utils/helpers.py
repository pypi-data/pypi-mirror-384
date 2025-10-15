"""Utility functions and helpers for CDLF.

This module provides common utility functions used throughout the framework
including validation, statistical computations, and data preprocessing.
"""

from typing import Any, Optional

import numpy as np
import numpy.typing as npt


def compute_quantile(
    scores: npt.NDArray[np.floating[Any]],
    alpha: float,
    method: str = "higher",
) -> float:
    """Compute the (1-alpha) quantile of nonconformity scores.

    Args:
        scores: Array of nonconformity scores.
        alpha: Significance level in (0, 1).
        method: Quantile interpolation method. Default is "higher" for
            conservative finite-sample guarantees.

    Returns:
        The computed quantile value.

    Raises:
        ValueError: If scores is empty or alpha is invalid.
    """
    if len(scores) == 0:
        raise ValueError("scores array cannot be empty")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    n = len(scores)
    q = np.ceil((n + 1) * (1 - alpha)) / n
    # Clip q to [0, 1] to handle edge cases
    q = min(q, 1.0)
    return float(np.quantile(scores, q, method=method))


def validate_alpha(alpha: float) -> None:
    """Validate significance level parameter.

    Args:
        alpha: Significance level to validate.

    Raises:
        ValueError: If alpha is not in (0, 1).
        TypeError: If alpha is not a float.
    """
    if not isinstance(alpha, (float, int)):
        raise TypeError(f"alpha must be a numeric type, got {type(alpha)}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")


def validate_calibration_data(
    X_cal: npt.NDArray[np.floating[Any]],
    y_cal: npt.NDArray[Any],
    min_samples: int = 10,
) -> None:
    """Validate calibration data inputs.

    Args:
        X_cal: Calibration features.
        y_cal: Calibration labels.
        min_samples: Minimum required number of samples. Default is 10.

    Raises:
        ValueError: If data is invalid or has insufficient samples.
        TypeError: If data types are incorrect.
    """
    if not isinstance(X_cal, np.ndarray):
        raise TypeError(f"X_cal must be a numpy array, got {type(X_cal)}")
    if not isinstance(y_cal, np.ndarray):
        raise TypeError(f"y_cal must be a numpy array, got {type(y_cal)}")

    if len(X_cal) == 0 or len(y_cal) == 0:
        raise ValueError("Calibration data cannot be empty")

    if len(X_cal) != len(y_cal):
        raise ValueError(
            f"X_cal and y_cal must have same length, got {len(X_cal)} and {len(y_cal)}"
        )

    if len(X_cal) < min_samples:
        raise ValueError(
            f"Insufficient calibration samples: got {len(X_cal)}, need at least {min_samples}"
        )


def split_data(
    X: npt.NDArray[np.floating[Any]],
    y: npt.NDArray[Any],
    split_ratio: float = 0.5,
    random_state: Optional[int] = None,
) -> tuple[
    npt.NDArray[np.floating[Any]],
    npt.NDArray[np.floating[Any]],
    npt.NDArray[Any],
    npt.NDArray[Any],
]:
    """Split data into training and calibration sets.

    Args:
        X: Feature array of shape (n_samples, n_features).
        y: Label array of shape (n_samples,).
        split_ratio: Fraction of data for training. Default is 0.5.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (X_train, X_cal, y_train, y_cal).

    Raises:
        ValueError: If split_ratio is not in (0, 1).
    """
    if not 0 < split_ratio < 1:
        raise ValueError(f"split_ratio must be in (0, 1), got {split_ratio}")

    if random_state is not None:
        np.random.seed(random_state)

    n_samples = len(X)
    n_train = int(n_samples * split_ratio)

    indices = np.random.permutation(n_samples)
    train_idx = indices[:n_train]
    cal_idx = indices[n_train:]

    return X[train_idx], X[cal_idx], y[train_idx], y[cal_idx]


def check_is_fitted(predictor: Any) -> None:
    """Check if a conformal predictor has been calibrated.

    Args:
        predictor: Conformal predictor instance.

    Raises:
        RuntimeError: If predictor has not been calibrated.
    """
    if not hasattr(predictor, "is_calibrated") or not predictor.is_calibrated:
        raise RuntimeError(
            f"{predictor.__class__.__name__} must be calibrated before making predictions. "
            "Call .calibrate() first."
        )


def format_prediction_intervals(
    lower: npt.NDArray[Any],
    upper: npt.NDArray[Any],
) -> npt.NDArray[Any]:
    """Format prediction intervals as a 2D array.

    Args:
        lower: Lower bounds of shape (n_samples,).
        upper: Upper bounds of shape (n_samples,).

    Returns:
        Array of shape (n_samples, 2) with [lower, upper] for each sample.
    """
    return np.column_stack([lower, upper])
