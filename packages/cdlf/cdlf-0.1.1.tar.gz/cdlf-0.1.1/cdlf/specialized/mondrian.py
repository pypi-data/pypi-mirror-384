"""Mondrian conformal prediction implementation.

This module implements Mondrian conformal prediction, which provides
conditional validity by performing conformal calibration separately
for different groups or categories.

Reference: Vovk et al. (2005) - "Algorithmic Learning in a Random World"
Chapter 4: Conditional Prediction

Mathematical Formulation:
1. Partition the data space into K disjoint categories/groups
2. For each category k, compute nonconformity scores separately:
   - Classification: A_i^k = 1 - p(y_i | x_i) for samples in category k
   - Regression: A_i^k = |y_i - ŷ_i| for samples in category k
3. For each category k, find the (1-α) quantile Q_α^k
4. For prediction on new sample x in category k:
   - Use the category-specific threshold Q_α^k
   - Classification: Include class j if p(j|x) >= 1 - Q_α^k
   - Regression: Interval = [ŷ - Q_α^k, ŷ + Q_α^k]

This provides class-conditional or feature-conditional coverage guarantees,
which is especially useful for imbalanced datasets or heterogeneous data.
"""

from typing import Any, Optional, Union, Callable, Dict, List, Set
import warnings

import numpy as np
import numpy.typing as npt
import pandas as pd

from cdlf.core.base import BaseConformalPredictor


