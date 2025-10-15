"""Conformalized Quantile Regression (CQR) implementation.

This module implements CQR, which combines quantile regression with
conformal prediction to provide efficient prediction intervals for regression.

Reference: Romano et al. (2019) - "Conformalized Quantile Regression"
https://arxiv.org/abs/1905.03222

Mathematical Formulation:
1. Train quantile regressors for α/2 and 1-α/2 quantiles:
   - q_low(x) estimates the α/2 quantile of Y|X=x
   - q_high(x) estimates the 1-α/2 quantile of Y|X=x

2. Compute nonconformity scores on calibration set:
   E_i = max(q_low(X_i) - Y_i, Y_i - q_high(X_i))

3. Find conformal correction Q_α:
   Q_α = quantile(E_1, ..., E_n, level=(1-α)(1+1/n))

4. Final prediction interval:
   C(x) = [q_low(x) - Q_α, q_high(x) + Q_α]

This produces adaptive intervals that expand based on local uncertainty,
providing tighter intervals where the model is confident and wider intervals
in regions of high uncertainty.
"""

from typing import Any, Optional, Union, Literal, Tuple
import warnings

import numpy as np
import numpy.typing as npt
import pandas as pd

from cdlf.core.base import BaseConformalPredictor


class ConformizedQuantileRegression(BaseConformalPredictor):
    """Conformalized Quantile Regression for efficient prediction intervals.

    CQR uses quantile regression to estimate conditional quantiles and then
    applies conformal calibration for finite-sample validity. This results in
    prediction intervals that adapt to heteroscedastic noise patterns in the data.

    Attributes:
        model_low: Quantile regression model for lower quantile (α/2).
        model_high: Quantile regression model for upper quantile (1-α/2).
        alpha: Significance level (1 - confidence level).
        backend: Backend framework ('neural', 'sklearn', or 'custom').
        correction: Conformal correction term Q_α from calibration.
        nonconformity_scores: Stored nonconformity scores from calibration.

    Example:
        >>> import numpy as np
        >>> from sklearn.ensemble import GradientBoostingRegressor
        >>> from cdlf.specialized.cqr import ConformizedQuantileRegression
        >>>
        >>> # Create quantile regressors
        >>> model_low = GradientBoostingRegressor(loss='quantile', alpha=0.05)
        >>> model_high = GradientBoostingRegressor(loss='quantile', alpha=0.95)
        >>>
        >>> # Initialize CQR
        >>> cqr = ConformizedQuantileRegression(
        ...     model_low=model_low,
        ...     model_high=model_high,
        ...     alpha=0.1,
        ...     backend='sklearn'
        ... )
        >>>
        >>> # Train and calibrate
        >>> X_train, y_train = np.random.randn(1000, 10), np.random.randn(1000)
        >>> X_cal, y_cal = np.random.randn(500, 10), np.random.randn(500)
        >>> cqr.fit(X_train, y_train)
        >>> cqr.calibrate(X_cal, y_cal)
        >>>
        >>> # Generate prediction intervals
        >>> X_test = np.random.randn(100, 10)
        >>> lower, upper = cqr.predict(X_test)
    """

    def __init__(
        self,
        model_low: Any,
        model_high: Any,
        alpha: float = 0.1,
        backend: Literal['neural', 'sklearn', 'custom'] = 'sklearn'
    ) -> None:
        """Initialize CQR predictor.

        Args:
            model_low: Quantile regression model for α/2 quantile.
                Should have fit() and predict() methods.
            model_high: Quantile regression model for 1-α/2 quantile.
                Should have fit() and predict() methods.
            alpha: Significance level. Default is 0.1 (90% confidence).
            backend: Backend framework to use ('neural', 'sklearn', or 'custom').

        Raises:
            ValueError: If alpha is not in (0, 1) or models lack required methods.
        """
        super().__init__(alpha=alpha)

        # Validate models
        if not hasattr(model_low, 'fit') or not hasattr(model_low, 'predict'):
            raise ValueError("model_low must have 'fit' and 'predict' methods")
        if not hasattr(model_high, 'fit') or not hasattr(model_high, 'predict'):
            raise ValueError("model_high must have 'fit' and 'predict' methods")

        self.model_low = model_low
        self.model_high = model_high
        self.backend = backend
        self.correction: Optional[float] = None
        self.nonconformity_scores: Optional[npt.NDArray[np.floating[Any]]] = None
        self._is_fitted = False

    def fit(
        self,
        X: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y: Union[npt.NDArray[Any], pd.Series],
    ) -> 'ConformizedQuantileRegression':
        """Train the quantile regression models.

        Args:
            X: Training features of shape (n_samples, n_features).
            y: Training labels of shape (n_samples,).

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If input shapes are invalid.
        """
        # Convert pandas to numpy
        if isinstance(X, pd.DataFrame):
            X = X.values
        if isinstance(y, pd.Series):
            y = y.values

        # Validate inputs
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y).ravel()

        if X.shape[0] != y.shape[0]:
            raise ValueError(f"X and y must have same number of samples, "
                           f"got {X.shape[0]} and {y.shape[0]}")

        # Train quantile models
        if self.backend == 'sklearn':
            # For sklearn GradientBoostingRegressor with quantile loss
            self.model_low.fit(X, y)
            self.model_high.fit(X, y)
        elif self.backend == 'neural':
            # For neural networks (assumes models handle quantile loss internally)
            self.model_low.fit(X, y)
            self.model_high.fit(X, y)
        else:  # custom
            # For custom models
            self.model_low.fit(X, y)
            self.model_high.fit(X, y)

        self._is_fitted = True
        return self

    def calibrate(
        self,
        X_cal: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_cal: Union[npt.NDArray[Any], pd.Series],
    ) -> None:
        """Calibrate CQR on calibration data.

        Computes nonconformity scores and the conformal correction term Q_α.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,).

        Raises:
            RuntimeError: If models have not been fitted.
            ValueError: If calibration set is too small.
        """
        if not self._is_fitted:
            raise RuntimeError("Models must be fitted before calibration. Call fit() first.")

        # Convert pandas to numpy
        if isinstance(X_cal, pd.DataFrame):
            X_cal = X_cal.values
        if isinstance(y_cal, pd.Series):
            y_cal = y_cal.values

        # Validate inputs
        X_cal = np.asarray(X_cal, dtype=np.float32)
        y_cal = np.asarray(y_cal).ravel()

        n_cal = X_cal.shape[0]
        if n_cal < 10:
            warnings.warn(f"Calibration set size ({n_cal}) is very small. "
                         "Consider using more calibration data for better coverage.",
                         RuntimeWarning)

        # Get quantile predictions
        q_low = self.model_low.predict(X_cal).ravel()
        q_high = self.model_high.predict(X_cal).ravel()

        # Compute nonconformity scores
        # E_i = max(q_low(X_i) - Y_i, Y_i - q_high(X_i))
        self.nonconformity_scores = np.maximum(q_low - y_cal, y_cal - q_high)

        # Compute conformal correction
        # Q_α = quantile(E, level=(1-α)(1+1/n))
        level = np.ceil((1 - self.alpha) * (n_cal + 1)) / n_cal
        level = min(level, 1.0)  # Ensure level <= 1

        self.correction = np.quantile(self.nonconformity_scores, level)
        self.is_calibrated = True

    def predict(
        self,
        X: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        return_quantiles: bool = False
    ) -> Union[Tuple[npt.NDArray[Any], npt.NDArray[Any]],
               Tuple[npt.NDArray[Any], npt.NDArray[Any], npt.NDArray[Any], npt.NDArray[Any]]]:
        """Generate conformalized quantile prediction intervals.

        Args:
            X: Test features of shape (n_samples, n_features).
            return_quantiles: If True, also return the raw quantile predictions.

        Returns:
            If return_quantiles=False:
                Tuple of (lower_bounds, upper_bounds) for prediction intervals.
            If return_quantiles=True:
                Tuple of (lower_bounds, upper_bounds, q_low, q_high).

        Raises:
            RuntimeError: If predictor has not been calibrated.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before prediction. "
                             "Call calibrate() first.")

        # Convert pandas to numpy
        if isinstance(X, pd.DataFrame):
            X = X.values

        X = np.asarray(X, dtype=np.float32)

        # Get quantile predictions
        q_low = self.model_low.predict(X).ravel()
        q_high = self.model_high.predict(X).ravel()

        # Apply conformal correction
        # C(x) = [q_low(x) - Q_α, q_high(x) + Q_α]
        lower_bounds = q_low - self.correction
        upper_bounds = q_high + self.correction

        if return_quantiles:
            return lower_bounds, upper_bounds, q_low, q_high
        return lower_bounds, upper_bounds

    def get_interval_widths(
        self,
        X: Union[npt.NDArray[np.floating[Any]], pd.DataFrame]
    ) -> npt.NDArray[np.floating[Any]]:
        """Compute prediction interval widths for given inputs.

        Args:
            X: Test features of shape (n_samples, n_features).

        Returns:
            Array of interval widths of shape (n_samples,).
        """
        lower, upper = self.predict(X)
        return upper - lower

    def evaluate_coverage(
        self,
        X_test: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_test: Union[npt.NDArray[Any], pd.Series]
    ) -> dict[str, float]:
        """Evaluate coverage and efficiency metrics on test data.

        Args:
            X_test: Test features of shape (n_samples, n_features).
            y_test: True test labels of shape (n_samples,).

        Returns:
            Dictionary containing:
                - 'coverage': Empirical coverage rate
                - 'mean_width': Mean interval width
                - 'median_width': Median interval width
                - 'width_std': Standard deviation of interval widths
        """
        # Convert pandas to numpy
        if isinstance(y_test, pd.Series):
            y_test = y_test.values
        y_test = np.asarray(y_test).ravel()

        lower, upper = self.predict(X_test)
        widths = upper - lower

        # Check coverage
        covered = (y_test >= lower) & (y_test <= upper)
        coverage = np.mean(covered)

        return {
            'coverage': float(coverage),
            'mean_width': float(np.mean(widths)),
            'median_width': float(np.median(widths)),
            'width_std': float(np.std(widths))
        }

    def plot_intervals(
        self,
        X_test: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_test: Optional[Union[npt.NDArray[Any], pd.Series]] = None,
        indices: Optional[npt.NDArray[np.integer[Any]]] = None,
        max_samples: int = 100
    ) -> None:
        """Visualize prediction intervals.

        Args:
            X_test: Test features.
            y_test: True test labels (optional, for coverage visualization).
            indices: Specific indices to plot. If None, plots first max_samples.
            max_samples: Maximum number of samples to plot if indices not specified.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            warnings.warn("matplotlib not installed. Cannot create plots.")
            return

        lower, upper = self.predict(X_test)

        if indices is None:
            n_samples = min(len(lower), max_samples)
            indices = np.arange(n_samples)
        else:
            indices = np.asarray(indices)

        plt.figure(figsize=(12, 6))

        # Plot intervals
        for i, idx in enumerate(indices):
            plt.plot([i, i], [lower[idx], upper[idx]], 'b-', alpha=0.5, linewidth=2)

        # Plot true values if provided
        if y_test is not None:
            if isinstance(y_test, pd.Series):
                y_test = y_test.values
            y_test = np.asarray(y_test).ravel()

            for i, idx in enumerate(indices):
                color = 'green' if (lower[idx] <= y_test[idx] <= upper[idx]) else 'red'
                plt.scatter(i, y_test[idx], c=color, s=30, zorder=5)

        plt.xlabel('Sample Index')
        plt.ylabel('Value')
        plt.title(f'CQR Prediction Intervals (α={self.alpha})')
        plt.grid(True, alpha=0.3)

        if y_test is not None:
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='blue', alpha=0.5, label='Prediction Interval'),
                plt.scatter([], [], c='green', s=30, label='Covered'),
                plt.scatter([], [], c='red', s=30, label='Not Covered')
            ]
            plt.legend(handles=legend_elements)

        plt.tight_layout()
        plt.show()
