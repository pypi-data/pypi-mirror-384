"""Production-ready monitoring and metrics for conformal prediction.

This module provides comprehensive metrics for evaluating conformal prediction
performance including coverage, efficiency, validity tracking, and drift detection
with Prometheus metrics export support.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import numpy.typing as npt

# Optional Prometheus import - graceful fallback if not installed
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not installed. Metrics export disabled.")

logger = logging.getLogger(__name__)


@dataclass
class PredictionRecord:
    """Record of a single prediction for monitoring.

    Attributes:
        timestamp: Time of prediction
        y_true: True value (if available)
        prediction_set: Predicted interval or set
        interval_width: Width of the prediction interval
        covered: Whether the true value was covered
        model_version: Version of the model used
    """
    timestamp: datetime
    y_true: Optional[float] = None
    prediction_set: Optional[Union[Tuple[float, float], Set[int]]] = None
    interval_width: Optional[float] = None
    covered: Optional[bool] = None
    model_version: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Configuration for monitoring system.

    Attributes:
        coverage_threshold: Alert threshold for coverage degradation
        drift_threshold: Threshold for drift detection
        window_sizes: Time windows for aggregation (in seconds)
        max_history_size: Maximum records to keep in memory
        alert_cooldown: Minimum seconds between alerts
        enable_prometheus: Whether to enable Prometheus metrics
    """
    coverage_threshold: float = 0.85
    drift_threshold: float = 0.05
    window_sizes: List[int] = field(default_factory=lambda: [60, 300, 3600, 86400])
    max_history_size: int = 10000
    alert_cooldown: int = 300
    enable_prometheus: bool = False  # Disabled by default to avoid test conflicts


