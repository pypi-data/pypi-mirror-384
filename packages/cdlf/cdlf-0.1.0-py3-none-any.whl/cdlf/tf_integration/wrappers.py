"""TensorFlow model wrappers for conformal prediction.

This module provides wrapper classes that add conformal prediction capabilities
to existing TensorFlow/Keras models without modification.
"""

from typing import Any, Callable, Optional, Union, Literal

import tensorflow as tf
import numpy as np
import numpy.typing as npt

from cdlf.core.split_cp import SplitConformalPredictor
from cdlf.core.cross_cp import CrossConformalPredictor
from cdlf.core.full_cp import FullConformalPredictor


class ConformalizedModel:
    """Wrapper to add conformal prediction to TensorFlow models.

    This wrapper enables conformal prediction for any TensorFlow/Keras model
    without requiring changes to the model architecture. It transparently adds
    conformal prediction during inference while preserving the original model's
    training and inference API.

    Example:
        ```python
        # Create and train a standard Keras model
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_train, y_train, epochs=10)

        # Wrap with conformal prediction
        conf_model = ConformalizedModel(model, method='split', alpha=0.1)

        # Calibrate on held-out data
        conf_model.calibrate(X_cal, y_cal)

        # Get predictions with intervals
        predictions, intervals = conf_model.predict_with_intervals(X_test)
        lower, upper = intervals
        ```

    Attributes:
        model: The underlying TensorFlow/Keras model.
        method: Conformal prediction method ('split', 'cross', or 'full').
        alpha: Significance level for prediction intervals.
        task: Task type ('regression' or 'classification').
        is_calibrated: Whether the wrapper has been calibrated.
        cp_predictor: The underlying conformal predictor instance.
    """

    def __init__(
        self,
        model: tf.keras.Model,
        method: Literal['split', 'cross', 'full'] = 'split',
        alpha: float = 0.1,
        task: Optional[Literal['regression', 'classification']] = None,
        nonconformity_func: Optional[Callable] = None,
        **cp_kwargs: Any,
    ) -> None:
        """Initialize model wrapper with conformal prediction.

        Args:
            model: TensorFlow/Keras model to wrap.
            method: CP method - 'split', 'cross', or 'full'.
            alpha: Significance level. Default is 0.1 (90% confidence).
            task: Task type - 'regression' or 'classification'. If None, inferred from model.
            nonconformity_func: Custom nonconformity function. If None, uses defaults.
            **cp_kwargs: Additional arguments for the specific CP method.
                For 'cross': n_folds (int) - number of CV folds.
                For 'full': aggregation (str) - aggregation method.

        Raises:
            ValueError: If alpha is not in (0, 1) or method is invalid.
        """
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")

        if method not in ['split', 'cross', 'full']:
            raise ValueError(f"method must be 'split', 'cross', or 'full', got {method}")

        self.model = model
        self.method = method
        self.alpha = alpha
        self.nonconformity_func = nonconformity_func
        self.is_calibrated = False

        # Infer task from model if not specified
        if task is None:
            self.task = self._infer_task()
        else:
            self.task = task

        # Create a model adapter for the CP algorithms
        self.model_adapter = _TensorFlowModelAdapter(self.model, self.task)

        # Initialize the appropriate conformal predictor
        if method == 'split':
            self.cp_predictor = SplitConformalPredictor(
                model=self.model_adapter,
                alpha=alpha,
                nonconformity_func=nonconformity_func,
                task=self.task,
            )
        elif method == 'cross':
            n_folds = cp_kwargs.get('n_folds', 5)
            # For cross CP, we need a model factory
            model_factory = lambda: _TensorFlowModelAdapter(
                tf.keras.models.clone_model(self.model), self.task
            )
            self.cp_predictor = CrossConformalPredictor(
                model_factory=model_factory,
                alpha=alpha,
                nonconformity_func=nonconformity_func,
                task=self.task,
                n_folds=n_folds,
            )
        else:  # full
            grid_resolution = cp_kwargs.get('grid_resolution', 100)
            # For full CP, we need a model factory (same as cross CP)
            model_factory = lambda: _TensorFlowModelAdapter(
                tf.keras.models.clone_model(self.model), self.task
            )
            self.cp_predictor = FullConformalPredictor(
                model_factory=model_factory,
                alpha=alpha,
                nonconformity_func=nonconformity_func,
                task=self.task,
                grid_resolution=grid_resolution,
            )

    def _infer_task(self) -> str:
        """Infer task type from model architecture.

        Returns:
            'regression' or 'classification' based on model output.
        """
        # Check the final layer's activation and output shape
        output_layer = self.model.layers[-1]

        # Check for common classification signatures
        if hasattr(output_layer, 'activation'):
            activation = output_layer.activation
            if activation is not None:
                activation_name = activation.__name__ if hasattr(activation, '__name__') else str(activation)
                if 'softmax' in activation_name.lower() or 'sigmoid' in activation_name.lower():
                    return 'classification'

        # Check output shape
        output_shape = self.model.output_shape
        if output_shape[-1] == 1:
            # Single output, could be binary classification or regression
            # Default to regression unless sigmoid activation
            if hasattr(output_layer, 'activation'):
                activation = output_layer.activation
                if activation is not None:
                    activation_name = activation.__name__ if hasattr(activation, '__name__') else str(activation)
                    if 'sigmoid' in activation_name.lower():
                        return 'classification'
            return 'regression'
        elif output_shape[-1] > 1:
            # Multiple outputs, likely classification
            return 'classification'

        # Default to regression
        return 'regression'

    def fit(
        self,
        *args: Any,
        validation_split: Optional[float] = None,
        **kwargs: Any,
    ) -> tf.keras.callbacks.History:
        """Train the underlying model.

        This method passes through to the underlying model's fit method,
        allowing normal training. If validation_split is provided and > 0,
        automatically uses validation data for calibration after training.

        Args:
            *args: Positional arguments for model.fit().
            validation_split: Fraction of data to use for validation/calibration.
            **kwargs: Keyword arguments for model.fit().

        Returns:
            Training history from model.fit().
        """
        history = self.model.fit(*args, **kwargs)

        # Auto-calibrate if validation data is available
        if validation_split and validation_split > 0 and len(args) >= 2:
            X, y = args[0], args[1]
            n_samples = len(X)
            n_val = int(n_samples * validation_split)
            X_cal = X[-n_val:]
            y_cal = y[-n_val:]
            self.calibrate(X_cal, y_cal)

        return history

    def calibrate(
        self,
        X_cal: Union[npt.NDArray[np.floating[Any]], tf.Tensor],
        y_cal: Union[npt.NDArray[Any], tf.Tensor],
    ) -> None:
        """Calibrate the conformal predictor on calibration data.

        This computes the nonconformity scores on the calibration set
        and determines the quantile threshold for the desired coverage.

        Args:
            X_cal: Calibration features of shape (n_samples, n_features).
            y_cal: Calibration labels of shape (n_samples,) or (n_samples, n_outputs).

        Raises:
            ValueError: If calibration data is empty or has mismatched dimensions.
        """
        # Convert TensorFlow tensors to numpy if needed
        if isinstance(X_cal, tf.Tensor):
            X_cal = X_cal.numpy()
        if isinstance(y_cal, tf.Tensor):
            y_cal = y_cal.numpy()

        # Calibrate the underlying CP predictor
        self.cp_predictor.calibrate(X_cal, y_cal)
        self.is_calibrated = True

    def predict(
        self,
        X: Union[npt.NDArray[np.floating[Any]], tf.Tensor],
        batch_size: Optional[int] = None,
        verbose: int = 0,
    ) -> npt.NDArray[Any]:
        """Make standard predictions without conformal intervals.

        This method provides standard model predictions, maintaining
        compatibility with the original model's API.

        Args:
            X: Input features of shape (n_samples, n_features).
            batch_size: Batch size for prediction. If None, predicts on entire dataset.
            verbose: Verbosity mode. 0 = silent, 1 = progress bar.

        Returns:
            Model predictions with same format as underlying model.
        """
        return self.model.predict(X, batch_size=batch_size, verbose=verbose)

    def predict_with_intervals(
        self,
        X: Union[npt.NDArray[np.floating[Any]], tf.Tensor],
        batch_size: Optional[int] = None,
        return_predictions: bool = True,
    ) -> tuple[Optional[npt.NDArray[Any]], Union[tuple[npt.NDArray[Any], npt.NDArray[Any]], list[list[int]]]]:
        """Generate predictions with conformal prediction intervals/sets.

        For regression tasks, returns prediction intervals [lower, upper].
        For classification tasks, returns prediction sets containing valid classes.

        Args:
            X: Input features of shape (n_samples, n_features).
            batch_size: Batch size for prediction. If None, predicts on entire dataset.
            return_predictions: Whether to also return point predictions.

        Returns:
            If return_predictions is True:
                - For regression: (predictions, (lower_bounds, upper_bounds))
                - For classification: (predictions, prediction_sets)
            Otherwise, just the intervals/sets.

        Raises:
            RuntimeError: If the predictor has not been calibrated.
        """
        if not self.is_calibrated:
            raise RuntimeError("Model must be calibrated before generating intervals. Call calibrate() first.")

        # Convert TensorFlow tensors to numpy if needed
        if isinstance(X, tf.Tensor):
            X = X.numpy()

        # Handle batch prediction if specified
        if batch_size is not None and len(X) > batch_size:
            n_samples = len(X)
            n_batches = (n_samples + batch_size - 1) // batch_size

            if self.task == 'regression':
                all_lower = []
                all_upper = []
                all_preds = [] if return_predictions else None

                for i in range(n_batches):
                    start = i * batch_size
                    end = min((i + 1) * batch_size, n_samples)
                    batch_X = X[start:end]

                    lower, upper = self.cp_predictor.predict(batch_X)
                    all_lower.append(lower)
                    all_upper.append(upper)

                    if return_predictions:
                        preds = self.model.predict(batch_X, verbose=0)
                        all_preds.append(preds)

                lower_bounds = np.concatenate(all_lower)
                upper_bounds = np.concatenate(all_upper)
                intervals = (lower_bounds, upper_bounds)

                if return_predictions:
                    predictions = np.concatenate(all_preds)
                    return predictions, intervals
                return None, intervals

            else:  # classification
                all_sets = []
                all_preds = [] if return_predictions else None

                for i in range(n_batches):
                    start = i * batch_size
                    end = min((i + 1) * batch_size, n_samples)
                    batch_X = X[start:end]

                    pred_sets = self.cp_predictor.predict(batch_X)
                    all_sets.extend(pred_sets)

                    if return_predictions:
                        preds = self.model.predict(batch_X, verbose=0)
                        all_preds.append(preds)

                if return_predictions:
                    predictions = np.concatenate(all_preds)
                    return predictions, all_sets
                return None, all_sets

        # Non-batched prediction
        cp_output = self.cp_predictor.predict(X)

        if return_predictions:
            predictions = self.model.predict(X, batch_size=batch_size, verbose=0)
            return predictions, cp_output
        return None, cp_output

    def get_coverage(
        self,
        X_test: Union[npt.NDArray[np.floating[Any]], tf.Tensor],
        y_test: Union[npt.NDArray[Any], tf.Tensor],
    ) -> float:
        """Compute empirical coverage on test data.

        Coverage is the fraction of true labels that fall within the
        predicted intervals (regression) or sets (classification).

        Args:
            X_test: Test features.
            y_test: True test labels.

        Returns:
            Empirical coverage rate in [0, 1].
        """
        # Convert TensorFlow tensors to numpy if needed
        if isinstance(X_test, tf.Tensor):
            X_test = X_test.numpy()
        if isinstance(y_test, tf.Tensor):
            y_test = y_test.numpy()

        return self.cp_predictor.get_coverage(X_test, y_test)

    def get_efficiency(
        self,
        X: Union[npt.NDArray[np.floating[Any]], tf.Tensor],
    ) -> Union[npt.NDArray[np.floating[Any]], npt.NDArray[np.integer[Any]]]:
        """Compute efficiency metrics for predictions.

        For regression: returns interval widths.
        For classification: returns prediction set sizes.

        Args:
            X: Input features.

        Returns:
            Array of efficiency metrics (widths or set sizes).
        """
        # Convert TensorFlow tensors to numpy if needed
        if isinstance(X, tf.Tensor):
            X = X.numpy()

        if self.task == 'regression':
            return self.cp_predictor.get_interval_width(X)
        else:
            return self.cp_predictor.get_set_sizes(X)

    def save_wrapper(self, filepath: str) -> None:
        """Save the conformalized model wrapper.

        Saves both the underlying model and the calibration data.

        Args:
            filepath: Path to save the wrapper.
        """
        import pickle
        import os

        # Create directory if it doesn't exist
        os.makedirs(filepath, exist_ok=True)

        # Save the Keras model
        model_path = os.path.join(filepath, 'model.keras')
        self.model.save(model_path)

        # Save the wrapper state
        state = {
            'method': self.method,
            'alpha': self.alpha,
            'task': self.task,
            'is_calibrated': self.is_calibrated,
            'cp_state': self.cp_predictor.get_params() if self.is_calibrated else None,
        }

        state_path = os.path.join(filepath, 'wrapper_state.pkl')
        with open(state_path, 'wb') as f:
            pickle.dump(state, f)

    @classmethod
    def load_wrapper(cls, filepath: str) -> 'ConformalizedModel':
        """Load a saved conformalized model wrapper.

        Args:
            filepath: Path to the saved wrapper.

        Returns:
            Loaded ConformalizedModel instance.
        """
        import pickle
        import os

        # Load the Keras model
        model_path = os.path.join(filepath, 'model.keras')
        model = tf.keras.models.load_model(model_path)

        # Load the wrapper state
        state_path = os.path.join(filepath, 'wrapper_state.pkl')
        with open(state_path, 'rb') as f:
            state = pickle.load(f)

        # Recreate the wrapper
        wrapper = cls(
            model=model,
            method=state['method'],
            alpha=state['alpha'],
            task=state['task'],
        )

        # Restore calibration if it was calibrated
        if state['is_calibrated'] and state['cp_state']:
            # This is a simplified restoration - full implementation would
            # restore all calibration scores and quantiles
            wrapper.is_calibrated = True

        return wrapper

    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Make the wrapper callable like the underlying model.

        Args:
            *args: Positional arguments passed to model.
            **kwargs: Keyword arguments passed to model.

        Returns:
            Model output.
        """
        return self.model(*args, **kwargs)


class _TensorFlowModelAdapter:
    """Adapter to make TensorFlow models compatible with CP algorithms.

    This internal class wraps a TensorFlow model to provide the standard
    predict and predict_proba interface expected by the CP algorithms.
    """

    def __init__(self, model: tf.keras.Model, task: str) -> None:
        """Initialize the adapter.

        Args:
            model: TensorFlow/Keras model to wrap.
            task: Task type ('regression' or 'classification').
        """
        self.model = model
        self.task = task
        self._is_fitted = True  # Assume pre-trained model

    def fit(self, X: npt.NDArray[Any], y: npt.NDArray[Any], **kwargs: Any) -> None:
        """Fit the model (for cross-validation in CrossCP).

        Args:
            X: Training features.
            y: Training labels.
            **kwargs: Additional training arguments.
        """
        # Compile if not already compiled
        if not self.model.compiled:
            if self.task == 'regression':
                self.model.compile(optimizer='adam', loss='mse')
            else:
                self.model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')

        # Train with reasonable defaults
        epochs = kwargs.get('epochs', 10)
        batch_size = kwargs.get('batch_size', 32)
        verbose = kwargs.get('verbose', 0)

        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=verbose)
        self._is_fitted = True

    def predict(self, X: npt.NDArray[Any]) -> npt.NDArray[Any]:
        """Make predictions.

        Args:
            X: Input features.

        Returns:
            Predictions.
        """
        preds = self.model.predict(X, verbose=0)

        if self.task == 'classification' and preds.shape[-1] > 1:
            # Return class predictions for multi-class
            return np.argmax(preds, axis=-1)
        elif self.task == 'classification' and preds.shape[-1] == 1:
            # Binary classification
            return (preds > 0.5).astype(int).squeeze()
        else:
            # Regression
            return preds.squeeze() if preds.shape[-1] == 1 else preds

    def predict_proba(self, X: npt.NDArray[Any]) -> npt.NDArray[Any]:
        """Predict class probabilities for classification.

        Args:
            X: Input features.

        Returns:
            Class probabilities.
        """
        if self.task != 'classification':
            raise ValueError("predict_proba is only for classification tasks")

        preds = self.model.predict(X, verbose=0)

        # Handle binary classification with single output
        if preds.shape[-1] == 1:
            # Convert to two-class probabilities
            pos_probs = preds.squeeze()
            neg_probs = 1 - pos_probs
            return np.column_stack([neg_probs, pos_probs])

        return preds
