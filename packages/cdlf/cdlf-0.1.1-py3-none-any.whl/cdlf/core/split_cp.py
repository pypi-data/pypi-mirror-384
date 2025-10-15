"""Split Conformal Prediction implementation.

This module implements the Split Conformal Prediction algorithm, which provides
prediction intervals with finite-sample coverage guarantees by splitting the
calibration data and computing nonconformity scores.
"""

from typing import Any, Callable, Optional, Union

import numpy as np
import numpy.typing as npt

from cdlf.core.base import BaseConformalPredictor


class SplitConformalPredictor(BaseConformalPredictor):
    """Split Conformal Prediction for regression and classification.

    Split CP divides the calibration data into two parts: one for training
    the model and one for calibration. It computes nonconformity scores on
    the calibration set and uses these to generate prediction intervals.

    Mathematical guarantee: For exchangeable data, the prediction intervals
    achieve coverage ≥ (1-α) with probability 1.

    Attributes:
        model: The underlying predictive model (must have predict method).
        nonconformity_func: Function to compute nonconformity scores.
        task: Either 'regression' or 'classification'.
        calibration_scores: Stored nonconformity scores from calibration.
        quantile: The computed quantile for the prediction interval.
    """

    def __init__(
        self,
        model: Any,
        alpha: float = 0.1,
        nonconformity_func: Optional[Callable] = None,
        task: str = 'regression',
    ) -> None:
        """Initialize the Split Conformal Predictor.

        Args:
            model: Predictive model with a predict method.
            alpha: Significance level (1 - confidence level). Must be in (0, 1).
            nonconformity_func: Custom nonconformity function. If None, uses default.
            task: Task type - 'regression' or 'classification'.

        Raises:
            ValueError: If task is not 'regression' or 'classification'.
        """
        super().__init__(alpha)

        if task not in ['regression', 'classification']:
            raise ValueError(f"task must be 'regression' or 'classification', got {task}")

        self.model = model
        self.task = task
        self.nonconformity_func = nonconformity_func
        self.calibration_scores: Optional[npt.NDArray[np.floating[Any]]] = None
        self.quantile: Optional[float] = None
        self.n_classes: Optional[int] = None

        # Set default nonconformity functions if not provided
        if self.nonconformity_func is None:
            if task == 'regression':
                self.nonconformity_func = self._default_regression_nonconformity
            else:
                self.nonconformity_func = self._default_classification_nonconformity

    def _default_regression_nonconformity(
        self,
        y_true: npt.NDArray[np.floating[Any]],
        y_pred: npt.NDArray[np.floating[Any]]
    ) -> npt.NDArray[np.floating[Any]]:
        """Default nonconformity function for regression: |y - ŷ|.

        Args:
            y_true: True target values.
            y_pred: Predicted values.

        Returns:
            Array of nonconformity scores.
        """
        return np.abs(y_true - y_pred)

    def _default_classification_nonconformity(
        self,
        y_true: npt.NDArray[Any],
        y_pred_proba: npt.NDArray[np.floating[Any]]
    ) -> npt.NDArray[np.floating[Any]]:
        """Default nonconformity function for classification: 1 - P(y_true).

        Args:
            y_true: True class labels.
            y_pred_proba: Predicted class probabilities.

        Returns:
            Array of nonconformity scores.
        """
        n_samples = len(y_true)
        scores = np.zeros(n_samples)
        for i in range(n_samples):
            scores[i] = 1.0 - y_pred_proba[i, int(y_true[i])]
        return scores

    def calibrate(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any],
    ) -> None:
        """Calibrate the conformal predictor on calibration data.

        Computes nonconformity scores α_i = |y_i - f(x_i)| for regression
        or α_i = 1 - P(y_i) for classification, then computes the quantile
        q = ⌈(n+1)(1-α)⌉/n-th quantile of scores.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,) or (n_samples, n_outputs).

        Raises:
            ValueError: If calibration data is empty or has mismatched dimensions.
        """
        # Validate inputs
        if len(X_cal) == 0 or len(y_cal) == 0:
            raise ValueError("Calibration data cannot be empty")

        if len(X_cal) != len(y_cal):
            raise ValueError(f"X_cal and y_cal must have same number of samples, "
                           f"got {len(X_cal)} and {len(y_cal)}")

        n_cal = len(X_cal)

        # Make predictions on calibration set
        if self.task == 'regression':
            y_pred = self.model.predict(X_cal)
            self.calibration_scores = self.nonconformity_func(y_cal, y_pred)
        else:  # classification
            # Assume model has predict_proba method for classification
            if hasattr(self.model, 'predict_proba'):
                y_pred_proba = self.model.predict_proba(X_cal)
            else:
                # Fallback to one-hot encoding of predictions
                y_pred = self.model.predict(X_cal)
                n_samples = len(y_pred)
                # Infer number of classes
                unique_classes = np.unique(np.concatenate([y_cal, y_pred]))
                self.n_classes = len(unique_classes)
                y_pred_proba = np.zeros((n_samples, self.n_classes))
                for i, pred in enumerate(y_pred):
                    y_pred_proba[i, int(pred)] = 1.0

            if self.n_classes is None:
                self.n_classes = y_pred_proba.shape[1]

            self.calibration_scores = self.nonconformity_func(y_cal, y_pred_proba)

        # Compute quantile using the correct formula: ⌈(n+1)(1-α)⌉
        # This ensures finite-sample coverage guarantee
        q_level = np.ceil((n_cal + 1) * (1 - self.alpha)) / n_cal

        # Handle edge case where q_level > 1
        if q_level > 1:
            q_level = 1.0

        # Compute the quantile of nonconformity scores
        self.quantile = np.quantile(self.calibration_scores, q_level, method='higher')
        self.is_calibrated = True

    def predict(
        self,
        X: npt.NDArray[np.floating[Any]],
    ) -> Union[tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]],
               list[list[int]]]:
        """Generate conformal predictions for new data.

        For regression: returns prediction intervals [f(x) - q, f(x) + q].
        For classification: returns prediction sets containing labels with
        nonconformity scores below the threshold.

        Args:
            X: Test features of shape (n_samples, n_features).

        Returns:
            For regression: tuple of (lower_bounds, upper_bounds).
            For classification: list of prediction sets (list of valid labels per sample).

        Raises:
            RuntimeError: If the predictor has not been calibrated.
            ValueError: If input dimensions are invalid.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before making predictions")

        if len(X.shape) < 2:
            X = X.reshape(1, -1)

        n_test = len(X)

        if self.task == 'regression':
            # Get point predictions
            y_pred = self.model.predict(X)

            # Compute prediction intervals: [ŷ - q, ŷ + q]
            lower_bounds = y_pred - self.quantile
            upper_bounds = y_pred + self.quantile

            return lower_bounds, upper_bounds

        else:  # classification
            # Get predicted probabilities
            if hasattr(self.model, 'predict_proba'):
                y_pred_proba = self.model.predict_proba(X)
            else:
                y_pred = self.model.predict(X)
                y_pred_proba = np.zeros((n_test, self.n_classes))
                for i, pred in enumerate(y_pred):
                    y_pred_proba[i, int(pred)] = 1.0

            # Create prediction sets
            prediction_sets = []
            for i in range(n_test):
                # Include all labels with nonconformity score ≤ quantile
                # Nonconformity for each class: 1 - P(class)
                pred_set = []
                for c in range(self.n_classes):
                    nonconformity = 1.0 - y_pred_proba[i, c]
                    if nonconformity <= self.quantile:
                        pred_set.append(c)
                prediction_sets.append(pred_set)

            return prediction_sets

    def get_coverage(
        self,
        X_test: npt.NDArray[np.floating[Any]],
        y_test: npt.NDArray[Any]
    ) -> float:
        """Compute empirical coverage on test data.

        Args:
            X_test: Test features.
            y_test: True test labels.

        Returns:
            Empirical coverage rate (fraction of correct predictions).
        """
        predictions = self.predict(X_test)
        n_test = len(X_test)

        if self.task == 'regression':
            lower, upper = predictions
            covered = np.sum((y_test >= lower) & (y_test <= upper))
        else:  # classification
            covered = 0
            for i, pred_set in enumerate(predictions):
                if int(y_test[i]) in pred_set:
                    covered += 1

        return covered / n_test

    def get_interval_width(
        self,
        X: npt.NDArray[np.floating[Any]]
    ) -> npt.NDArray[np.floating[Any]]:
        """Get prediction interval widths for regression tasks.

        Args:
            X: Test features.

        Returns:
            Array of interval widths.

        Raises:
            ValueError: If called for classification tasks.
        """
        if self.task != 'regression':
            raise ValueError("Interval width is only defined for regression tasks")

        lower, upper = self.predict(X)
        return upper - lower

    def get_set_sizes(
        self,
        X: npt.NDArray[np.floating[Any]]
    ) -> npt.NDArray[np.integer[Any]]:
        """Get prediction set sizes for classification tasks.

        Args:
            X: Test features.

        Returns:
            Array of set sizes.

        Raises:
            ValueError: If called for regression tasks.
        """
        if self.task != 'classification':
            raise ValueError("Set size is only defined for classification tasks")

        pred_sets = self.predict(X)
        return np.array([len(s) for s in pred_sets])
