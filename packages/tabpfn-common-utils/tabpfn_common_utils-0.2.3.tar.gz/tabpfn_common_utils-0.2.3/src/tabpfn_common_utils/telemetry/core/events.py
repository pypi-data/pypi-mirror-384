import os
import sys
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Literal, Optional


def _uuid4() -> str:
    """
    Generate a random UUID4.

    Returns:
        str: UUID4 as a string.
    """
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    """
    Get the current UTC date and time.

    Returns:
        datetime: Current UTC date and time.
    """
    return datetime.now(timezone.utc)


@lru_cache(maxsize=1)
def _get_py_version() -> str:
    """
    Get the Python version as a string.

    Returns:
        str: Python version (e.g., "3.9")
    """
    version_info = sys.version_info
    return f"{version_info.major}.{version_info.minor}"


@lru_cache(maxsize=1)
def _get_sdk_version() -> str:
    """
    Get the version of the tabpfn package if it's installed.

    Returns:
        str: Version string if tabpfn is installed.
    """
    try:
        import tabpfn  # type: ignore[import]

        return getattr(tabpfn, "__version__", "unknown")
    except ImportError:
        return "unknown"  # tabpfn is not installed


@dataclass
class BaseTelemetryEvent:
    """
    Base class for all telemetry events.
    """

    # Python version that the SDK is running on
    python_version: str = field(default_factory=_get_py_version, init=False)

    # TabPFN version that the SDK is running on
    tabpfn_version: str = field(default_factory=_get_sdk_version, init=False)

    # Timestamp of the event
    timestamp: datetime = field(default_factory=_utc_now, init=False)

    # Name of the TabPFN extension making the call
    extension: Optional[str] = field(default=None, init=False)

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def source(self) -> str:
        return os.environ.get("TABPFN_TELEMETRY_SOURCE", "sdk")

    @property
    def properties(self) -> dict[str, Any]:
        d = asdict(self)
        d["source"] = self.source
        d.pop("timestamp", None)
        d.pop("name", None)
        return d


@dataclass
class PingEvent(BaseTelemetryEvent):
    """
    Event emitted when a ping is sent.
    """

    frequency: Literal["daily", "weekly", "monthly"] = "daily"

    @property
    def name(self) -> str:
        return "ping"


@dataclass
class DatasetEvent(BaseTelemetryEvent):
    """
    Event emitted when a dataset is loaded. No data is sent with this event.
    """

    # Task associated with the dataset
    task: Literal["classification", "regression"]

    # Role of the dataset in the training/testing process
    role: Literal["train", "test"]

    # Number of rows in the dataset
    num_rows: int = 0

    # Number of columns in the dataset
    num_columns: int = 0

    @property
    def name(self) -> str:
        return "dataset"


@dataclass
class FitEvent(BaseTelemetryEvent):
    """
    Event emitted when a model is fit.
    """

    # Task associated with the fit call
    task: Literal["classification", "regression"]

    # Number of rows in the dataset
    num_rows: int = 0

    # Number of columns in the dataset
    num_columns: int = 0

    # Duration of the fit call in milliseconds
    duration_ms: int = -1

    @property
    def name(self) -> str:
        return "fit_called"


@dataclass
class PredictEvent(BaseTelemetryEvent):
    """
    Event emitted when a model is used to make predictions.
    """

    # Task associated with the predict call
    task: Literal["classification", "regression"]

    # Number of rows in the dataset
    num_rows: int = 0

    # Number of columns in the dataset
    num_columns: int = 0

    # Duration of the predict call in milliseconds
    duration_ms: int = -1

    @property
    def name(self) -> str:
        return "predict_called"
