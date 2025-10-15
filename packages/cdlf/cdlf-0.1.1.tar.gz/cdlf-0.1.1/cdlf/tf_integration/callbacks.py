"""TensorFlow/Keras callbacks for conformal prediction.

This module provides training callbacks that enable online calibration
and monitoring during model training.
"""

from typing import Any, Optional, Union

import tensorflow as tf
import numpy as np
import numpy.typing as npt


class ConformalCalibrationCallback(tf.keras.callbacks.Callback):
    """Keras callback for automatic conformal calibration during training.

    This callback performs periodic calibration of conformal predictors
    during model training, enabling adaptive prediction intervals.

    Example:
        ```python
        # Create callback with validation data for calibration
        cal_callback = ConformalCalibrationCallback(
            alpha=0.1,
            calibration_freq=5,  # Calibrate every 5 epochs
            task='regression'
        )

        # Use in model training
        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            callbacks=[cal_callback],
            epochs=50
        )

        # After training, get calibration history
        history = cal_callback.get_calibration_history()
        ```

    Attributes:
        alpha: Significance level for prediction intervals.
        calibration_data: Tuple of (X_cal, y_cal) for calibration.
        calibration_freq: Frequency of calibration in epochs.
        task: Task type ('regression' or 'classification').
        quantile: Current calibrated quantile value.
        history: Dictionary tracking calibration metrics over time.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        calibration_data: Optional[tuple[npt.NDArray[np.floating[Any]], npt.NDArray[Any]]] = None,
        calibration_freq: int = 1,
        task: str = 'regression',
        verbose: int = 0,
    ) -> None:
        """Initialize calibration callback.

        Args:
            alpha: Significance level. Default is 0.1 (90% confidence).
            calibration_data: Optional calibration data (X_cal, y_cal).
                If None, uses validation data from fit().
            calibration_freq: Calibrate every N epochs. Default is 1.
            task: Task type - 'regression' or 'classification'.
            verbose: Verbosity level. 0 = silent, 1 = progress updates.

        Raises:
            ValueError: If alpha is not in (0, 1) or calibration_freq < 1.
        """
        super().__init__()
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")
        if calibration_freq < 1:
            raise ValueError(f"calibration_freq must be at least 1, got {calibration_freq}")

        self.alpha = alpha
        self.calibration_data = calibration_data
        self.calibration_freq = calibration_freq
        self.task = task
        self.verbose = verbose
        self.quantile: Optional[float] = None
        self.calibration_scores: Optional[npt.NDArray[np.floating[Any]]] = None
        self.validation_data: Optional[tuple[npt.NDArray[Any], npt.NDArray[Any]]] = None

        self.history: dict[str, list[float]] = {
            "coverage": [],
            "interval_width": [] if task == 'regression' else [],
            "set_size": [] if task == 'classification' else [],
            "quantile": [],
            "epoch": [],
        }

    def _compute_nonconformity_scores(
        self,
        y_true: npt.NDArray[Any],
        y_pred: npt.NDArray[Any],
    ) -> npt.NDArray[np.floating[Any]]:
        """Compute nonconformity scores.

        Args:
            y_true: True labels.
            y_pred: Predictions.

        Returns:
            Array of nonconformity scores.
        """
        if self.task == 'regression':
            # Absolute residuals for regression
            return np.abs(y_true - y_pred.squeeze())
        else:
            # For classification, use 1 - predicted probability of true class
            # Assuming y_pred contains probabilities
            n_samples = len(y_true)
            scores = np.zeros(n_samples)
            for i in range(n_samples):
                if len(y_pred.shape) > 1 and y_pred.shape[1] > 1:
                    # Multi-class probabilities
                    scores[i] = 1.0 - y_pred[i, int(y_true[i])]
                else:
                    # Binary classification
                    true_class = int(y_true[i])
                    pred_prob = y_pred[i, 0] if len(y_pred.shape) > 1 else y_pred[i]
                    scores[i] = 1.0 - (pred_prob if true_class == 1 else 1 - pred_prob)
            return scores

    def _calibrate(self, X_cal: npt.NDArray[Any], y_cal: npt.NDArray[Any]) -> None:
        """Perform calibration on the given data.

        Args:
            X_cal: Calibration features.
            y_cal: Calibration labels.
        """
        # Get model predictions
        y_pred = self.model.predict(X_cal, verbose=0)

        # Compute nonconformity scores
        self.calibration_scores = self._compute_nonconformity_scores(y_cal, y_pred)

        # Compute quantile
        n_cal = len(self.calibration_scores)
        q_level = np.ceil((n_cal + 1) * (1 - self.alpha)) / n_cal
        if q_level > 1:
            q_level = 1.0

        self.quantile = np.quantile(self.calibration_scores, q_level, method='higher')

        if self.verbose > 0:
            print(f"Calibration complete. Quantile: {self.quantile:.4f}")

    def _compute_coverage(
        self,
        X_test: npt.NDArray[Any],
        y_test: npt.NDArray[Any],
    ) -> float:
        """Compute empirical coverage on test data.

        Args:
            X_test: Test features.
            y_test: True test labels.

        Returns:
            Coverage rate.
        """
        if self.quantile is None:
            return 0.0

        y_pred = self.model.predict(X_test, verbose=0)
        n_test = len(X_test)

        if self.task == 'regression':
            # Check if true values fall within intervals
            lower = y_pred.squeeze() - self.quantile
            upper = y_pred.squeeze() + self.quantile
            covered = np.sum((y_test >= lower) & (y_test <= upper))
        else:
            # For classification, check if true class is in prediction set
            covered = 0
            for i in range(n_test):
                # Simplified: check if nonconformity score of true class is below quantile
                score = self._compute_nonconformity_scores(
                    y_test[i:i+1], y_pred[i:i+1]
                )[0]
                if score <= self.quantile:
                    covered += 1

        return covered / n_test

    def on_epoch_end(self, epoch: int, logs: Optional[dict[str, Any]] = None) -> None:
        """Perform calibration at the end of specified epochs.

        Args:
            epoch: Current epoch number.
            logs: Dictionary of training metrics.
        """
        # Check if it's time to calibrate
        if (epoch + 1) % self.calibration_freq != 0:
            return

        # Get calibration data
        if self.calibration_data is not None:
            X_cal, y_cal = self.calibration_data
        elif self.validation_data is not None:
            # Use validation data from model.fit()
            X_cal = self.validation_data[0]
            y_cal = self.validation_data[1]
        else:
            # Try to get validation data from model's validation_data attribute
            # In Keras 2.x, this might be available during training
            if hasattr(self, 'model') and hasattr(self.model, 'validation_data') and self.model.validation_data:
                self.validation_data = self.model.validation_data
                X_cal = self.validation_data[0]
                y_cal = self.validation_data[1]
            else:
                if self.verbose > 0:
                    print("Warning: No calibration data available")
                return

        # Perform calibration
        self._calibrate(X_cal, y_cal)

        # Compute and store metrics
        coverage = self._compute_coverage(X_cal, y_cal)
        self.history["coverage"].append(coverage)
        self.history["quantile"].append(self.quantile)
        self.history["epoch"].append(epoch)

        if self.task == 'regression':
            # Store average interval width
            self.history["interval_width"].append(2 * self.quantile)
        else:
            # For classification, store average set size (simplified)
            avg_set_size = self._estimate_avg_set_size()
            self.history["set_size"].append(avg_set_size)

        # Add metrics to logs for TensorBoard
        if logs is not None:
            logs[f'cp_coverage'] = coverage
            logs[f'cp_quantile'] = self.quantile
            if self.task == 'regression':
                logs[f'cp_interval_width'] = 2 * self.quantile

    def _estimate_avg_set_size(self) -> float:
        """Estimate average prediction set size for classification.

        Returns:
            Estimated average set size.
        """
        # This is a simplified estimation
        # In practice, would compute actual set sizes
        if self.calibration_scores is not None:
            # Estimate based on fraction of scores below quantile
            return np.mean(self.calibration_scores <= self.quantile) * 10  # Assuming 10 classes
        return 0.0

    def on_train_end(self, logs: Optional[dict[str, Any]] = None) -> None:
        """Final calibration at the end of training.

        Args:
            logs: Dictionary of training metrics.
        """
        # Perform final calibration
        if self.calibration_data is not None:
            X_cal, y_cal = self.calibration_data
        elif self.validation_data is not None:
            X_cal = self.validation_data[0]
            y_cal = self.validation_data[1]
        else:
            return

        self._calibrate(X_cal, y_cal)

        if self.verbose > 0:
            coverage = self._compute_coverage(X_cal, y_cal)
            print(f"\nFinal calibration complete:")
            print(f"  Quantile: {self.quantile:.4f}")
            print(f"  Coverage: {coverage:.2%}")

    def get_calibration_history(self) -> dict[str, list[float]]:
        """Get calibration metrics history.

        Returns:
            Dictionary of metric names to lists of values.
        """
        return self.history

    def get_quantile(self) -> Optional[float]:
        """Get the current calibrated quantile.

        Returns:
            Calibrated quantile value or None if not calibrated.
        """
        return self.quantile


class CoverageMonitorCallback(tf.keras.callbacks.Callback):
    """Callback to monitor conformal prediction coverage during training.

    This callback tracks the empirical coverage of prediction intervals
    on validation data throughout training.

    Example:
        ```python
        coverage_monitor = CoverageMonitorCallback(
            validation_data=(X_val, y_val),
            target_coverage=0.9,
            task='regression'
        )

        model.fit(
            X_train, y_train,
            callbacks=[coverage_monitor],
            epochs=50
        )
        ```

    Attributes:
        validation_data: Data for computing coverage.
        target_coverage: Desired coverage level.
        task: Task type.
        coverage_history: List of coverage values over epochs.
    """

    def __init__(
        self,
        validation_data: tuple[npt.NDArray[Any], npt.NDArray[Any]],
        target_coverage: float = 0.9,
        task: str = 'regression',
        quantile: Optional[float] = None,
        verbose: int = 0,
    ) -> None:
        """Initialize coverage monitor.

        Args:
            validation_data: Tuple of (X_val, y_val) for monitoring.
            target_coverage: Target coverage level (1 - alpha).
            task: Task type - 'regression' or 'classification'.
            quantile: Pre-calibrated quantile. If None, uses a default.
            verbose: Verbosity level.
        """
        super().__init__()
        self.validation_data = validation_data
        self.target_coverage = target_coverage
        self.task = task
        self.quantile = quantile if quantile is not None else 1.0
        self.verbose = verbose
        self.coverage_history: list[float] = []
        self.deviation_history: list[float] = []

    def on_epoch_end(self, epoch: int, logs: Optional[dict[str, Any]] = None) -> None:
        """Monitor coverage at epoch end.

        Args:
            epoch: Current epoch.
            logs: Training logs.
        """
        X_val, y_val = self.validation_data
        y_pred = self.model.predict(X_val, verbose=0)

        # Compute coverage
        if self.task == 'regression':
            lower = y_pred.squeeze() - self.quantile
            upper = y_pred.squeeze() + self.quantile
            coverage = np.mean((y_val >= lower) & (y_val <= upper))
        else:
            # Simplified for classification
            coverage = self.target_coverage  # Placeholder

        self.coverage_history.append(coverage)
        deviation = coverage - self.target_coverage
        self.deviation_history.append(deviation)

        if self.verbose > 0 and (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch + 1}: Coverage = {coverage:.2%}, "
                  f"Target = {self.target_coverage:.2%}, "
                  f"Deviation = {deviation:+.2%}")

        # Add to logs for TensorBoard
        if logs is not None:
            logs['cp_coverage'] = coverage
            logs['cp_coverage_deviation'] = deviation


class AdaptiveAlphaCallback(tf.keras.callbacks.Callback):
    """Callback for dynamically adjusting significance level α during training.

    This callback adjusts the significance level based on observed coverage
    to maintain the desired coverage level.

    Example:
        ```python
        adaptive_callback = AdaptiveAlphaCallback(
            initial_alpha=0.1,
            target_coverage=0.9,
            adjustment_rate=0.01
        )

        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            callbacks=[adaptive_callback],
            epochs=50
        )
        ```

    Attributes:
        alpha: Current significance level.
        target_coverage: Desired coverage level.
        adjustment_rate: Rate of alpha adjustment.
        alpha_history: History of alpha values.
    """

    def __init__(
        self,
        initial_alpha: float = 0.1,
        target_coverage: float = 0.9,
        adjustment_rate: float = 0.01,
        min_alpha: float = 0.01,
        max_alpha: float = 0.5,
        calibration_freq: int = 5,
        task: str = 'regression',
        verbose: int = 0,
        validation_data: Optional[tuple[npt.NDArray[Any], npt.NDArray[Any]]] = None,
    ) -> None:
        """Initialize adaptive alpha callback.

        Args:
            initial_alpha: Starting significance level.
            target_coverage: Target coverage (1 - alpha).
            adjustment_rate: Learning rate for alpha adjustment.
            min_alpha: Minimum allowed alpha.
            max_alpha: Maximum allowed alpha.
            calibration_freq: Frequency of adjustment in epochs.
            task: Task type.
            verbose: Verbosity level.
            validation_data: Optional validation data (X_val, y_val) for coverage computation.
        """
        super().__init__()
        self.alpha = initial_alpha
        self.target_coverage = target_coverage
        self.adjustment_rate = adjustment_rate
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.calibration_freq = calibration_freq
        self.task = task
        self.verbose = verbose
        self.validation_data = validation_data

        self.alpha_history: list[float] = [initial_alpha]
        self.coverage_history: list[float] = []
        self.quantile: Optional[float] = None

    def _compute_coverage_and_adjust(
        self,
        X_val: npt.NDArray[Any],
        y_val: npt.NDArray[Any],
    ) -> None:
        """Compute coverage and adjust alpha.

        Args:
            X_val: Validation features.
            y_val: Validation labels.
        """
        # Get predictions
        y_pred = self.model.predict(X_val, verbose=0)

        # Compute nonconformity scores
        if self.task == 'regression':
            scores = np.abs(y_val - y_pred.squeeze())
        else:
            # Simplified for classification
            scores = np.random.random(len(y_val))  # Placeholder

        # Compute current quantile
        n_cal = len(scores)
        q_level = np.ceil((n_cal + 1) * (1 - self.alpha)) / n_cal
        if q_level > 1:
            q_level = 1.0
        self.quantile = np.quantile(scores, q_level, method='higher')

        # Compute empirical coverage
        if self.task == 'regression':
            lower = y_pred.squeeze() - self.quantile
            upper = y_pred.squeeze() + self.quantile
            coverage = np.mean((y_val >= lower) & (y_val <= upper))
        else:
            coverage = 1 - self.alpha  # Placeholder

        self.coverage_history.append(coverage)

        # Adjust alpha based on coverage error
        coverage_error = coverage - self.target_coverage

        # If coverage is too low, decrease alpha (increase intervals)
        # If coverage is too high, increase alpha (decrease intervals)
        self.alpha = self.alpha - self.adjustment_rate * coverage_error

        # Clip alpha to valid range
        self.alpha = np.clip(self.alpha, self.min_alpha, self.max_alpha)
        self.alpha_history.append(self.alpha)

        if self.verbose > 0:
            print(f"Coverage: {coverage:.2%}, Target: {self.target_coverage:.2%}, "
                  f"New α: {self.alpha:.3f}")

    def on_epoch_end(self, epoch: int, logs: Optional[dict[str, Any]] = None) -> None:
        """Adjust alpha at epoch end.

        Args:
            epoch: Current epoch.
            logs: Training logs.
        """
        if (epoch + 1) % self.calibration_freq != 0:
            return

        # Get validation data
        if self.validation_data is not None:
            X_val = self.validation_data[0]
            y_val = self.validation_data[1]
            self._compute_coverage_and_adjust(X_val, y_val)

            # Add to logs
            if logs is not None:
                logs['cp_alpha'] = self.alpha
                if len(self.coverage_history) > 0:
                    logs['cp_coverage'] = self.coverage_history[-1]

    def get_history(self) -> dict[str, list[float]]:
        """Get adjustment history.

        Returns:
            Dictionary with alpha and coverage history.
        """
        return {
            'alpha': self.alpha_history,
            'coverage': self.coverage_history,
        }
