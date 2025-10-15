"""Custom TensorFlow/Keras layers for conformal prediction.

This module provides custom layers that can be integrated into TensorFlow models
to enable conformal prediction directly in the model architecture.
"""

from typing import Any, Optional, Union, Literal

import tensorflow as tf
import numpy as np
import numpy.typing as npt


class ConformalLayer(tf.keras.layers.Layer):
    """Keras layer for conformal prediction intervals.

    This layer can be added to a Keras model to output prediction intervals
    alongside point predictions. It must be calibrated with calibration data
    before being used for prediction.

    Example:
        ```python
        # Create a model with a conformal output layer
        inputs = tf.keras.Input(shape=(10,))
        x = tf.keras.layers.Dense(64, activation='relu')(inputs)
        x = tf.keras.layers.Dense(32, activation='relu')(x)
        prediction = tf.keras.layers.Dense(1, name='prediction')(x)

        # Add conformal layer
        conf_layer = ConformalLayer(alpha=0.1, name='conformal')
        conf_output = conf_layer(prediction)

        model = tf.keras.Model(inputs=inputs, outputs=conf_output)

        # After training, calibrate the conformal layer
        conf_layer.calibrate(X_cal, y_cal, model)

        # Now predictions will include intervals
        output = model.predict(X_test)
        # output has 'prediction', 'lower_bound', 'upper_bound'
        ```

    Attributes:
        alpha: Significance level for prediction intervals.
        quantile: Calibrated quantile for interval width.
        task: Task type ('regression' or 'classification').
        calibration_scores: Stored nonconformity scores from calibration.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        task: str = 'regression',
        **kwargs: Any,
    ) -> None:
        """Initialize conformal layer.

        Args:
            alpha: Significance level. Default is 0.1 (90% confidence).
            task: Task type - 'regression' or 'classification'.
            **kwargs: Additional keyword arguments for the Keras layer.
        """
        super().__init__(**kwargs)
        self.alpha = alpha
        self.task = task
        self.quantile = tf.Variable(
            0.0,  # Start uncalibrated
            trainable=False,
            dtype=tf.float32,
            name="quantile",
        )
        self.is_calibrated = tf.Variable(
            False,
            trainable=False,
            dtype=tf.bool,
            name="is_calibrated",
        )
        self.calibration_scores = None

    def build(self, input_shape: tf.TensorShape) -> None:
        """Build the layer.

        Args:
            input_shape: Shape of input tensors.
        """
        super().build(input_shape)

    def call(
        self,
        inputs: tf.Tensor,
        training: Optional[bool] = None,
    ) -> dict[str, tf.Tensor]:
        """Forward pass computing prediction intervals.

        Args:
            inputs: Input tensor of shape (batch_size, ...).
            training: Whether in training mode.

        Returns:
            Dictionary with keys 'prediction', 'lower_bound', 'upper_bound', 'interval_width'.
            During training, bounds equal prediction (intervals are zero).
            During inference after calibration, bounds are computed using the calibrated quantile.
        """
        # Always return dict for TF 2.16+ Functional API compatibility
        # TensorFlow models require consistent output structure across training/inference

        if self.task == 'regression':
            # Compute bounds - during training or when not calibrated, bounds equal prediction
            # During inference with calibration, use quantile
            # Use tf.cond for graph-mode compatibility
            def compute_calibrated_bounds():
                return inputs - self.quantile, inputs + self.quantile

            def compute_uncalibrated_bounds():
                return inputs, inputs

            # Check if we should use calibrated bounds
            # training is a Python bool or None, quantile comparison needs TF ops
            use_quantile = tf.logical_and(
                tf.logical_not(training if training is not None else False),
                tf.greater(self.quantile, 0.0)
            )

            lower_bound, upper_bound = tf.cond(
                use_quantile,
                compute_calibrated_bounds,
                compute_uncalibrated_bounds
            )

            return {
                'prediction': inputs,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'interval_width': upper_bound - lower_bound,
            }
        else:
            # Classification
            return {
                'prediction': inputs,
                'conformal_enabled': tf.greater(self.quantile, 0.0),
                'quantile': self.quantile,
            }

    def calibrate(
        self,
        X_cal: npt.NDArray[np.floating[Any]],
        y_cal: npt.NDArray[Any],
        model: Optional[tf.keras.Model] = None,
    ) -> None:
        """Calibrate the conformal layer.

        Args:
            X_cal: Calibration features.
            y_cal: Calibration labels.
            model: The model containing this layer (for getting predictions).
        """
        if model is None:
            raise ValueError("Model must be provided for calibration")

        # Get predictions on calibration set
        y_pred = model.predict(X_cal, verbose=0)

        # Extract prediction values if output is a dict
        if isinstance(y_pred, dict):
            y_pred = y_pred['prediction']

        # Compute nonconformity scores
        if self.task == 'regression':
            scores = np.abs(y_cal - y_pred.squeeze())
        else:
            # For classification, need probability scores
            # This is a simplified version
            scores = 1.0 - np.max(y_pred, axis=-1)

        # Compute quantile
        n_cal = len(scores)
        q_level = np.ceil((n_cal + 1) * (1 - self.alpha)) / n_cal
        if q_level > 1:
            q_level = 1.0

        quantile_value = np.quantile(scores, q_level, method='higher')

        # Update layer variables
        self.quantile.assign(quantile_value)
        self.is_calibrated.assign(True)
        self.calibration_scores = scores

    def get_config(self) -> dict[str, Any]:
        """Get layer configuration for serialization.

        Returns:
            Dictionary of configuration parameters.
        """
        config = super().get_config()
        config.update({
            "alpha": self.alpha,
            "task": self.task,
        })
        return config

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> 'ConformalLayer':
        """Create layer from configuration.

        Args:
            config: Layer configuration dictionary.

        Returns:
            New ConformalLayer instance.
        """
        return cls(**config)


class NonconformityScoreLayer(tf.keras.layers.Layer):
    """Layer that computes nonconformity scores.

    This layer computes nonconformity scores between predictions and targets,
    which are used to calibrate conformal predictors.

    Example:
        ```python
        # In a multi-output model for computing scores
        inputs = tf.keras.Input(shape=(10,))
        prediction = tf.keras.layers.Dense(1)(inputs)
        target = tf.keras.Input(shape=(1,))

        score_layer = NonconformityScoreLayer()
        scores = score_layer([prediction, target])

        scoring_model = tf.keras.Model(
            inputs=[inputs, target],
            outputs=scores
        )
        ```

    Attributes:
        score_type: Type of nonconformity score ('absolute', 'squared', 'custom').
        custom_score_fn: Optional custom scoring function.
    """

    def __init__(
        self,
        score_type: Literal['absolute', 'squared', 'normalized'] = 'absolute',
        custom_score_fn: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize nonconformity score layer.

        Args:
            score_type: Type of score - 'absolute', 'squared', or 'normalized'.
            custom_score_fn: Optional custom TensorFlow function for scoring.
            **kwargs: Additional Keras layer arguments.
        """
        super().__init__(**kwargs)
        self.score_type = score_type
        self.custom_score_fn = custom_score_fn

    @tf.function
    def call(
        self,
        inputs: list[tf.Tensor],
        training: Optional[bool] = None,
    ) -> tf.Tensor:
        """Compute nonconformity scores.

        Args:
            inputs: List of [predictions, targets] tensors.
            training: Whether in training mode.

        Returns:
            Tensor of nonconformity scores.
        """
        if len(inputs) != 2:
            raise ValueError("NonconformityScoreLayer expects [predictions, targets]")

        predictions, targets = inputs

        if self.custom_score_fn is not None:
            return self.custom_score_fn(predictions, targets)

        if self.score_type == 'absolute':
            # |y - ŷ|
            scores = tf.abs(targets - predictions)
        elif self.score_type == 'squared':
            # (y - ŷ)²
            scores = tf.square(targets - predictions)
        elif self.score_type == 'normalized':
            # |y - ŷ| / (|ŷ| + ε)
            epsilon = 1e-8
            scores = tf.abs(targets - predictions) / (tf.abs(predictions) + epsilon)
        else:
            raise ValueError(f"Unknown score_type: {self.score_type}")

        return scores

    def get_config(self) -> dict[str, Any]:
        """Get layer configuration.

        Returns:
            Configuration dictionary.
        """
        config = super().get_config()
        config.update({
            "score_type": self.score_type,
        })
        return config


