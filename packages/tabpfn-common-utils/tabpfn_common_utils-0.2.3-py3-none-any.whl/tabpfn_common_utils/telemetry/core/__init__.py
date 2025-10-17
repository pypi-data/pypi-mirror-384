"""Headless telemetry API containing event schemas and capture."""

from __future__ import annotations

from .events import (
    BaseTelemetryEvent,
    PingEvent,
    DatasetEvent,
    FitEvent,
    PredictEvent,
)
from .service import ProductTelemetry, capture_event
from .decorators import track_model_call, set_extension, get_current_extension

# Public exports
__all__ = [
    "BaseTelemetryEvent",
    "PingEvent",
    "DatasetEvent",
    "FitEvent",
    "PredictEvent",
    "ProductTelemetry",
    "capture_event",
    "track_model_call",
    "set_extension",
    "get_current_extension",
]