class CoverageMonitor:
    """Monitor for tracking empirical coverage with time-based aggregation.

    This class tracks prediction coverage over time, supports sliding windows,
    generates alerts when coverage drops below threshold, and exports metrics.

    Attributes:
        config: Monitoring configuration
        alpha: Target significance level
        history: Deque of prediction records
        alerts: List of generated alerts
        prometheus_metrics: Dictionary of Prometheus metric objects
    """

    def __init__(
        self,
        alpha: float = 0.1,
        config: Optional[MonitoringConfig] = None
    ) -> None:
        """Initialize coverage monitor.

        Args:
            alpha: Target significance level (1 - coverage)
            config: Monitoring configuration

        Raises:
            ValueError: If alpha is not in (0, 1)
        """
        if not 0 < alpha < 1:
            raise ValueError(f"alpha must be in (0, 1), got {alpha}")

        self.alpha = alpha
        self.target_coverage = 1 - alpha
        self.config = config or MonitoringConfig()

        # Storage
        self.history: deque = deque(maxlen=self.config.max_history_size)
        self.alerts: List[Dict[str, Any]] = []
        self._last_alert_time: Optional[datetime] = None

        # Initialize Prometheus metrics if available
        self.prometheus_metrics = {}
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self._init_prometheus_metrics()

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metric collectors."""
        from prometheus_client import REGISTRY

        # Check if metrics already exist, reuse them if they do
        def get_or_create_gauge(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Gauge(name, doc, labels)

        def get_or_create_counter(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Counter(name, doc, labels)

        self.prometheus_metrics = {
            'coverage_rate': get_or_create_gauge(
                'cdlf_coverage_rate',
                'Empirical coverage rate',
                ['window', 'model_version']
            ),
            'predictions_total': get_or_create_counter(
                'cdlf_predictions_total',
                'Total number of predictions',
                ['model_version']
            ),
            'coverage_violations': get_or_create_counter(
                'cdlf_coverage_violations',
                'Number of coverage violations',
                ['model_version']
            ),
            'coverage_alert': get_or_create_gauge(
                'cdlf_coverage_alert',
                'Coverage degradation alert (1=active, 0=cleared)',
                ['model_version']
            )
        }
        logger.info("Prometheus metrics initialized")

    def track_prediction(
        self,
        y_true: Optional[float],
        prediction_set: Union[Tuple[float, float], Set[int]],
        timestamp: Optional[datetime] = None,
        model_version: Optional[str] = None
    ) -> None:
        """Track a single prediction for monitoring.

        Args:
            y_true: True value (None if not yet available)
            prediction_set: Prediction interval (lower, upper) or set of classes
            timestamp: Time of prediction (defaults to now)
            model_version: Version of model used
        """
        timestamp = timestamp or datetime.now()

        # Calculate coverage and width
        covered = None
        interval_width = None

        if isinstance(prediction_set, tuple) and len(prediction_set) == 2:
            # Regression interval
            lower, upper = prediction_set
            interval_width = upper - lower
            if y_true is not None:
                covered = lower <= y_true <= upper
        elif isinstance(prediction_set, set):
            # Classification set
            interval_width = len(prediction_set)
            if y_true is not None:
                covered = y_true in prediction_set

        # Store record
        record = PredictionRecord(
            timestamp=timestamp,
            y_true=y_true,
            prediction_set=prediction_set,
            interval_width=interval_width,
            covered=covered,
            model_version=model_version or "default"
        )
        self.history.append(record)

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['predictions_total'].labels(
                model_version=record.model_version
            ).inc()

            if covered is False:
                self.prometheus_metrics['coverage_violations'].labels(
                    model_version=record.model_version
                ).inc()

        # Check for alerts
        self._check_coverage_alert()

        logger.debug(f"Tracked prediction: covered={covered}, width={interval_width}")

    def get_coverage_rate(
        self,
        window: Union[str, int] = '1h',
        model_version: Optional[str] = None
    ) -> float:
        """Get coverage rate for a specific time window.

        Args:
            window: Time window as string ('1m', '5m', '1h', '24h') or seconds
            model_version: Filter by model version

        Returns:
            Coverage rate in [0, 1], or NaN if no data
        """
        window_seconds = self._parse_window(window)
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        # Filter records
        relevant_records = [
            r for r in self.history
            if r.timestamp >= cutoff_time
            and r.covered is not None
            and (model_version is None or r.model_version == model_version)
        ]

        if not relevant_records:
            return None

        coverage = sum(r.covered for r in relevant_records) / len(relevant_records)

        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['coverage_rate'].labels(
                window=window,
                model_version=model_version or "all"
            ).set(coverage)

        return coverage

    def get_coverage_by_window(
        self,
        model_version: Optional[str] = None
    ) -> Dict[str, float]:
        """Get coverage rates for all configured time windows.

        Args:
            model_version: Filter by model version

        Returns:
            Dictionary mapping window names to coverage rates
        """
        windows = {
            '1m': 60,
            '5m': 300,
            '1h': 3600,
            '24h': 86400
        }

        return {
            window: self.get_coverage_rate(seconds, model_version)
            for window, seconds in windows.items()
        }

    def _parse_window(self, window: Union[str, int]) -> int:
        """Parse window specification to seconds.

        Args:
            window: Window as string or integer seconds

        Returns:
            Window size in seconds
        """
        if isinstance(window, int):
            return window

        # Parse string formats
        window = window.lower()
        if window.endswith('m'):
            return int(window[:-1]) * 60
        elif window.endswith('h'):
            return int(window[:-1]) * 3600
        elif window.endswith('d'):
            return int(window[:-1]) * 86400
        else:
            return int(window)

    def _check_coverage_alert(self) -> None:
        """Check if coverage has dropped below threshold and generate alert."""
        # Check cooldown
        if self._last_alert_time:
            time_since_alert = (datetime.now() - self._last_alert_time).total_seconds()
            if time_since_alert < self.config.alert_cooldown:
                return

        # Check short-term coverage
        coverage_5m = self.get_coverage_rate('5m')
        if np.isnan(coverage_5m):
            return

        if coverage_5m < self.config.coverage_threshold * self.target_coverage:
            alert = {
                'timestamp': datetime.now(),
                'type': 'coverage_degradation',
                'severity': 'warning',
                'message': f'Coverage dropped to {coverage_5m:.2%} (target: {self.target_coverage:.2%})',
                'coverage': coverage_5m,
                'target': self.target_coverage
            }

            self.alerts.append(alert)
            self._last_alert_time = datetime.now()

            # Update Prometheus alert metric
            if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
                self.prometheus_metrics['coverage_alert'].labels(
                    model_version="all"
                ).set(1)

            logger.warning(alert['message'])
        else:
            # Clear alert if coverage recovered
            if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
                self.prometheus_metrics['coverage_alert'].labels(
                    model_version="all"
                ).set(0)


class IntervalWidthMonitor:
    """Monitor for tracking prediction interval efficiency.

    This class tracks the distribution of prediction interval widths,
    identifies efficiency degradation, and provides statistical summaries.

    Attributes:
        config: Monitoring configuration
        width_history: Deque of interval width records
        prometheus_metrics: Dictionary of Prometheus metric objects
    """

    def __init__(self, config: Optional[MonitoringConfig] = None) -> None:
        """Initialize interval width monitor.

        Args:
            config: Monitoring configuration
        """
        self.config = config or MonitoringConfig()
        self.width_history: deque = deque(maxlen=self.config.max_history_size)

        # Initialize Prometheus metrics
        self.prometheus_metrics = {}
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self._init_prometheus_metrics()

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metric collectors."""
        from prometheus_client import REGISTRY

        # Check if metrics already exist, reuse them if they do
        def get_or_create_summary(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Summary(name, doc, labels)

        def get_or_create_gauge(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Gauge(name, doc, labels)

        self.prometheus_metrics = {
            'interval_width': get_or_create_summary(
                'cdlf_interval_width',
                'Prediction interval width distribution',
                ['model_version']
            ),
            'interval_width_mean': get_or_create_gauge(
                'cdlf_interval_width_mean',
                'Mean prediction interval width',
                ['window', 'model_version']
            ),
            'interval_width_median': get_or_create_gauge(
                'cdlf_interval_width_median',
                'Median prediction interval width',
                ['window', 'model_version']
            ),
            'interval_width_p95': get_or_create_gauge(
                'cdlf_interval_width_p95',
                '95th percentile prediction interval width',
                ['window', 'model_version']
            )
        }

    def track_interval(
        self,
        interval_width: float,
        timestamp: Optional[datetime] = None,
        model_version: Optional[str] = None
    ) -> None:
        """Track an interval width measurement.

        Args:
            interval_width: Width of the prediction interval
            timestamp: Time of measurement
            model_version: Model version used
        """
        record = {
            'timestamp': timestamp or datetime.now(),
            'width': interval_width,
            'model_version': model_version or 'default'
        }
        self.width_history.append(record)

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['interval_width'].labels(
                model_version=record['model_version']
            ).observe(interval_width)

    def get_efficiency_metrics(
        self,
        window: Union[str, int] = '1h',
        model_version: Optional[str] = None
    ) -> Dict[str, float]:
        """Get efficiency metrics for a time window.

        Args:
            window: Time window specification
            model_version: Filter by model version

        Returns:
            Dictionary with mean, median, std, p95 interval widths
        """
        window_seconds = self._parse_window(window)
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        # Filter records
        widths = [
            r['width'] for r in self.width_history
            if r['timestamp'] >= cutoff_time
            and (model_version is None or r['model_version'] == model_version)
        ]

        if not widths:
            return {
                'mean': None,
                'median': None,
                'std': None,
                'p95': None,
                'count': 0
            }

        metrics = {
            'mean': np.mean(widths),
            'median': np.median(widths),
            'std': np.std(widths),
            'p95': np.percentile(widths, 95),
            'count': len(widths)
        }

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['interval_width_mean'].labels(
                window=window,
                model_version=model_version or "all"
            ).set(metrics['mean'])

            self.prometheus_metrics['interval_width_median'].labels(
                window=window,
                model_version=model_version or "all"
            ).set(metrics['median'])

            self.prometheus_metrics['interval_width_p95'].labels(
                window=window,
                model_version=model_version or "all"
            ).set(metrics['p95'])

        return metrics

    def _parse_window(self, window: Union[str, int]) -> int:
        """Parse window specification to seconds."""
        if isinstance(window, int):
            return window

        window = window.lower()
        if window.endswith('m'):
            return int(window[:-1]) * 60
        elif window.endswith('h'):
            return int(window[:-1]) * 3600
        elif window.endswith('d'):
            return int(window[:-1]) * 86400
        else:
            return int(window)


class CalibrationMonitor:
    """Monitor for detecting distribution drift and calibration issues.

    This class tracks calibration scores over time, detects distribution drift,
    and provides alerts when recalibration may be needed.

    Attributes:
        config: Monitoring configuration
        calibration_history: History of calibration scores
        drift_detector: Drift detection algorithm state
        prometheus_metrics: Prometheus metric objects
    """

    def __init__(
        self,
        config: Optional[MonitoringConfig] = None,
        baseline_scores: Optional[npt.NDArray[Any]] = None
    ) -> None:
        """Initialize calibration monitor.

        Args:
            config: Monitoring configuration
            baseline_scores: Initial calibration scores for drift detection
        """
        self.config = config or MonitoringConfig()
        self.calibration_history: deque = deque(maxlen=self.config.max_history_size)
        self.baseline_scores = baseline_scores
        self.drift_alerts: List[Dict[str, Any]] = []

        # Initialize Prometheus metrics
        self.prometheus_metrics = {}
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self._init_prometheus_metrics()

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metric collectors."""
        from prometheus_client import REGISTRY

        # Check if metrics already exist, reuse them if they do
        def get_or_create_summary(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Summary(name, doc, labels)

        def get_or_create_gauge(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Gauge(name, doc, labels)

        def get_or_create_counter(name: str, doc: str, labels: list) -> Any:
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name') and collector._name == name:
                    return collector
            return Counter(name, doc, labels)

        self.prometheus_metrics = {
            'calibration_score': get_or_create_summary(
                'cdlf_calibration_score',
                'Nonconformity score distribution',
                ['model_version']
            ),
            'drift_detected': get_or_create_gauge(
                'cdlf_drift_detected',
                'Distribution drift detection (1=drift, 0=stable)',
                ['model_version']
            ),
            'calibration_updates': get_or_create_counter(
                'cdlf_calibration_updates',
                'Number of calibration updates',
                ['model_version']
            )
        }

    def track_calibration_score(
        self,
        score: float,
        timestamp: Optional[datetime] = None,
        model_version: Optional[str] = None
    ) -> None:
        """Track a calibration/nonconformity score.

        Args:
            score: Nonconformity score
            timestamp: Time of measurement
            model_version: Model version
        """
        record = {
            'timestamp': timestamp or datetime.now(),
            'score': score,
            'model_version': model_version or 'default'
        }
        self.calibration_history.append(record)

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['calibration_score'].labels(
                model_version=record['model_version']
            ).observe(score)

    def detect_drift(
        self,
        threshold: Optional[float] = None,
        window: Union[str, int] = '1h',
        method: str = 'ks'
    ) -> bool:
        """Detect distribution drift in calibration scores.

        Args:
            threshold: Drift detection threshold (uses config default if None)
            window: Time window for recent scores
            method: Detection method ('ks' for Kolmogorov-Smirnov test)

        Returns:
            True if drift detected, False otherwise
        """
        if self.baseline_scores is None:
            logger.warning("No baseline scores set for drift detection")
            return False

        threshold = threshold or self.config.drift_threshold
        window_seconds = self._parse_window(window)
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        # Get recent scores
        recent_scores = np.array([
            r['score'] for r in self.calibration_history
            if r['timestamp'] >= cutoff_time
        ])

        if len(recent_scores) < 30:  # Need minimum samples
            return False

        # Perform drift test
        drift_detected = False

        if method == 'ks':
            from scipy.stats import ks_2samp
            statistic, p_value = ks_2samp(self.baseline_scores, recent_scores)
            drift_detected = p_value < threshold

            if drift_detected:
                alert = {
                    'timestamp': datetime.now(),
                    'type': 'distribution_drift',
                    'severity': 'warning',
                    'message': f'Distribution drift detected (p-value: {p_value:.4f})',
                    'statistic': statistic,
                    'p_value': p_value,
                    'method': method
                }
                self.drift_alerts.append(alert)
                logger.warning(alert['message'])

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['drift_detected'].labels(
                model_version='all'
            ).set(1 if drift_detected else 0)

        return drift_detected

    def update_baseline(self, new_baseline: npt.NDArray[Any]) -> None:
        """Update baseline calibration scores.

        Args:
            new_baseline: New baseline scores for drift detection
        """
        self.baseline_scores = new_baseline

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE and self.config.enable_prometheus:
            self.prometheus_metrics['calibration_updates'].labels(
                model_version='all'
            ).inc()

        logger.info(f"Updated baseline with {len(new_baseline)} scores")

    def _parse_window(self, window: Union[str, int]) -> int:
        """Parse window specification to seconds."""
        if isinstance(window, int):
            return window

        window = window.lower()
        if window.endswith('m'):
            return int(window[:-1]) * 60
        elif window.endswith('h'):
            return int(window[:-1]) * 3600
        elif window.endswith('d'):
            return int(window[:-1]) * 86400
        else:
            return int(window)

    def export_prometheus_metrics(self) -> str:
        """Export all metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available"

        from prometheus_client import generate_latest
        return generate_latest().decode('utf-8')
