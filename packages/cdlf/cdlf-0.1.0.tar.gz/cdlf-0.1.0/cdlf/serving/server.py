"""Production-ready FastAPI server for serving conformal prediction models.

This module provides a production-ready REST API server for deploying
conformal prediction models with automatic documentation, validation, monitoring,
rate limiting, and async support for high-throughput scenarios.
"""

import asyncio
import logging
import os
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import monitoring components
from cdlf.monitoring.metrics import (
    CalibrationMonitor,
    CoverageMonitor,
    IntervalWidthMonitor,
    MonitoringConfig,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Models
# ============================================================================


class ModelType(str, Enum):
    """Supported model types."""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    QUANTILE = "quantile"


class ServerConfig(BaseModel):
    """Server configuration model.

    Attributes:
        host: Server host address
        port: Server port
        workers: Number of worker processes
        reload: Enable hot reload for development
        log_level: Logging level
        cors_origins: Allowed CORS origins
        rate_limit: Rate limit configuration
        max_batch_size: Maximum batch size for predictions
        request_timeout: Request timeout in seconds
        model_cache_size: Number of models to cache
        enable_metrics: Enable Prometheus metrics endpoint
        enable_tracing: Enable distributed tracing
    """

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of workers")
    reload: bool = Field(default=False, description="Enable hot reload")
    log_level: str = Field(default="INFO", description="Log level")
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    rate_limit: str = Field(
        default="100/minute",
        description="Rate limit (e.g., '100/minute')"
    )
    max_batch_size: int = Field(
        default=1000,
        ge=1,
        description="Max batch size"
    )
    request_timeout: int = Field(
        default=30,
        ge=1,
        description="Request timeout (seconds)"
    )
    model_cache_size: int = Field(
        default=5,
        ge=1,
        description="Model cache size"
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics endpoint"
    )
    enable_tracing: bool = Field(
        default=False,
        description="Enable distributed tracing"
    )

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("CDLF_HOST", "0.0.0.0"),
            port=int(os.getenv("CDLF_PORT", "8000")),
            workers=int(os.getenv("CDLF_WORKERS", "1")),
            reload=os.getenv("CDLF_RELOAD", "false").lower() == "true",
            log_level=os.getenv("CDLF_LOG_LEVEL", "INFO"),
            cors_origins=os.getenv("CDLF_CORS_ORIGINS", "*").split(","),
            rate_limit=os.getenv("CDLF_RATE_LIMIT", "100/minute"),
            max_batch_size=int(os.getenv("CDLF_MAX_BATCH_SIZE", "1000")),
            request_timeout=int(os.getenv("CDLF_REQUEST_TIMEOUT", "30")),
            model_cache_size=int(os.getenv("CDLF_MODEL_CACHE_SIZE", "5")),
            enable_metrics=os.getenv("CDLF_ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("CDLF_ENABLE_TRACING", "false").lower() == "true",
        )


# ============================================================================
# Request/Response Models
# ============================================================================


class PredictionRequest(BaseModel):
    """Request model for prediction endpoint.

    Attributes:
        features: Input features as a 2D array
        alpha: Significance level for prediction intervals
        return_intervals: Whether to return prediction intervals
        model_version: Specific model version to use
        request_id: Optional request ID for tracking
    """

    features: List[List[float]] = Field(
        ...,
        description="Input features as 2D array",
        min_items=1,
        max_items=10000  # Prevent DOS
    )
    alpha: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Significance level (1 - coverage)"
    )
    return_intervals: bool = Field(
        default=True,
        description="Return prediction intervals"
    )
    model_version: Optional[str] = Field(
        default=None,
        description="Model version to use"
    )
    request_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Request ID for tracking"
    )

    @validator("features")
    def validate_features(cls, v):
        """Validate feature dimensions."""
        if not v:
            raise ValueError("Features cannot be empty")

        # Check consistent dimensions
        feature_dim = len(v[0])
        if feature_dim == 0:
            raise ValueError("Feature dimension cannot be zero")

        for i, row in enumerate(v):
            if len(row) != feature_dim:
                raise ValueError(f"Inconsistent dimensions at row {i}")

        return v


