"""Full Conformal Prediction implementation.

This module implements the Full Conformal Prediction algorithm, which provides
exact finite-sample coverage guarantees without data splitting at the cost of
increased computational complexity.
"""

from typing import Any, Callable, Optional, Union

import numpy as np
import numpy.typing as npt

from cdlf.core.base import BaseConformalPredictor


class FullConformalPredictor(BaseConformalPredictor):
    """Full Conformal Prediction for regression and classification.

    Full CP computes nonconformity scores for each possible label by including
    it in the calibration set. This provides exact (1-α) coverage but requires
    retraining or re-evaluating the model for each test point.

    Mathematical guarantee: For exchangeable data, achieves exact (1-α) coverage
    with probability 1, without requiring data splitting.

    Attributes:
        model_factory: Function that returns a new model instance.
        nonconformity_func: Function to compute nonconformity scores.
        task: Either 'regression' or 'classification'.
        training_data: Stored training data for model retraining.
        grid_resolution: For regression, number of candidate values to test.
    """

    def __init__(
        self,
        model_factory: Callable,
        alpha: float = 0.1,
        nonconformity_func: Optional[Callable] = None,
        task: str = 'regression',
        grid_resolution: int = 100,
    ) -> None:
        """Initialize the Full Conformal Predictor.

        Args:
            model_factory: Function that returns a new trainable model instance.
            alpha: Significance level (1 - confidence level). Must be in (0, 1).
            nonconformity_func: Custom nonconformity function. If None, uses default.
            task: Task type - 'regression' or 'classification'.
            grid_resolution: Number of candidate values for regression tasks.

        Raises:
            ValueError: If task is not 'regression' or 'classification'.
        """
        super().__init__(alpha)

        if task not in ['regression', 'classification']:
            raise ValueError(f"task must be 'regression' or 'classification', got {task}")

        self.model_factory = model_factory
        self.task = task
        self.nonconformity_func = nonconformity_func
        self.grid_resolution = grid_resolution
        self.X_train: Optional[npt.NDArray[np.floating[Any]]] = None
        self.y_train: Optional[npt.NDArray[Any]] = None
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
        """Store training data for full conformal prediction.

        In Full CP, calibration involves storing the training data that will
        be used to compute p-values for test points.

        Args:
            X_cal: Training features of shape (n_samples, n_features).
            y_cal: Training labels of shape (n_samples,) or (n_samples, n_outputs).

        Raises:
            ValueError: If calibration data is empty or has mismatched dimensions.
        """
        # Validate inputs
        if len(X_cal) == 0 or len(y_cal) == 0:
            raise ValueError("Calibration data cannot be empty")

        if len(X_cal) != len(y_cal):
            raise ValueError(f"X_cal and y_cal must have same number of samples, "
                           f"got {len(X_cal)} and {len(y_cal)}")

        # Store training data
        self.X_train = X_cal.copy()
        self.y_train = y_cal.copy()

        # For classification, determine number of classes
        if self.task == 'classification':
            self.n_classes = len(np.unique(y_cal))

        self.is_calibrated = True

    def _compute_p_value(
        self,
        x_test: npt.NDArray[np.floating[Any]],
        y_candidate: Any
    ) -> float:
        """Compute p-value for a test point with candidate label.

        The p-value is computed as the proportion of training points with
        nonconformity scores greater than or equal to the test point's score.

        Args:
            x_test: Test feature vector of shape (n_features,).
            y_candidate: Candidate label/value to test.

        Returns:
            P-value for the candidate label.
        """
        n_train = len(self.X_train)

        # Augment training data with test point
        X_aug = np.vstack([self.X_train, x_test.reshape(1, -1)])
        y_aug = np.append(self.y_train, y_candidate)

        # Train model on augmented data
        model = self.model_factory()
        model.fit(X_aug, y_aug)

        # Compute nonconformity scores
        if self.task == 'regression':
            y_pred = model.predict(X_aug)
            scores = self.nonconformity_func(y_aug, y_pred)
        else:  # classification
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_aug)
            else:
                y_pred = model.predict(X_aug)
                y_pred_proba = np.zeros((n_train + 1, self.n_classes))
                for i, pred in enumerate(y_pred):
                    y_pred_proba[i, int(pred)] = 1.0
            scores = self.nonconformity_func(y_aug, y_pred_proba)

        # Compute p-value: proportion of scores ≥ test score
        test_score = scores[-1]
        p_value = np.sum(scores >= test_score) / (n_train + 1)

        return p_value

    def predict(
        self,
        X: npt.NDArray[np.floating[Any]],
    ) -> Union[tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]],
               list[list[int]]]:
        """Generate conformal predictions for new data.

        For regression: tests a grid of candidate values and returns interval.
        For classification: tests all possible class labels.

        Args:
            X: Test features of shape (n_samples, n_features).

        Returns:
            For regression: tuple of (lower_bounds, upper_bounds).
            For classification: list of prediction sets (list of valid labels per sample).

        Raises:
            RuntimeError: If the predictor has not been calibrated.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before making predictions")

        if len(X.shape) < 2:
            X = X.reshape(1, -1)

        n_test = len(X)

        if self.task == 'regression':
            # For regression, we need to test a grid of candidate values
            # First, get a rough prediction to center the grid
            model_init = self.model_factory()
            model_init.fit(self.X_train, self.y_train)
            y_rough = model_init.predict(X)

            lower_bounds = np.zeros(n_test)
            upper_bounds = np.zeros(n_test)

            for i in range(n_test):
                # Create grid of candidate values around rough prediction
                y_min = self.y_train.min()
                y_max = self.y_train.max()
                y_range = y_max - y_min

                # Center grid around rough prediction with wider range
                grid_center = y_rough[i] if len(y_rough.shape) > 0 else y_rough
                grid_min = grid_center - 2 * y_range
                grid_max = grid_center + 2 * y_range

                candidates = np.linspace(grid_min, grid_max, self.grid_resolution)

                # Compute p-values for all candidates
                p_values = []
                for y_cand in candidates:
                    p_val = self._compute_p_value(X[i], y_cand)
                    p_values.append(p_val)

                # Include candidates with p-value > α
                accepted = candidates[np.array(p_values) > self.alpha]

                if len(accepted) > 0:
                    lower_bounds[i] = accepted.min()
                    upper_bounds[i] = accepted.max()
                else:
                    # If no candidates accepted, use rough prediction
                    lower_bounds[i] = grid_center
                    upper_bounds[i] = grid_center

            return lower_bounds, upper_bounds

        else:  # classification
            prediction_sets = []

            for i in range(n_test):
                pred_set = []

                # Test each possible class label
                for c in range(self.n_classes):
                    p_val = self._compute_p_value(X[i], c)

                    # Include class if p-value > α
                    if p_val > self.alpha:
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

    def predict_fast_approximation(
        self,
        X: npt.NDArray[np.floating[Any]],
    ) -> Union[tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]],
               list[list[int]]]:
        """Fast approximation using a single trained model.

        This method trains the model once on all training data and uses
        nonconformity scores to approximate the full CP prediction sets.
        Less computationally expensive but provides weaker guarantees.

        Args:
            X: Test features of shape (n_samples, n_features).

        Returns:
            For regression: tuple of (lower_bounds, upper_bounds).
            For classification: list of prediction sets.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before making predictions")

        # Train model once on all training data
        model = self.model_factory()
        model.fit(self.X_train, self.y_train)

        # Compute training nonconformity scores
        if self.task == 'regression':
            y_train_pred = model.predict(self.X_train)
            train_scores = self.nonconformity_func(self.y_train, y_train_pred)

            # Use quantile of training scores
            n_train = len(self.X_train)
            q_level = np.ceil((n_train + 1) * (1 - self.alpha)) / n_train
            if q_level > 1:
                q_level = 1.0
            quantile = np.quantile(train_scores, q_level, method='higher')

            # Make predictions
            y_pred = model.predict(X)
            lower_bounds = y_pred - quantile
            upper_bounds = y_pred + quantile

            return lower_bounds, upper_bounds

        else:  # classification
            # This approximation is less accurate for classification
            # Fall back to regular prediction
            return self.predict(X)