class PredictionIntervalLayer(tf.keras.layers.Layer):
    """Layer that generates prediction intervals from predictions and quantiles.

    This layer takes predictions and a calibrated quantile value to produce
    prediction intervals for regression tasks.

    Example:
        ```python
        # Create a model that outputs intervals
        inputs = tf.keras.Input(shape=(10,))
        prediction = tf.keras.layers.Dense(1)(inputs)

        interval_layer = PredictionIntervalLayer(quantile=1.5)
        intervals = interval_layer(prediction)

        model = tf.keras.Model(inputs=inputs, outputs=intervals)
        # Output will have shape (batch_size, 3) with columns:
        # [prediction, lower_bound, upper_bound]
        ```

    Attributes:
        quantile: The calibrated quantile value for interval width.
        symmetric: Whether to use symmetric intervals.
        adaptive: Whether to adapt interval width based on input.
    """

    def __init__(
        self,
        quantile: Optional[float] = None,
        symmetric: bool = True,
        adaptive: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize prediction interval layer.

        Args:
            quantile: Initial quantile value. If None, must be set before use.
            symmetric: Whether to create symmetric intervals.
            adaptive: Whether to adapt intervals based on input features.
            **kwargs: Additional Keras layer arguments.
        """
        super().__init__(**kwargs)
        self.symmetric = symmetric
        self.adaptive = adaptive

        # Initialize quantile variable
        initial_value = quantile if quantile is not None else 1.0
        self.quantile = tf.Variable(
            initial_value,
            trainable=False,
            dtype=tf.float32,
            name="quantile",
        )

        if adaptive:
            # For adaptive intervals, we'll learn a scaling function
            self.scale_dense = tf.keras.layers.Dense(
                1,
                activation='sigmoid',
                name='adaptive_scale',
            )

    @tf.function
    def call(
        self,
        inputs: tf.Tensor,
        training: Optional[bool] = None,
    ) -> tf.Tensor:
        """Generate prediction intervals.

        Args:
            inputs: Prediction tensor of shape (batch_size, 1) or (batch_size,).
            training: Whether in training mode.

        Returns:
            Tensor of shape (batch_size, 3) with columns
            [prediction, lower_bound, upper_bound].
        """
        # Ensure inputs have consistent shape
        if len(inputs.shape) == 1:
            inputs = tf.expand_dims(inputs, axis=-1)

        # Compute interval width
        if self.adaptive:
            # Use adaptive scaling based on input features
            # This would typically take additional features as input
            # For simplicity, using a constant scale here
            scale = tf.ones_like(inputs)
            interval_width = self.quantile * scale
        else:
            interval_width = self.quantile

        if self.symmetric:
            # Symmetric intervals: [ŷ - q, ŷ + q]
            lower_bound = inputs - interval_width
            upper_bound = inputs + interval_width
        else:
            # Asymmetric intervals (would require separate quantiles)
            # For now, defaulting to symmetric
            lower_bound = inputs - interval_width
            upper_bound = inputs + interval_width

        # Stack into single output tensor
        output = tf.concat([inputs, lower_bound, upper_bound], axis=-1)

        return output

    def set_quantile(self, quantile: float) -> None:
        """Update the quantile value.

        Args:
            quantile: New quantile value.
        """
        self.quantile.assign(quantile)

    def get_config(self) -> dict[str, Any]:
        """Get layer configuration.

        Returns:
            Configuration dictionary.
        """
        config = super().get_config()
        config.update({
            "quantile": float(self.quantile.numpy()),
            "symmetric": self.symmetric,
            "adaptive": self.adaptive,
        })
        return config

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> 'PredictionIntervalLayer':
        """Create layer from configuration.

        Args:
            config: Layer configuration.

        Returns:
            New PredictionIntervalLayer instance.
        """
        return cls(**config)


class ConformalOutputLayer(tf.keras.layers.Layer):
    """Combined output layer that produces both predictions and conformal intervals.

    This layer is designed to be the final layer in a model, producing
    structured output with predictions and their associated uncertainty.

    Example:
        ```python
        # Build model with conformal output
        inputs = tf.keras.Input(shape=(10,))
        x = tf.keras.layers.Dense(64, activation='relu')(inputs)
        x = tf.keras.layers.Dense(32, activation='relu')(x)
        x = tf.keras.layers.Dense(1)(x)

        output = ConformalOutputLayer(
            alpha=0.1,
            task='regression'
        )(x)

        model = tf.keras.Model(inputs=inputs, outputs=output)
        ```

    Attributes:
        alpha: Significance level.
        task: Task type ('regression' or 'classification').
        quantile: Calibrated quantile.
        return_dict: Whether to return output as dictionary.
    """

    def __init__(
        self,
        alpha: float = 0.1,
        task: str = 'regression',
        return_dict: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize conformal output layer.

        Args:
            alpha: Significance level for intervals.
            task: Task type - 'regression' or 'classification'.
            return_dict: Whether to return structured dict output.
            **kwargs: Additional Keras layer arguments.
        """
        super().__init__(**kwargs)
        self.alpha = alpha
        self.task = task
        self.return_dict = return_dict

        # Initialize components
        self.conformal_layer = ConformalLayer(alpha=alpha, task=task)
        self.interval_layer = PredictionIntervalLayer() if task == 'regression' else None

    def call(
        self,
        inputs: tf.Tensor,
        training: Optional[bool] = None,
    ) -> Union[tf.Tensor, dict[str, tf.Tensor]]:
        """Generate conformal output.

        Args:
            inputs: Input predictions.
            training: Whether in training mode.

        Returns:
            Structured output with predictions and intervals.
            Type is consistent based on return_dict flag for TF 2.16+ compatibility.
        """
        # Apply conformal layer - always returns dict
        conf_output = self.conformal_layer(inputs, training=training)

        # Always return consistent type based on return_dict setting
        if self.return_dict:
            # Return dict (most common use case)
            return conf_output
        else:
            # Return concatenated tensor
            if self.task == 'regression':
                return tf.concat([
                    conf_output['prediction'],
                    conf_output['lower_bound'],
                    conf_output['upper_bound']
                ], axis=-1)
            # For classification, return just the prediction
            return conf_output['prediction']

    def calibrate(self, X_cal: Any, y_cal: Any, model: tf.keras.Model) -> None:
        """Calibrate the conformal components.

        Args:
            X_cal: Calibration features.
            y_cal: Calibration labels.
            model: The containing model.
        """
        self.conformal_layer.calibrate(X_cal, y_cal, model)

        if self.interval_layer is not None:
            self.interval_layer.set_quantile(float(self.conformal_layer.quantile.numpy()))

    def get_config(self) -> dict[str, Any]:
        """Get configuration.

        Returns:
            Configuration dictionary.
        """
        config = super().get_config()
        config.update({
            "alpha": self.alpha,
            "task": self.task,
            "return_dict": self.return_dict,
        })
        return config
