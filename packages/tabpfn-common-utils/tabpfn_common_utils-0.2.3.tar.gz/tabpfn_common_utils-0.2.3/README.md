# TabPFN Common Utilities

A comprehensive utility package for [TabPFN](https://github.com/priorlabs/tabpfn) - the foundation model for tabular data.

## Features

### 🔒 Privacy-First Telemetry System
- **Anonymous & Aggregated Data Collection**: Implements safe, GDPR-compliant telemetry that respects user privacy
- **Configurable Analytics**: Optional telemetry that can be disabled via environment variables
- **Usage Pattern Insights**: Tracks TabPFN usage patterns to improve the model and user experience
- **Zero Personal Data**: No personal information or sensitive data is collected or transmitted

### 💰 Cost Estimation
- **Resource Planning**: Accurate estimation of computational costs and duration for TabPFN predictions
- **Cloud Pricing**: Essential for resource planning in cloud-based TabPFN services
- **Task-Specific Calculations**: Different cost models for classification vs regression tasks

### 📊 Data Processing Utilities
- **Regression Results**: Comprehensive handling of prediction outputs with mean, median, mode, and quantiles
- **Data Serialization**: Convert between pandas DataFrames, NumPy arrays, and CSV formats
- **Dataset Management**: Load and preprocess standard ML datasets with proper train/test splits
- **Preprocessing Configuration**: Extensive options for data transformation strategies

## Installation

```bash
pip install tabpfn-common-utils
```

Or with uv:
```bash
uv add tabpfn-common-utils
```

## Quick Start

### Telemetry (Privacy-Compliant)

```python
from tabpfn_common_utils.telemetry import ProductTelemetry

# Initialize telemetry service (anonymous, GDPR-compliant)
telemetry = ProductTelemetry()

# Track usage events (no personal data collected)
telemetry.capture(...)

# Telemetry can be disabled by setting environment variable
export TABPFN_DISABLE_TELEMETRY=1
```

### Regression Results

```python
from tabpfn_common_utils.regression_pred_result import RegressionPredictResult

# Handle regression prediction results
result = RegressionPredictResult({
    "mean": [1.2, 2.3, 3.4],
    "median": [1.1, 2.2, 3.3],
    "mode": [1.0, 2.0, 3.0],
    "quantile_0.25": [0.9, 1.9, 2.9],
    "quantile_0.75": [1.5, 2.5, 3.5]
})

# Convert to basic representation for serialization
basic_repr = RegressionPredictResult.to_basic_representation(result)
```

### Data Utilities

```python
from tabpfn_common_utils.utils import get_example_dataset, serialize_to_csv_formatted_bytes
import pandas as pd

# Load example dataset
X_train, X_test, y_train, y_test = get_example_dataset("iris")

# Serialize data to CSV bytes
csv_bytes = serialize_to_csv_formatted_bytes(X_train)
```

## Privacy & Compliance

This package implements **privacy-first telemetry** that:

- ✅ **GDPR Compliant**: No personal data collection
- ✅ **Anonymous Only**: No user identification or tracking
- ✅ **Aggregated Data**: Only statistical insights are collected
- ✅ **User Control**: Can be completely disabled
- ✅ **Transparent**: Open source code for full transparency

Telemetry data helps improve TabPFN but never compromises user privacy.

## Development

### Setup

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run tests
uv run pytest

# Type checking
uv run pyright

# Code formatting
uv run ruff check --fix
```

### Adding Dependencies

```bash
# Add runtime dependency
uv add <package_name>

# Add development dependency
uv add --group dev <package_name>
```

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure all code passes type checking and formatting requirements.

## Links

- [TabPFN Main Repository](https://github.com/priorlabs/tabpfn)
- [Documentation](https://github.com/priorlabs/tabpfn_common_utils)
- [Issues](https://github.com/priorlabs/tabpfn_common_utils/issues)