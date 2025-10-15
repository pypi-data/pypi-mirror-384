"""Cross Conformal Prediction implementation.

This module implements the Cross Conformal Prediction algorithm, which uses
K-fold cross-validation to achieve better efficiency than full CP while
maintaining better coverage than split CP.
"""

from typing import Any, Callable, Optional, Union

import numpy as np
import numpy.typing as npt

from cdlf.core.base import BaseConformalPredictor


class CrossConformalPredictor(BaseConformalPredictor):
    """Cross Conformal Prediction for regression and classification.

    Cross CP uses K-fold cross-validation to train K models on K-1 folds
    and calibrate on the held-out fold. This aggregates prediction sets
    across folds for better efficiency than full CP.

    Mathematical guarantee: For exchangeable data, achieves coverage
    ≥ (1-α) with high probability through cross-validation aggregation.

    Attributes:
        model_factory: Function that returns a new model instance.
        nonconformity_func: Function to compute nonconformity scores.
        task: Either 'regression' or 'classification'.
        n_folds: Number of cross-validation folds.
        fold_models: List of trained models for each fold.
        fold_scores: Nonconformity scores for each fold.
        quantiles: Computed quantiles for each fold.
    """

    def __init__(
        self,
        model_factory: Callable,
        alpha: float = 0.1,
        nonconformity_func: Optional[Callable] = None,
        task: str = 'regression',
        n_folds: int = 5,
    ) -> None:
        """Initialize the Cross Conformal Predictor.

        Args:
            model_factory: Function that returns a new trainable model instance.
            alpha: Significance level (1 - confidence level). Must be in (0, 1).
            nonconformity_func: Custom nonconformity function. If None, uses default.
            task: Task type - 'regression' or 'classification'.
            n_folds: Number of cross-validation folds. Must be ≥ 2.

        Raises:
            ValueError: If task is not 'regression' or 'classification'.
            ValueError: If n_folds < 2.
        """
        super().__init__(alpha)

        if task not in ['regression', 'classification']:
            raise ValueError(f"task must be 'regression' or 'classification', got {task}")

        if n_folds < 2:
            raise ValueError(f"n_folds must be at least 2, got {n_folds}")

        self.model_factory = model_factory
        self.task = task
        self.n_folds = n_folds
        self.nonconformity_func = nonconformity_func

        self.fold_models: list[Any] = []
        self.fold_scores: list[npt.NDArray[np.floating[Any]]] = []
        self.quantiles: list[float] = []
        self.n_classes: Optional[int] = None
        self.fold_indices: Optional[list[tuple[npt.NDArray[np.integer[Any]],
                                               npt.NDArray[np.integer[Any]]]]] = None

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

    def _create_folds(
        self,
        n_samples: int
    ) -> list[tuple[npt.NDArray[np.integer[Any]], npt.NDArray[np.integer[Any]]]]:
        """Create K-fold cross-validation indices.

        Args:
            n_samples: Number of samples in the dataset.

        Returns:
            List of (train_indices, val_indices) tuples for each fold.
        """
        indices = np.arange(n_samples)
        np.random.shuffle(indices)

        fold_size = n_samples // self.n_folds
        folds = []

        for k in range(self.n_folds):
            if k < self.n_folds - 1:
                val_indices = indices[k * fold_size:(k + 1) * fold_size]
            else:
                # Last fold gets remaining samples
                val_indices = indices[k * fold_size:]

            train_indices = np.setdiff1d(indices, val_indices)
            folds.append((train_indices, val_indices))

        return folds

    def calibrate(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any],
    ) -> None:
        """Calibrate using K-fold cross-validation.

        Trains K models on K-1 folds and computes nonconformity scores on
        the held-out fold. Stores models and quantiles for each fold.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,) or (n_samples, n_outputs).

        Raises:
            ValueError: If calibration data is empty or has mismatched dimensions.
            ValueError: If n_folds > n_samples.
        """
        # Validate inputs
        if len(X_cal) == 0 or len(y_cal) == 0:
            raise ValueError("Calibration data cannot be empty")

        if len(X_cal) != len(y_cal):
            raise ValueError(f"X_cal and y_cal must have same number of samples, "
                           f"got {len(X_cal)} and {len(y_cal)}")

        n_samples = len(X_cal)

        if self.n_folds > n_samples:
            raise ValueError(f"n_folds ({self.n_folds}) cannot be greater than "
                           f"n_samples ({n_samples})")

        # For classification, determine number of classes
        if self.task == 'classification':
            self.n_classes = len(np.unique(y_cal))

        # Create cross-validation folds
        self.fold_indices = self._create_folds(n_samples)

        # Clear previous calibration
        self.fold_models = []
        self.fold_scores = []
        self.quantiles = []

        # Train models and compute scores for each fold
        all_scores = np.zeros(n_samples)

        for k, (train_idx, val_idx) in enumerate(self.fold_indices):
            # Get training and validation data for this fold
            X_train_fold = X_cal[train_idx]
            y_train_fold = y_cal[train_idx]
            X_val_fold = X_cal[val_idx]
            y_val_fold = y_cal[val_idx]

            # Train model on training fold
            model = self.model_factory()
            model.fit(X_train_fold, y_train_fold)
            self.fold_models.append(model)

            # Compute nonconformity scores on validation fold
            if self.task == 'regression':
                y_pred = model.predict(X_val_fold)
                scores = self.nonconformity_func(y_val_fold, y_pred)
            else:  # classification
                if hasattr(model, 'predict_proba'):
                    y_pred_proba = model.predict_proba(X_val_fold)
                else:
                    y_pred = model.predict(X_val_fold)
                    y_pred_proba = np.zeros((len(val_idx), self.n_classes))
                    for i, pred in enumerate(y_pred):
                        y_pred_proba[i, int(pred)] = 1.0
                scores = self.nonconformity_func(y_val_fold, y_pred_proba)

            # Store scores at their original indices
            all_scores[val_idx] = scores
            self.fold_scores.append(scores)

        # Compute quantile for all scores combined
        # Use the correct formula: ⌈(n+1)(1-α)⌉/n
        q_level = np.ceil((n_samples + 1) * (1 - self.alpha)) / n_samples

        # Handle edge case where q_level > 1
        if q_level > 1:
            q_level = 1.0

        # Compute overall quantile
        self.overall_quantile = np.quantile(all_scores, q_level, method='higher')

        # Also compute per-fold quantiles for alternative aggregation
        for scores in self.fold_scores:
            n_fold = len(scores)
            q_level_fold = np.ceil((n_fold + 1) * (1 - self.alpha)) / n_fold
            if q_level_fold > 1:
                q_level_fold = 1.0
            quantile = np.quantile(scores, q_level_fold, method='higher')
            self.quantiles.append(quantile)

        self.is_calibrated = True

    def predict(
        self,
        X: npt.NDArray[np.floating[Any]],
        aggregation: str = 'union'
    ) -> Union[tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]],
               list[list[int]]]:
        """Generate conformal predictions using cross-validation models.

        Aggregates predictions across all K models using specified method.

        Args:
            X: Test features of shape (n_samples, n_features).
            aggregation: How to aggregate predictions across folds.
                        'union': Take union of all prediction sets (widest intervals).
                        'intersection': Take intersection (narrowest intervals).
                        'median': Use median of fold quantiles.

        Returns:
            For regression: tuple of (lower_bounds, upper_bounds).
            For classification: list of prediction sets (list of valid labels per sample).

        Raises:
            RuntimeError: If the predictor has not been calibrated.
            ValueError: If aggregation method is invalid.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before making predictions")

        if aggregation not in ['union', 'intersection', 'median']:
            raise ValueError(f"aggregation must be 'union', 'intersection', or 'median', "
                           f"got {aggregation}")

        if len(X.shape) < 2:
            X = X.reshape(1, -1)

        n_test = len(X)

        if self.task == 'regression':
            # Get predictions from all models
            all_lower = []
            all_upper = []

            for k, model in enumerate(self.fold_models):
                y_pred = model.predict(X)

                if aggregation == 'median':
                    # Use median quantile
                    quantile = np.median(self.quantiles)
                else:
                    # Use overall quantile for union/intersection
                    quantile = self.overall_quantile

                lower = y_pred - quantile
                upper = y_pred + quantile

                all_lower.append(lower)
                all_upper.append(upper)

            # Aggregate predictions
            all_lower = np.array(all_lower)
            all_upper = np.array(all_upper)

            if aggregation == 'union':
                # Widest intervals
                lower_bounds = np.min(all_lower, axis=0)
                upper_bounds = np.max(all_upper, axis=0)
            elif aggregation == 'intersection':
                # Narrowest intervals
                lower_bounds = np.max(all_lower, axis=0)
                upper_bounds = np.min(all_upper, axis=0)
                # Ensure valid intervals
                invalid = lower_bounds > upper_bounds
                if np.any(invalid):
                    # Fall back to median for invalid intervals
                    median_pred = np.median(np.vstack([all_lower, all_upper]), axis=0)
                    lower_bounds[invalid] = median_pred[invalid]
                    upper_bounds[invalid] = median_pred[invalid]
            else:  # median
                lower_bounds = np.median(all_lower, axis=0)
                upper_bounds = np.median(all_upper, axis=0)

            return lower_bounds, upper_bounds

        else:  # classification
            prediction_sets = []

            for i in range(n_test):
                if aggregation == 'union':
                    # Union of all fold predictions
                    pred_set = set()
                    for model in self.fold_models:
                        if hasattr(model, 'predict_proba'):
                            y_pred_proba = model.predict_proba(X[i:i+1])
                        else:
                            y_pred = model.predict(X[i:i+1])
                            y_pred_proba = np.zeros((1, self.n_classes))
                            y_pred_proba[0, int(y_pred[0])] = 1.0

                        # Add classes with low nonconformity
                        for c in range(self.n_classes):
                            nonconformity = 1.0 - y_pred_proba[0, c]
                            if nonconformity <= self.overall_quantile:
                                pred_set.add(c)
                    pred_set = list(pred_set)

                elif aggregation == 'intersection':
                    # Intersection of all fold predictions
                    pred_sets_per_fold = []
                    for model in self.fold_models:
                        if hasattr(model, 'predict_proba'):
                            y_pred_proba = model.predict_proba(X[i:i+1])
                        else:
                            y_pred = model.predict(X[i:i+1])
                            y_pred_proba = np.zeros((1, self.n_classes))
                            y_pred_proba[0, int(y_pred[0])] = 1.0

                        fold_set = []
                        for c in range(self.n_classes):
                            nonconformity = 1.0 - y_pred_proba[0, c]
                            if nonconformity <= self.overall_quantile:
                                fold_set.append(c)
                        pred_sets_per_fold.append(set(fold_set))

                    # Take intersection
                    if pred_sets_per_fold:
                        pred_set = list(set.intersection(*pred_sets_per_fold))
                    else:
                        pred_set = []

                    # If intersection is empty, use most confident prediction
                    if not pred_set:
                        # Get average probabilities across folds
                        avg_proba = np.zeros(self.n_classes)
                        for model in self.fold_models:
                            if hasattr(model, 'predict_proba'):
                                avg_proba += model.predict_proba(X[i:i+1])[0]
                            else:
                                y_pred = model.predict(X[i:i+1])
                                avg_proba[int(y_pred[0])] += 1.0
                        avg_proba /= len(self.fold_models)
                        pred_set = [np.argmax(avg_proba)]

                else:  # median
                    # Use median quantile approach
                    median_quantile = np.median(self.quantiles)
                    # Average probabilities across folds
                    avg_proba = np.zeros(self.n_classes)
                    for model in self.fold_models:
                        if hasattr(model, 'predict_proba'):
                            avg_proba += model.predict_proba(X[i:i+1])[0]
                        else:
                            y_pred = model.predict(X[i:i+1])
                            avg_proba[int(y_pred[0])] += 1.0
                    avg_proba /= len(self.fold_models)

                    pred_set = []
                    for c in range(self.n_classes):
                        nonconformity = 1.0 - avg_proba[c]
                        if nonconformity <= median_quantile:
                            pred_set.append(c)

                prediction_sets.append(pred_set)

            return prediction_sets

    def get_coverage(
        self,
        X_test: npt.NDArray[np.floating[Any]],
        y_test: npt.NDArray[Any],
        aggregation: str = 'union'
    ) -> float:
        """Compute empirical coverage on test data.

        Args:
            X_test: Test features.
            y_test: True test labels.
            aggregation: Aggregation method for predictions.

        Returns:
            Empirical coverage rate (fraction of correct predictions).
        """
        predictions = self.predict(X_test, aggregation=aggregation)
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
        X: npt.NDArray[np.floating[Any]],
        aggregation: str = 'union'
    ) -> npt.NDArray[np.floating[Any]]:
        """Get prediction interval widths for regression tasks.

        Args:
            X: Test features.
            aggregation: Aggregation method for predictions.

        Returns:
            Array of interval widths.

        Raises:
            ValueError: If called for classification tasks.
        """
        if self.task != 'regression':
            raise ValueError("Interval width is only defined for regression tasks")

        lower, upper = self.predict(X, aggregation=aggregation)
        return upper - lower

    def get_set_sizes(
        self,
        X: npt.NDArray[np.floating[Any]],
        aggregation: str = 'union'
    ) -> npt.NDArray[np.integer[Any]]:
        """Get prediction set sizes for classification tasks.

        Args:
            X: Test features.
            aggregation: Aggregation method for predictions.

        Returns:
            Array of set sizes.

        Raises:
            ValueError: If called for regression tasks.
        """
        if self.task != 'classification':
            raise ValueError("Set size is only defined for classification tasks")

        pred_sets = self.predict(X, aggregation=aggregation)
        return np.array([len(s) for s in pred_sets])

    def get_fold_performance(
        self,
        X_test: npt.NDArray[np.floating[Any]],
        y_test: npt.NDArray[Any]
    ) -> dict[str, Any]:
        """Analyze performance of individual folds.

        Args:
            X_test: Test features.
            y_test: True test labels.

        Returns:
            Dictionary containing per-fold performance metrics.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before analyzing performance")

        fold_coverages = []
        fold_widths = [] if self.task == 'regression' else []
        fold_set_sizes = [] if self.task == 'classification' else []

        for k, model in enumerate(self.fold_models):
            if self.task == 'regression':
                y_pred = model.predict(X_test)
                lower = y_pred - self.quantiles[k]
                upper = y_pred + self.quantiles[k]
                coverage = np.mean((y_test >= lower) & (y_test <= upper))
                width = np.mean(upper - lower)
                fold_coverages.append(coverage)
                fold_widths.append(width)
            else:
                # Classification fold analysis
                if hasattr(model, 'predict_proba'):
                    y_pred_proba = model.predict_proba(X_test)
                else:
                    y_pred = model.predict(X_test)
                    y_pred_proba = np.zeros((len(X_test), self.n_classes))
                    for i, pred in enumerate(y_pred):
                        y_pred_proba[i, int(pred)] = 1.0

                covered = 0
                set_sizes = []
                for i in range(len(X_test)):
                    pred_set = []
                    for c in range(self.n_classes):
                        nonconformity = 1.0 - y_pred_proba[i, c]
                        if nonconformity <= self.quantiles[k]:
                            pred_set.append(c)
                    if int(y_test[i]) in pred_set:
                        covered += 1
                    set_sizes.append(len(pred_set))

                fold_coverages.append(covered / len(X_test))
                fold_set_sizes.append(np.mean(set_sizes))

        results = {
            'fold_coverages': fold_coverages,
            'mean_coverage': np.mean(fold_coverages),
            'std_coverage': np.std(fold_coverages),
        }

        if self.task == 'regression':
            results['fold_widths'] = fold_widths
            results['mean_width'] = np.mean(fold_widths)
            results['std_width'] = np.std(fold_widths)
        else:
            results['fold_set_sizes'] = fold_set_sizes
            results['mean_set_size'] = np.mean(fold_set_sizes)
            results['std_set_size'] = np.std(fold_set_sizes)

        return results