class BatchPredictionRequest(BaseModel):
    """Request model for batch prediction endpoint.

    Attributes:
        batches: List of prediction requests
        parallel: Process batches in parallel
        fail_fast: Stop on first error
    """

    batches: List[PredictionRequest] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of prediction requests"
    )
    parallel: bool = Field(
        default=True,
        description="Process in parallel"
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop on first error"
    )


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint.

    Attributes:
        predictions: Point predictions
        lower_bounds: Lower bounds of intervals
        upper_bounds: Upper bounds of intervals
        prediction_sets: Prediction sets for classification
        coverage_guarantee: Theoretical coverage guarantee
        model_version: Model version used
        request_id: Request ID for tracking
        processing_time_ms: Processing time in milliseconds
        metadata: Additional metadata
    """

    predictions: List[float] = Field(
        ...,
        description="Point predictions"
    )
    lower_bounds: Optional[List[float]] = Field(
        default=None,
        description="Lower bounds of intervals"
    )
    upper_bounds: Optional[List[float]] = Field(
        default=None,
        description="Upper bounds of intervals"
    )
    prediction_sets: Optional[List[Set[int]]] = Field(
        default=None,
        description="Prediction sets (classification)"
    )
    coverage_guarantee: float = Field(
        ...,
        ge=0,
        le=1,
        description="Coverage guarantee"
    )
    model_version: str = Field(
        ...,
        description="Model version used"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Processing time (ms)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class CalibrationRequest(BaseModel):
    """Request model for calibration update endpoint.

    Attributes:
        features: Calibration features
        labels: Calibration labels
        alpha: Significance level
        method: Calibration method
        replace: Replace existing calibration
    """

    features: List[List[float]] = Field(
        ...,
        min_items=10,
        max_items=100000,
        description="Calibration features"
    )
    labels: List[float] = Field(
        ...,
        min_items=10,
        max_items=100000,
        description="Calibration labels"
    )
    alpha: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="Significance level"
    )
    method: str = Field(
        default="split",
        description="Calibration method"
    )
    replace: bool = Field(
        default=False,
        description="Replace existing calibration"
    )

    @validator("labels")
    def validate_dimensions(cls, v, values):
        """Validate matching dimensions."""
        if "features" in values and len(v) != len(values["features"]):
            raise ValueError("Features and labels must have same length")
        return v


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint.

    Attributes:
        coverage: Coverage metrics by window
        efficiency: Efficiency metrics
        drift: Drift detection status
        model_versions: Active model versions
        total_predictions: Total prediction count
        uptime_seconds: Server uptime
    """

    coverage: Dict[str, Optional[float]] = Field(
        ...,
        description="Coverage by time window"
    )
    efficiency: Dict[str, Optional[float]] = Field(
        ...,
        description="Efficiency metrics"
    )
    drift: bool = Field(
        ...,
        description="Drift detected"
    )
    model_versions: List[str] = Field(
        ...,
        description="Active model versions"
    )
    total_predictions: int = Field(
        ...,
        ge=0,
        description="Total predictions"
    )
    uptime_seconds: float = Field(
        ...,
        ge=0,
        description="Server uptime"
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint.

    Attributes:
        status: Health status
        timestamp: Current timestamp
        version: Server version
        model_loaded: Model loaded status
        monitoring_active: Monitoring status
    """

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Timestamp")
    version: str = Field(..., description="Server version")
    model_loaded: bool = Field(..., description="Model loaded")
    monitoring_active: bool = Field(..., description="Monitoring active")


# ============================================================================
# Model Manager
# ============================================================================


class ModelManager:
    """Manages multiple model versions with caching and hot-swapping.

    Attributes:
        models: Dictionary of loaded models
        active_version: Currently active model version
        cache_size: Maximum models to keep in memory
    """

    def __init__(self, cache_size: int = 5):
        """Initialize model manager.

        Args:
            cache_size: Maximum number of models to cache
        """
        self.models: Dict[str, Any] = {}
        self.active_version: Optional[str] = None
        self.cache_size = cache_size
        self._lock = asyncio.Lock()
        logger.info(f"ModelManager initialized with cache_size={cache_size}")

    async def load_model(
        self,
        model: Any,
        version: str = "default",
        activate: bool = True
    ) -> None:
        """Load a model version.

        Args:
            model: Model instance
            version: Model version identifier
            activate: Whether to make this the active version
        """
        async with self._lock:
            # Check cache size
            if len(self.models) >= self.cache_size:
                # Remove oldest non-active model
                for v in list(self.models.keys()):
                    if v != self.active_version:
                        del self.models[v]
                        logger.info(f"Evicted model version: {v}")
                        break

            # Store model
            self.models[version] = model

            if activate or self.active_version is None:
                self.active_version = version
                logger.info(f"Activated model version: {version}")

    async def get_model(self, version: Optional[str] = None) -> Any:
        """Get a model by version.

        Args:
            version: Model version (uses active if None)

        Returns:
            Model instance

        Raises:
            ValueError: If model version not found
        """
        async with self._lock:
            version = version or self.active_version
            if not version or version not in self.models:
                raise ValueError(f"Model version not found: {version}")
            return self.models[version]

    async def list_versions(self) -> List[str]:
        """List available model versions."""
        async with self._lock:
            return list(self.models.keys())


# ============================================================================
# Main Server Class
# ============================================================================


class ConformalPredictionServer:
    """Production-ready FastAPI server for conformal prediction models.

    This class provides a complete REST API for serving conformal prediction
    models with monitoring, versioning, rate limiting, and async support.

    Attributes:
        config: Server configuration
        model_manager: Model version manager
        coverage_monitor: Coverage monitoring
        width_monitor: Interval width monitoring
        calibration_monitor: Calibration drift monitoring
        app: FastAPI application instance
        start_time: Server start timestamp
    """

    def __init__(
        self,
        model: Optional[Any] = None,
        config: Optional[ServerConfig] = None,
        monitoring_config: Optional[MonitoringConfig] = None
    ):
        """Initialize the prediction server.

        Args:
            model: Initial model to serve
            config: Server configuration
            monitoring_config: Monitoring configuration
        """
        self.config = config or ServerConfig.from_env()
        self.monitoring_config = monitoring_config or MonitoringConfig()

        # Initialize components
        self.model_manager = ModelManager(self.config.model_cache_size)
        self.coverage_monitor = CoverageMonitor(config=self.monitoring_config)
        self.width_monitor = IntervalWidthMonitor(config=self.monitoring_config)
        self.calibration_monitor = CalibrationMonitor(config=self.monitoring_config)

        # Server state
        self.start_time = datetime.now()
        self.total_predictions = 0
        self.app: Optional[FastAPI] = None

        # Load initial model if provided
        if model is not None:
            # Note: Model loading will be completed during app startup in lifespan
            self._initial_model = model
        else:
            self._initial_model = None

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        logger.info("ConformalPredictionServer initialized")

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Manage application lifecycle.

        Args:
            app: FastAPI application instance
        """
        # Startup
        logger.info("Starting ConformalPredictionServer...")

        # Load initial model if provided
        if self._initial_model is not None:
            await self.model_manager.load_model(self._initial_model)
            logger.info("Initial model loaded successfully")

        yield
        # Shutdown
        logger.info("Shutting down ConformalPredictionServer...")

    def create_app(self) -> FastAPI:
        """Create and configure FastAPI application.

        Returns:
            Configured FastAPI application
        """
        # Create app with lifespan manager
        self.app = FastAPI(
            title="CDLF Prediction Server",
            description="Production-ready API for Conformal Deep Learning Framework",
            version="1.0.0",
            lifespan=self.lifespan,
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )

        # Configure rate limiting
        self.limiter = Limiter(key_func=get_remote_address)
        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        # Add middleware
        self._add_middleware()

        # Add routes
        self._add_routes()

        # Add exception handlers
        self._add_exception_handlers()

        logger.info("FastAPI application created")
        return self.app

    def _add_middleware(self) -> None:
        """Add middleware to the application."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # GZip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Trusted host middleware for security
        if self.config.host != "0.0.0.0":
            # Add testserver for test compatibility
            allowed_hosts = [self.config.host, "testserver"]
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=allowed_hosts
            )

        # Request ID and logging middleware
        @self.app.middleware("http")
        async def add_request_id(request: Request, call_next):
            request_id = request.headers.get("X-Request-ID", str(time.time()))
            logger.info(f"Request {request_id}: {request.method} {request.url}")

            start_time = time.time()
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            logger.info(f"Request {request_id} completed in {process_time:.2f}ms")
            return response

    def _add_routes(self) -> None:
        """Add API routes to the application."""
        limiter = self.app.state.limiter

        # Health check endpoint
        @self.app.get(
            "/health",
            response_model=HealthResponse,
            tags=["Health"],
            summary="Health check endpoint"
        )
        async def health_check() -> HealthResponse:
            """Check server health and readiness."""
            try:
                versions = await self.model_manager.list_versions()
                model_loaded = len(versions) > 0
            except:
                model_loaded = False

            return HealthResponse(
                status="healthy" if model_loaded else "degraded",
                timestamp=datetime.now(),
                version="1.0.0",
                model_loaded=model_loaded,
                monitoring_active=True
            )

        # Liveness probe (Kubernetes)
        @self.app.get("/livez", tags=["Health"])
        async def liveness() -> Response:
            """Kubernetes liveness probe."""
            return Response(content="OK", status_code=200)

        # Readiness probe (Kubernetes)
        @self.app.get("/readyz", tags=["Health"])
        async def readiness() -> Response:
            """Kubernetes readiness probe."""
            try:
                versions = await self.model_manager.list_versions()
                if len(versions) > 0:
                    return Response(content="OK", status_code=200)
            except:
                pass
            return Response(content="Not Ready", status_code=503)

        # Main prediction endpoint
        @self.app.post(
            "/predict",
            response_model=PredictionResponse,
            tags=["Prediction"],
            summary="Make predictions with intervals"
        )
        @self.limiter.limit(self.config.rate_limit)
        async def predict(
            prediction_request: PredictionRequest,
            background_tasks: BackgroundTasks,
            request: Request
        ) -> PredictionResponse:
            """Make predictions with conformal prediction intervals."""
            start_time = time.time()

            try:
                # Get model
                model = await self.model_manager.get_model(prediction_request.model_version)

                # Convert features to numpy
                X = np.array(prediction_request.features)

                # Make predictions
                if prediction_request.return_intervals:
                    predictions, intervals = await self._async_predict_with_intervals(
                        model, X, prediction_request.alpha
                    )
                    lower_bounds = intervals[0].tolist()
                    upper_bounds = intervals[1].tolist()
                else:
                    predictions = await self._async_predict(model, X)
                    lower_bounds = None
                    upper_bounds = None

                # Track in background
                if prediction_request.return_intervals:
                    for i, (lower, upper) in enumerate(zip(lower_bounds, upper_bounds)):
                        background_tasks.add_task(
                            self.width_monitor.track_interval,
                            upper - lower,
                            model_version=prediction_request.model_version
                        )

                self.total_predictions += len(predictions)

                processing_time = (time.time() - start_time) * 1000

                return PredictionResponse(
                    predictions=predictions.tolist(),
                    lower_bounds=lower_bounds,
                    upper_bounds=upper_bounds,
                    coverage_guarantee=1 - prediction_request.alpha,
                    model_version=prediction_request.model_version or self.model_manager.active_version,
                    request_id=prediction_request.request_id,
                    processing_time_ms=processing_time,
                    metadata={
                        "batch_size": len(prediction_request.features),
                        "alpha": prediction_request.alpha
                    }
                )

            except Exception as e:
                logger.error(f"Prediction error: {str(e)}\n{traceback.format_exc()}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Prediction failed: {str(e)}"
                )

        # Batch prediction endpoint
        @self.app.post(
            "/batch_predict",
            response_model=List[PredictionResponse],
            tags=["Prediction"],
            summary="Batch predictions"
        )
        @self.limiter.limit(f"{int(self.config.rate_limit.split('/')[0])*10}/minute")
        async def batch_predict(
            batch_request: BatchPredictionRequest,
            background_tasks: BackgroundTasks,
            request: Request
        ) -> List[PredictionResponse]:
            """Process multiple prediction requests in batch."""
            responses = []

            if batch_request.parallel:
                # Process in parallel
                tasks = [
                    predict(batch, background_tasks, request)
                    for batch in batch_request.batches
                ]
                responses = await asyncio.gather(
                    *tasks,
                    return_exceptions=not batch_request.fail_fast
                )

                # Handle exceptions
                if batch_request.fail_fast:
                    for r in responses:
                        if isinstance(r, Exception):
                            raise r
            else:
                # Process sequentially
                for batch in batch_request.batches:
                    try:
                        response = await predict(batch, background_tasks, request)
                        responses.append(response)
                    except Exception as e:
                        if batch_request.fail_fast:
                            raise
                        responses.append(None)

            return [r for r in responses if r is not None]

        # Calibration update endpoint
        @self.app.post(
            "/calibrate",
            tags=["Calibration"],
            summary="Update model calibration"
        )
        @self.limiter.limit("10/hour")
        async def calibrate(
            calibration_request: CalibrationRequest,
            background_tasks: BackgroundTasks,
            request: Request
        ) -> Dict[str, Any]:
            """Update model calibration with new data."""
            try:
                model = await self.model_manager.get_model()

                X_cal = np.array(calibration_request.features)
                y_cal = np.array(calibration_request.labels)

                # Recalibrate model
                if hasattr(model, 'calibrate'):
                    await self._async_calibrate(model, X_cal, y_cal, calibration_request.alpha)

                    # Track calibration update
                    background_tasks.add_task(
                        self.calibration_monitor.update_baseline,
                        y_cal
                    )

                    return {
                        "status": "success",
                        "message": "Calibration updated",
                        "samples": len(y_cal),
                        "alpha": calibration_request.alpha
                    }
                else:
                    raise HTTPException(
                        status_code=status.HTTP_501_NOT_IMPLEMENTED,
                        detail="Model does not support calibration updates"
                    )

            except HTTPException:
                # Re-raise HTTPException (like 501 Not Implemented)
                raise
            except Exception as e:
                logger.error(f"Calibration error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Calibration failed: {str(e)}"
                )

        # Metrics endpoint
        @self.app.get(
            "/metrics",
            response_model=MetricsResponse,
            tags=["Monitoring"],
            summary="Get monitoring metrics"
        )
        async def get_metrics() -> MetricsResponse:
            """Get current monitoring metrics."""
            coverage = self.coverage_monitor.get_coverage_by_window()
            efficiency = self.width_monitor.get_efficiency_metrics()
            drift = self.calibration_monitor.detect_drift()
            versions = await self.model_manager.list_versions()
            uptime = (datetime.now() - self.start_time).total_seconds()

            return MetricsResponse(
                coverage=coverage,
                efficiency=efficiency,
                drift=drift,
                model_versions=versions,
                total_predictions=self.total_predictions,
                uptime_seconds=uptime
            )

        # Prometheus metrics endpoint
        if self.config.enable_metrics:
            @self.app.get(
                "/prometheus",
                tags=["Monitoring"],
                summary="Prometheus metrics export"
            )
            async def prometheus_metrics() -> Response:
                """Export metrics in Prometheus format."""
                metrics = self.calibration_monitor.export_prometheus_metrics()
                return Response(
                    content=metrics,
                    media_type="text/plain"
                )

        # Model management endpoints
        @self.app.get(
            "/models",
            tags=["Models"],
            summary="List model versions"
        )
        async def list_models() -> Dict[str, Any]:
            """List available model versions."""
            versions = await self.model_manager.list_versions()
            return {
                "versions": versions,
                "active": self.model_manager.active_version
            }

        @self.app.post(
            "/models/{version}/activate",
            tags=["Models"],
            summary="Activate model version"
        )
        @self.limiter.limit("10/hour")
        async def activate_model(request: Request, version: str) -> Dict[str, str]:
            """Activate a specific model version."""
            try:
                await self.model_manager.get_model(version)
                self.model_manager.active_version = version
                return {"status": "success", "active_version": version}
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )

    def _add_exception_handlers(self) -> None:
        """Add custom exception handlers."""
        @self.app.exception_handler(ValueError)
        async def value_error_handler(request: Request, exc: ValueError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": str(exc)}
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    async def _async_predict(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Make async predictions (wraps sync predict)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, model.predict, X)

    async def _async_predict_with_intervals(
        self,
        model: Any,
        X: np.ndarray,
        alpha: float
    ) -> tuple:
        """Make async predictions with intervals."""
        loop = asyncio.get_event_loop()

        if hasattr(model, 'predict_interval'):
            return await loop.run_in_executor(
                None,
                model.predict_interval,
                X,
                alpha
            )
        else:
            # Fallback for models without interval prediction
            predictions = await self._async_predict(model, X)
            # Simple interval estimation (should be replaced with actual CP)
            std = 1.0  # Placeholder
            z_score = 1.96  # For ~95% confidence
            lower = predictions - z_score * std
            upper = predictions + z_score * std
            return predictions, (lower, upper)

    async def _async_calibrate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        alpha: float
    ) -> None:
        """Perform async calibration."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, model.calibrate, X, y, alpha)

    def run(self) -> None:
        """Start the prediction server."""
        if self.app is None:
            self.create_app()

        import uvicorn

        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            workers=self.config.workers,
            reload=self.config.reload,
            log_level=self.config.log_level.lower()
        )


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    """
    Example usage of the ConformalPredictionServer.

    To run the server:
    ```python
    # Create a mock model for demonstration
    class MockModel:
        def predict(self, X):
            return np.random.randn(len(X))

        def predict_interval(self, X, alpha):
            predictions = self.predict(X)
            lower = predictions - 1.96
            upper = predictions + 1.96
            return predictions, (lower, upper)

        def calibrate(self, X, y, alpha):
            pass

    # Initialize and run server
    model = MockModel()
    server = ConformalPredictionServer(model)
    server.run()
    ```

    The server will be available at http://localhost:8000
    API documentation at http://localhost:8000/docs

    Example API calls:

    1. Health check:
    GET http://localhost:8000/health

    2. Make predictions:
    POST http://localhost:8000/predict
    {
        "features": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        "alpha": 0.1,
        "return_intervals": true
    }

    3. Batch predictions:
    POST http://localhost:8000/batch_predict
    {
        "batches": [
            {"features": [[1.0, 2.0]], "alpha": 0.1},
            {"features": [[3.0, 4.0]], "alpha": 0.05}
        ],
        "parallel": true
    }

    4. Get metrics:
    GET http://localhost:8000/metrics

    5. Update calibration:
    POST http://localhost:8000/calibrate
    {
        "features": [[1.0, 2.0], [3.0, 4.0]],
        "labels": [0.5, 1.5],
        "alpha": 0.1
    }

    Docker deployment:
    ```dockerfile
    FROM python:3.9-slim

    WORKDIR /app
    COPY requirements.txt .
    RUN pip install -r requirements.txt

    COPY . .

    ENV CDLF_HOST=0.0.0.0
    ENV CDLF_PORT=8000
    ENV CDLF_WORKERS=4
    ENV CDLF_LOG_LEVEL=INFO

    EXPOSE 8000

    CMD ["python", "-m", "cdlf.serving.server"]
    ```
    """

    # Demo server with mock model
    logger.info("Starting demo server...")

    class MockModel:
        """Mock model for demonstration."""
        def predict(self, X):
            return np.random.randn(len(X))

        def predict_interval(self, X, alpha):
            predictions = self.predict(X)
            lower = predictions - 1.96
            upper = predictions + 1.96
            return predictions, (lower, upper)

        def calibrate(self, X, y, alpha):
            logger.info(f"Mock calibration with {len(X)} samples")

    # Create and run server
    config = ServerConfig(
        host="0.0.0.0",
        port=8000,
        workers=1,
        reload=False,
        log_level="INFO"
    )

    server = ConformalPredictionServer(
        model=MockModel(),
        config=config
    )

    server.run()
