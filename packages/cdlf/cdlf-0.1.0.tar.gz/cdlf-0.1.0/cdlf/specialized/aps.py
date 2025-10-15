"""Adaptive Prediction Sets (APS) and Regularized APS (RAPS) implementation.

This module implements APS and RAPS for classification tasks, providing prediction sets
with guaranteed coverage and optimal average size.

Reference: Romano et al. (2020) - "Classification with Valid and Adaptive Coverage"
https://arxiv.org/abs/2006.02544

Mathematical Formulation (APS):
1. For each calibration sample, sort classes by predicted probability (descending)
2. Compute nonconformity score: S(x, y) = Σ_{j=1}^k p_{(j)} where k is smallest
   index such that y is in top k classes by probability
3. Find threshold τ such that P(S(X, Y) <= τ) >= 1 - α
4. For prediction: include classes until cumulative probability exceeds τ

Mathematical Formulation (RAPS):
Extends APS with regularization to reduce set size variance:
- S_reg(x, y) = S(x, y) + λ * (k - k_reg)+ where k_reg is a target set size
- This penalizes sets larger than k_reg, encouraging more consistent set sizes

The key innovation is that APS/RAPS produces the smallest average prediction sets
while maintaining the coverage guarantee, by adaptively including classes based
on their predicted probabilities rather than using fixed thresholds.
"""

from typing import Any, Optional, Union, List, Set, Tuple, Dict
import warnings

import numpy as np
import numpy.typing as npt
import pandas as pd

from cdlf.core.base import BaseConformalPredictor