class MondrianConformalPredictor(BaseConformalPredictor):
    """Mondrian conformal prediction for conditional validity.

    This implementation provides separate calibration for different categories
    or groups, enabling conditional coverage guarantees. Particularly effective
    for imbalanced datasets where global calibration may not provide adequate
    coverage for minority classes.

    Attributes:
        base_cp: Base conformal predictor to use within each category.
        alpha: Significance level (1 - confidence level).
        strategy: Strategy for categorization ('per_class' or 'custom').
        category_fn: Function to extract category from features (for 'custom' strategy).
        class_quantiles: Dictionary mapping classes/categories to their quantiles.
        class_scores: Dictionary storing nonconformity scores per class.
        task: Task type ('classification' or 'regression').
        min_samples_per_class: Minimum samples required per class for calibration.

    Example:
        >>> import numpy as np
        >>> from sklearn.ensemble import RandomForestClassifier
        >>> from cdlf.specialized.mondrian import MondrianConformalPredictor
        >>>
        >>> # Create and train classifier
        >>> model = RandomForestClassifier()
        >>> X_train = np.random.randn(1000, 10)
        >>> y_train = np.random.randint(0, 3, 1000)  # 3 classes
        >>> model.fit(X_train, y_train)
        >>>
        >>> # Initialize Mondrian CP with per-class calibration
        >>> mondrian_cp = MondrianConformalPredictor(
        ...     base_cp=model,
        ...     alpha=0.1,
        ...     strategy='per_class'
        ... )
        >>>
        >>> # Calibrate with class-specific thresholds
        >>> X_cal = np.random.randn(500, 10)
        >>> y_cal = np.random.randint(0, 3, 500)
        >>> mondrian_cp.calibrate_per_class(X_cal, y_cal)
        >>>
        >>> # Generate prediction sets
        >>> X_test = np.random.randn(100, 10)
        >>> prediction_sets = mondrian_cp.predict(X_test)
    """

    def __init__(
        self,
        base_cp: Any,
        alpha: float = 0.1,
        strategy: str = 'per_class',
        category_fn: Optional[Callable[[npt.NDArray[np.floating[Any]]], npt.NDArray[Any]]] = None,
        task: str = 'classification',
        min_samples_per_class: int = 10
    ) -> None:
        """Initialize Mondrian conformal predictor.

        Args:
            base_cp: Base conformal predictor or model with predict/predict_proba methods.
            alpha: Significance level. Default is 0.1 (90% confidence).
            strategy: Strategy for categorization:
                - 'per_class': Separate calibration per class (classification)
                - 'custom': Use custom category_fn for grouping
            category_fn: Function that extracts category from features (required if strategy='custom').
                Should take array of shape (n_samples, n_features) and return
                array of shape (n_samples,) with category labels.
            task: Task type ('classification' or 'regression').
            min_samples_per_class: Minimum samples required per class for calibration.

        Raises:
            ValueError: If strategy is 'custom' but category_fn is not provided.
        """
        super().__init__(alpha=alpha)

        if strategy == 'custom' and category_fn is None:
            raise ValueError("category_fn must be provided when strategy='custom'")

        self.base_cp = base_cp
        self.strategy = strategy
        self.category_fn = category_fn
        self.task = task
        self.min_samples_per_class = min_samples_per_class

        self.class_quantiles: Dict[Any, float] = {}
        self.class_scores: Dict[Any, npt.NDArray[np.floating[Any]]] = {}
        self.classes_: Optional[npt.NDArray[Any]] = None

    def calibrate_per_class(
        self,
        X_cal: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_cal: Union[npt.NDArray[Any], pd.Series],
    ) -> None:
        """Calibrate separately for each class/category.

        Computes class-specific nonconformity scores and quantiles for
        conditional coverage guarantees.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,).

        Raises:
            ValueError: If any class has insufficient calibration samples.
            RuntimeError: If base model hasn't been fitted.
        """
        # Convert pandas to numpy
        if isinstance(X_cal, pd.DataFrame):
            X_cal = X_cal.values
        if isinstance(y_cal, pd.Series):
            y_cal = y_cal.values

        X_cal = np.asarray(X_cal, dtype=np.float32)
        y_cal = np.asarray(y_cal)

        if self.task == 'classification':
            self._calibrate_classification(X_cal, y_cal)
        else:
            self._calibrate_regression(X_cal, y_cal)

        self.is_calibrated = True

    def _calibrate_classification(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any]
    ) -> None:
        """Calibrate for classification task."""
        # Get predictions
        if hasattr(self.base_cp, 'predict_proba'):
            proba = self.base_cp.predict_proba(X_cal)
        else:
            raise RuntimeError("Base model must have predict_proba method for classification")

        # Get unique classes
        self.classes_ = np.unique(y_cal)

        # Map class labels to indices in probability matrix
        if hasattr(self.base_cp, 'classes_'):
            # Use the model's class ordering
            model_classes = self.base_cp.classes_
        else:
            # Assume classes are 0-indexed
            model_classes = np.arange(proba.shape[1])

        # Compute nonconformity scores per class
        for class_label in self.classes_:
            # Get samples belonging to this class
            class_mask = (y_cal == class_label)
            n_class_samples = np.sum(class_mask)

            if n_class_samples < self.min_samples_per_class:
                warnings.warn(
                    f"Class {class_label} has only {n_class_samples} calibration samples "
                    f"(minimum recommended: {self.min_samples_per_class}). "
                    "Coverage guarantees may be unreliable.",
                    RuntimeWarning
                )

            if n_class_samples == 0:
                raise ValueError(f"Class {class_label} has no calibration samples")

            # Find the correct index for this class in the probability matrix
            class_idx = np.where(model_classes == class_label)[0]
            if len(class_idx) == 0:
                raise ValueError(f"Class {class_label} not found in model's classes")
            class_idx = class_idx[0]

            # Nonconformity scores: 1 - p(true_class | x)
            class_proba = proba[class_mask, class_idx]
            nonconformity_scores = 1 - class_proba

            # Store scores
            self.class_scores[class_label] = nonconformity_scores

            # Compute class-specific quantile
            n = len(nonconformity_scores)
            level = np.ceil((1 - self.alpha) * (n + 1)) / n
            level = min(level, 1.0)

            self.class_quantiles[class_label] = np.quantile(nonconformity_scores, level)

    def _calibrate_regression(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any]
    ) -> None:
        """Calibrate for regression task."""
        # Get predictions
        y_pred = self.base_cp.predict(X_cal).ravel()
        y_cal = y_cal.ravel()

        # Determine categories
        if self.strategy == 'custom':
            categories = self.category_fn(X_cal)
        else:
            # For regression with per_class, discretize the output space
            # Use quartiles as default categorization
            quartiles = np.percentile(y_cal, [25, 50, 75])
            categories = np.digitize(y_cal, quartiles)

        unique_categories = np.unique(categories)

        # Compute nonconformity scores per category
        for category in unique_categories:
            category_mask = (categories == category)
            n_category_samples = np.sum(category_mask)

            if n_category_samples < self.min_samples_per_class:
                warnings.warn(
                    f"Category {category} has only {n_category_samples} calibration samples",
                    RuntimeWarning
                )

            # Nonconformity scores: |y - ŷ|
            residuals = np.abs(y_cal[category_mask] - y_pred[category_mask])
            self.class_scores[category] = residuals

            # Compute category-specific quantile
            n = len(residuals)
            level = np.ceil((1 - self.alpha) * (n + 1)) / n
            level = min(level, 1.0)

            self.class_quantiles[category] = np.quantile(residuals, level)

    def calibrate(
        self,
        X_cal: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_cal: Union[npt.NDArray[Any], pd.Series],
    ) -> None:
        """Calibrate separately for each category.

        This is an alias for calibrate_per_class() to maintain compatibility
        with the base class interface.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,).
        """
        self.calibrate_per_class(X_cal, y_cal)

    def predict(
        self,
        X: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        return_class_info: bool = False
    ) -> Union[List[Set[int]], tuple[npt.NDArray[Any], npt.NDArray[Any]],
               tuple[Any, Dict[int, Any]]]:
        """Generate category-specific conformal predictions.

        Args:
            X: Test features of shape (n_samples, n_features).
            return_class_info: If True, also return class/category assignments.

        Returns:
            For classification:
                List of prediction sets (sets of predicted class labels).
            For regression:
                Tuple of (lower_bounds, upper_bounds) for prediction intervals.
            If return_class_info=True:
                Tuple of (predictions, class_assignments).

        Raises:
            RuntimeError: If predictor has not been calibrated.
            ValueError: If test data contains unseen categories.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before prediction. "
                             "Call calibrate_per_class() first.")

        # Convert pandas to numpy
        if isinstance(X, pd.DataFrame):
            X = X.values

        X = np.asarray(X, dtype=np.float32)

        if self.task == 'classification':
            return self._predict_classification(X, return_class_info)
        else:
            return self._predict_regression(X, return_class_info)

    def _predict_classification(
        self,
        X: npt.NDArray[np.floating[Any]],
        return_class_info: bool = False
    ) -> Union[List[Set[int]], tuple[List[Set[int]], npt.NDArray[Any]]]:
        """Generate prediction sets for classification."""
        # Get predicted probabilities
        proba = self.base_cp.predict_proba(X)
        n_samples = X.shape[0]

        # For classification, use predicted class as the conditioning variable
        predicted_classes = np.argmax(proba, axis=1)

        prediction_sets = []
        class_assignments = []

        for i in range(n_samples):
            # Get the predicted class for conditioning
            pred_class = predicted_classes[i]

            # Map to original class labels if needed
            if self.classes_ is not None and pred_class < len(self.classes_):
                conditioning_class = self.classes_[pred_class]
            else:
                conditioning_class = pred_class

            # Use global quantile if class not seen during calibration
            if conditioning_class not in self.class_quantiles:
                warnings.warn(f"Class {conditioning_class} not seen during calibration. "
                            "Using average quantile.", RuntimeWarning)
                threshold = np.mean(list(self.class_quantiles.values()))
            else:
                threshold = self.class_quantiles[conditioning_class]

            # Create prediction set
            # Include classes with probability >= 1 - threshold
            pred_set = set()
            for j, p in enumerate(proba[i]):
                if p >= 1 - threshold:
                    if self.classes_ is not None and j < len(self.classes_):
                        pred_set.add(self.classes_[j])
                    else:
                        pred_set.add(j)

            # Ensure non-empty prediction set
            if not pred_set:
                # Add the most likely class
                if self.classes_ is not None and pred_class < len(self.classes_):
                    pred_set.add(self.classes_[pred_class])
                else:
                    pred_set.add(pred_class)

            prediction_sets.append(pred_set)
            class_assignments.append(conditioning_class)

        if return_class_info:
            return prediction_sets, np.array(class_assignments)
        return prediction_sets

    def _predict_regression(
        self,
        X: npt.NDArray[np.floating[Any]],
        return_class_info: bool = False
    ) -> Union[tuple[npt.NDArray[Any], npt.NDArray[Any]],
               tuple[tuple[npt.NDArray[Any], npt.NDArray[Any]], npt.NDArray[Any]]]:
        """Generate prediction intervals for regression."""
        # Get point predictions
        y_pred = self.base_cp.predict(X).ravel()

        # Determine categories
        if self.strategy == 'custom':
            categories = self.category_fn(X)
        else:
            # Use predicted value quartiles for categorization
            if len(self.class_quantiles) > 0:
                # Use calibration quartiles
                quartile_values = sorted(self.class_quantiles.keys())
                categories = np.digitize(y_pred, quartile_values[:-1])
            else:
                # Fallback to uniform categorization
                categories = np.zeros(len(y_pred), dtype=int)

        lower_bounds = np.zeros(len(y_pred))
        upper_bounds = np.zeros(len(y_pred))

        for i, (pred, category) in enumerate(zip(y_pred, categories)):
            # Get category-specific quantile
            if category not in self.class_quantiles:
                warnings.warn(f"Category {category} not seen during calibration. "
                            "Using average quantile.", RuntimeWarning)
                radius = np.mean(list(self.class_quantiles.values()))
            else:
                radius = self.class_quantiles[category]

            lower_bounds[i] = pred - radius
            upper_bounds[i] = pred + radius

        if return_class_info:
            return (lower_bounds, upper_bounds), categories
        return lower_bounds, upper_bounds

    def get_class_quantiles(self) -> Dict[Any, float]:
        """Return per-class/category quantile thresholds.

        Returns:
            Dictionary mapping class/category labels to their quantile thresholds.

        Raises:
            RuntimeError: If predictor has not been calibrated.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated to access class quantiles.")
        return self.class_quantiles.copy()

    def evaluate_class_coverage(
        self,
        X_test: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_test: Union[npt.NDArray[Any], pd.Series]
    ) -> Dict[str, Any]:
        """Evaluate per-class coverage and efficiency metrics.

        Args:
            X_test: Test features of shape (n_samples, n_features).
            y_test: True test labels of shape (n_samples,).

        Returns:
            Dictionary containing:
                - 'overall_coverage': Overall empirical coverage
                - 'class_coverage': Per-class coverage rates
                - 'mean_set_size': Mean prediction set size (classification)
                - 'mean_interval_width': Mean interval width (regression)
                - 'class_metrics': Per-class detailed metrics
        """
        # Convert pandas to numpy
        if isinstance(X_test, pd.DataFrame):
            X_test = X_test.values
        if isinstance(y_test, pd.Series):
            y_test = y_test.values

        y_test = np.asarray(y_test)

        if self.task == 'classification':
            return self._evaluate_classification_coverage(X_test, y_test)
        else:
            return self._evaluate_regression_coverage(X_test, y_test)

    def _evaluate_classification_coverage(
        self,
        X_test: npt.NDArray[np.floating[Any]],
        y_test: npt.NDArray[Any]
    ) -> Dict[str, Any]:
        """Evaluate coverage for classification."""
        prediction_sets, class_assignments = self.predict(X_test, return_class_info=True)

        overall_covered = []
        class_coverage = {}
        class_set_sizes = {}

        unique_classes = np.unique(y_test)

        for class_label in unique_classes:
            class_mask = (y_test == class_label)
            class_covered = []
            class_sizes = []

            for i in np.where(class_mask)[0]:
                covered = y_test[i] in prediction_sets[i]
                class_covered.append(covered)
                class_sizes.append(len(prediction_sets[i]))
                overall_covered.append(covered)

            if class_covered:
                class_coverage[class_label] = np.mean(class_covered)
                class_set_sizes[class_label] = {
                    'mean': np.mean(class_sizes),
                    'median': np.median(class_sizes),
                    'std': np.std(class_sizes)
                }

        return {
            'overall_coverage': float(np.mean(overall_covered)),
            'class_coverage': class_coverage,
            'mean_set_size': float(np.mean([len(s) for s in prediction_sets])),
            'class_metrics': class_set_sizes
        }

    def _evaluate_regression_coverage(
        self,
        X_test: npt.NDArray[np.floating[Any]],
        y_test: npt.NDArray[Any]
    ) -> Dict[str, Any]:
        """Evaluate coverage for regression."""
        (lower, upper), categories = self.predict(X_test, return_class_info=True)
        y_test = y_test.ravel()

        covered = (y_test >= lower) & (y_test <= upper)
        widths = upper - lower

        # Compute per-category metrics
        category_coverage = {}
        category_widths = {}

        for category in np.unique(categories):
            cat_mask = (categories == category)
            if np.any(cat_mask):
                category_coverage[category] = float(np.mean(covered[cat_mask]))
                category_widths[category] = {
                    'mean': float(np.mean(widths[cat_mask])),
                    'median': float(np.median(widths[cat_mask])),
                    'std': float(np.std(widths[cat_mask]))
                }

        return {
            'overall_coverage': float(np.mean(covered)),
            'category_coverage': category_coverage,
            'mean_interval_width': float(np.mean(widths)),
            'category_metrics': category_widths
        }