class AdaptivePredictionSets(BaseConformalPredictor):
    """Adaptive Prediction Sets for classification with optimal efficiency.

    APS provides prediction sets for classification that have guaranteed
    coverage while minimizing the average set size through adaptive thresholds.
    Supports both standard APS and Regularized APS (RAPS) variants.

    Attributes:
        alpha: Significance level (1 - confidence level).
        regularization: RAPS regularization parameter λ (0 for standard APS).
        randomize: Whether to use randomized tie-breaking for equal probabilities.
        threshold: Calibrated threshold τ for prediction set inclusion.
        nonconformity_scores: Stored nonconformity scores from calibration.
        k_reg: Target set size for RAPS regularization.
        temperature: Temperature parameter for softmax calibration.

    Example:
        >>> import numpy as np
        >>> from sklearn.neural_network import MLPClassifier
        >>> from cdlf.specialized.aps import AdaptivePredictionSets
        >>>
        >>> # Train a classifier
        >>> model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=500)
        >>> X_train = np.random.randn(1000, 20)
        >>> y_train = np.random.randint(0, 10, 1000)  # 10 classes
        >>> model.fit(X_train, y_train)
        >>>
        >>> # Initialize APS
        >>> aps = AdaptivePredictionSets(alpha=0.1)
        >>>
        >>> # Calibrate
        >>> X_cal = np.random.randn(500, 20)
        >>> y_cal = np.random.randint(0, 10, 500)
        >>> probabilities_cal = model.predict_proba(X_cal)
        >>> aps.calibrate(probabilities_cal, y_cal)
        >>>
        >>> # Generate prediction sets
        >>> X_test = np.random.randn(100, 20)
        >>> probabilities_test = model.predict_proba(X_test)
        >>> prediction_sets = aps.predict(probabilities_test)
        >>>
        >>> # Use RAPS for more consistent set sizes
        >>> raps = AdaptivePredictionSets(alpha=0.1, regularization=0.1)
        >>> raps.calibrate(probabilities_cal, y_cal)
        >>> prediction_sets_raps = raps.predict(probabilities_test)
    """

    def __init__(
        self,
        alpha: float = 0.1,
        regularization: float = 0.0,
        randomize: bool = True,
        k_reg: Optional[int] = None,
        temperature: float = 1.0
    ) -> None:
        """Initialize APS/RAPS predictor.

        Args:
            alpha: Significance level. Default is 0.1 (90% confidence).
            regularization: RAPS regularization parameter λ. Default is 0 (standard APS).
                Positive values encourage more consistent set sizes.
            randomize: Whether to use randomized tie-breaking for equal probabilities.
                Helps with discrete distributions. Default is True.
            k_reg: Target set size for RAPS. If None, uses median set size from calibration.
            temperature: Temperature for softmax calibration. Values > 1 make probabilities
                more uniform, < 1 make them more peaked. Default is 1.0 (no scaling).

        Raises:
            ValueError: If alpha is not in (0, 1) or regularization < 0.
        """
        super().__init__(alpha=alpha)

        if regularization < 0:
            raise ValueError(f"regularization must be non-negative, got {regularization}")

        self.regularization = regularization
        self.randomize = randomize
        self.k_reg = k_reg
        self.temperature = temperature

        self.threshold: Optional[float] = None
        self.nonconformity_scores: Optional[npt.NDArray[np.floating[Any]]] = None
        self._calibration_set_sizes: Optional[npt.NDArray[np.integer[Any]]] = None

    def calibrate(
        self,
        probabilities_cal: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_cal: Union[npt.NDArray[np.integer[Any]], pd.Series],
    ) -> None:
        """Calibrate APS/RAPS on calibration data.

        Computes nonconformity scores for each calibration sample and finds
        the appropriate threshold τ for the desired coverage level.

        Args:
            probabilities_cal: Predicted class probabilities of shape (n_samples, n_classes).
            y_cal: True class labels of shape (n_samples,) with integer class labels.

        Raises:
            ValueError: If inputs have incompatible shapes or invalid values.
        """
        # Convert pandas to numpy
        if isinstance(probabilities_cal, pd.DataFrame):
            probabilities_cal = probabilities_cal.values
        if isinstance(y_cal, pd.Series):
            y_cal = y_cal.values

        probabilities_cal = np.asarray(probabilities_cal, dtype=np.float32)
        y_cal = np.asarray(y_cal, dtype=np.int32).ravel()

        n_cal = probabilities_cal.shape[0]
        n_classes = probabilities_cal.shape[1]

        if n_cal != len(y_cal):
            raise ValueError(f"probabilities_cal and y_cal must have same number of samples, "
                           f"got {n_cal} and {len(y_cal)}")

        if np.any((y_cal < 0) | (y_cal >= n_classes)):
            raise ValueError(f"y_cal contains invalid class labels. "
                           f"Expected labels in [0, {n_classes-1}]")

        # Apply temperature scaling if needed
        if self.temperature != 1.0:
            probabilities_cal = self._apply_temperature_scaling(probabilities_cal)

        # Compute nonconformity scores
        scores = []
        set_sizes = []

        for i in range(n_cal):
            score, set_size = self._compute_nonconformity_score(
                probabilities_cal[i], y_cal[i]
            )
            scores.append(score)
            set_sizes.append(set_size)

        self.nonconformity_scores = np.array(scores)
        self._calibration_set_sizes = np.array(set_sizes)

        # Set k_reg for RAPS if not provided
        if self.regularization > 0 and self.k_reg is None:
            self.k_reg = int(np.median(self._calibration_set_sizes))

        # Compute threshold
        n = len(self.nonconformity_scores)
        level = np.ceil((1 - self.alpha) * (n + 1)) / n
        level = min(level, 1.0)

        self.threshold = np.quantile(self.nonconformity_scores, level)
        self.is_calibrated = True

    def _apply_temperature_scaling(
        self,
        probabilities: npt.NDArray[np.floating[Any]]
    ) -> npt.NDArray[np.floating[Any]]:
        """Apply temperature scaling to probabilities."""
        # Apply temperature to logits
        eps = 1e-10
        logits = np.log(probabilities + eps)
        scaled_logits = logits / self.temperature

        # Convert back to probabilities
        exp_logits = np.exp(scaled_logits - np.max(scaled_logits, axis=1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def _compute_nonconformity_score(
        self,
        probs: npt.NDArray[np.floating[Any]],
        true_label: int
    ) -> Tuple[float, int]:
        """Compute nonconformity score for a single sample.

        Args:
            probs: Class probabilities of shape (n_classes,).
            true_label: True class label.

        Returns:
            Tuple of (nonconformity_score, set_size).
        """
        n_classes = len(probs)

        # Add randomization if enabled
        if self.randomize:
            u = np.random.uniform(size=n_classes)
            probs_randomized = probs + u * 1e-6  # Small random tie-breaking
        else:
            probs_randomized = probs

        # Sort probabilities in descending order
        sorted_indices = np.argsort(-probs_randomized)
        sorted_probs = probs[sorted_indices]

        # Find position of true class
        true_class_position = np.where(sorted_indices == true_label)[0][0]

        # Compute cumulative sum up to and including true class
        cumsum = np.cumsum(sorted_probs)
        score = cumsum[true_class_position]

        # Add random component for tie-breaking if enabled
        if self.randomize:
            u_true = np.random.uniform()
            score = score + u_true * (sorted_probs[true_class_position]
                                     if true_class_position < n_classes - 1
                                     else 0)

        # Apply RAPS regularization if enabled
        set_size = true_class_position + 1
        if self.regularization > 0 and self.k_reg is not None:
            penalty = self.regularization * max(0, set_size - self.k_reg)
            score += penalty

        return score, set_size

    def predict(
        self,
        probabilities: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        return_set_sizes: bool = False
    ) -> Union[List[Set[int]], Tuple[List[Set[int]], npt.NDArray[np.integer[Any]]]]:
        """Generate adaptive prediction sets for classification.

        Args:
            probabilities: Predicted class probabilities of shape (n_samples, n_classes).
            return_set_sizes: If True, also return the size of each prediction set.

        Returns:
            If return_set_sizes=False:
                List of prediction sets, where each set contains the predicted class labels.
            If return_set_sizes=True:
                Tuple of (prediction_sets, set_sizes).

        Raises:
            RuntimeError: If predictor has not been calibrated.
        """
        if not self.is_calibrated:
            raise RuntimeError("Predictor must be calibrated before prediction. "
                             "Call calibrate() first.")

        # Convert pandas to numpy
        if isinstance(probabilities, pd.DataFrame):
            probabilities = probabilities.values

        probabilities = np.asarray(probabilities, dtype=np.float32)
        n_samples, n_classes = probabilities.shape

        # Apply temperature scaling if needed
        if self.temperature != 1.0:
            probabilities = self._apply_temperature_scaling(probabilities)

        prediction_sets = []
        set_sizes = []

        for i in range(n_samples):
            pred_set = self._create_prediction_set(probabilities[i])
            prediction_sets.append(pred_set)
            set_sizes.append(len(pred_set))

        if return_set_sizes:
            return prediction_sets, np.array(set_sizes)
        return prediction_sets

    def _create_prediction_set(
        self,
        probs: npt.NDArray[np.floating[Any]]
    ) -> Set[int]:
        """Create prediction set for a single sample."""
        n_classes = len(probs)

        # Add randomization if enabled
        if self.randomize:
            u = np.random.uniform(size=n_classes)
            probs_randomized = probs + u * 1e-6
        else:
            probs_randomized = probs

        # Sort probabilities in descending order
        sorted_indices = np.argsort(-probs_randomized)
        sorted_probs = probs[sorted_indices]

        # Build prediction set by including classes until threshold is exceeded
        cumsum = 0.0
        pred_set = set()

        for k, (class_idx, prob) in enumerate(zip(sorted_indices, sorted_probs)):
            cumsum += prob

            # Add RAPS regularization if enabled
            if self.regularization > 0 and self.k_reg is not None:
                penalty = self.regularization * max(0, (k + 1) - self.k_reg)
                adjusted_score = cumsum + penalty
            else:
                adjusted_score = cumsum

            # Check if we should include this class
            if adjusted_score <= self.threshold:
                pred_set.add(int(class_idx))
            else:
                # For standard APS, always include at least the top class
                if not pred_set:
                    pred_set.add(int(sorted_indices[0]))
                break

        # Ensure non-empty set
        if not pred_set:
            pred_set.add(int(sorted_indices[0]))

        return pred_set

    def _sort_and_cumsum(
        self,
        probs: npt.NDArray[np.floating[Any]]
    ) -> Tuple[npt.NDArray[np.integer[Any]], npt.NDArray[np.floating[Any]]]:
        """Sort probabilities and compute cumulative sum.

        Core APS logic for sorting classes by probability and computing
        cumulative sums for threshold-based inclusion.

        Args:
            probs: Class probabilities of shape (n_classes,).

        Returns:
            Tuple of (sorted_indices, cumulative_probabilities).
        """
        sorted_indices = np.argsort(-probs)
        sorted_probs = probs[sorted_indices]
        cumsum_probs = np.cumsum(sorted_probs)
        return sorted_indices, cumsum_probs

    def predict_with_scores(
        self,
        probabilities: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
    ) -> Tuple[List[Set[int]], npt.NDArray[np.floating[Any]]]:
        """Generate prediction sets along with conformity scores.

        Args:
            probabilities: Predicted class probabilities of shape (n_samples, n_classes).

        Returns:
            Tuple of (prediction_sets, conformity_scores).

        Raises:
            RuntimeError: If predictor has not been calibrated.
        """
        prediction_sets = self.predict(probabilities)

        # Compute conformity scores for each prediction
        if isinstance(probabilities, pd.DataFrame):
            probabilities = probabilities.values

        probabilities = np.asarray(probabilities, dtype=np.float32)
        n_samples = probabilities.shape[0]

        conformity_scores = np.zeros(n_samples)
        for i in range(n_samples):
            # Conformity score is 1 - (sum of probabilities in prediction set)
            set_probs = probabilities[i, list(prediction_sets[i])]
            conformity_scores[i] = 1.0 - np.sum(set_probs)

        return prediction_sets, conformity_scores

    def evaluate_efficiency(
        self,
        probabilities_test: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_test: Union[npt.NDArray[np.integer[Any]], pd.Series]
    ) -> Dict[str, Any]:
        """Evaluate coverage and efficiency metrics on test data.

        Args:
            probabilities_test: Test probabilities of shape (n_samples, n_classes).
            y_test: True test labels of shape (n_samples,).

        Returns:
            Dictionary containing:
                - 'coverage': Empirical coverage rate
                - 'mean_set_size': Mean prediction set size
                - 'median_set_size': Median prediction set size
                - 'set_size_std': Standard deviation of set sizes
                - 'singleton_rate': Fraction of sets with only one class
                - 'empty_rate': Fraction of empty sets (should be 0)
                - 'size_histogram': Distribution of set sizes
        """
        # Convert pandas to numpy
        if isinstance(y_test, pd.Series):
            y_test = y_test.values
        y_test = np.asarray(y_test, dtype=np.int32).ravel()

        prediction_sets, set_sizes = self.predict(probabilities_test, return_set_sizes=True)

        # Check coverage
        covered = []
        for i, (pred_set, true_label) in enumerate(zip(prediction_sets, y_test)):
            covered.append(true_label in pred_set)

        coverage = np.mean(covered)

        # Compute size statistics
        singleton_rate = np.mean(set_sizes == 1)
        empty_rate = np.mean(set_sizes == 0)

        # Create size histogram
        max_size = min(10, np.max(set_sizes))  # Cap at 10 for display
        size_counts = np.bincount(set_sizes, minlength=max_size + 1)[:max_size + 1]
        size_histogram = {int(size): int(count) for size, count in enumerate(size_counts)}

        return {
            'coverage': float(coverage),
            'mean_set_size': float(np.mean(set_sizes)),
            'median_set_size': float(np.median(set_sizes)),
            'set_size_std': float(np.std(set_sizes)),
            'singleton_rate': float(singleton_rate),
            'empty_rate': float(empty_rate),
            'size_histogram': size_histogram
        }

    def plot_set_sizes(
        self,
        probabilities_test: Union[npt.NDArray[np.floating[Any]], pd.DataFrame],
        y_test: Optional[Union[npt.NDArray[np.integer[Any]], pd.Series]] = None
    ) -> None:
        """Visualize prediction set size distribution.

        Args:
            probabilities_test: Test probabilities.
            y_test: True test labels (optional, for coverage analysis).
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            warnings.warn("matplotlib not installed. Cannot create plots.")
            return

        _, set_sizes = self.predict(probabilities_test, return_set_sizes=True)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Histogram of set sizes
        axes[0].hist(set_sizes, bins=np.arange(0, np.max(set_sizes) + 2) - 0.5,
                    edgecolor='black', alpha=0.7)
        axes[0].set_xlabel('Prediction Set Size')
        axes[0].set_ylabel('Count')
        axes[0].set_title(f'Distribution of Set Sizes (α={self.alpha})')
        axes[0].grid(True, alpha=0.3)

        # Add mean and median lines
        mean_size = np.mean(set_sizes)
        median_size = np.median(set_sizes)
        axes[0].axvline(mean_size, color='red', linestyle='--',
                       label=f'Mean: {mean_size:.2f}')
        axes[0].axvline(median_size, color='green', linestyle='--',
                       label=f'Median: {median_size:.2f}')
        axes[0].legend()

        # Set sizes over samples
        axes[1].plot(set_sizes, alpha=0.6)
        axes[1].set_xlabel('Sample Index')
        axes[1].set_ylabel('Prediction Set Size')
        axes[1].set_title('Set Sizes Across Test Samples')
        axes[1].grid(True, alpha=0.3)

        if self.regularization > 0 and self.k_reg is not None:
            axes[1].axhline(self.k_reg, color='red', linestyle='--',
                          label=f'Target Size (k_reg={self.k_reg})')
            axes[1].legend()

        plt.suptitle(f'{"RAPS" if self.regularization > 0 else "APS"} Analysis '
                    f'(λ={self.regularization})')
        plt.tight_layout()
        plt.show()
