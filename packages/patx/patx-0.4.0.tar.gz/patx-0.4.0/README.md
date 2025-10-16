# PatX - Pattern eXtraction for Time Series Feature Engineering

[![PyPI version](https://badge.fury.io/py/patx.svg)](https://badge.fury.io/py/patx)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PatX is a Python package for extracting B-spline patterns from time series data to create features for machine learning models. 
It uses Optuna optimization to automatically find patterns that work best for your target variable.

**Key Features:**
- Automatic pattern extraction using B-spline curves with 5 control points
- Support for both univariate and multivariate time series
- Flexible input formats (Pandas DataFrames or NumPy arrays)
- Built-in support for classification and regression tasks
- Optuna-based optimization for pattern discovery
- Compatible with any scikit-learn compatible model
- Advanced time series transformations (wavelets, FFT, derivatives)
- Shift-tolerant pattern matching with numba acceleration

## Installation

```bash
pip install patx
```

## Quick Start

### Univariate Time Series (Single Input Series)

For a single time series dataset:

```python
import numpy as np
import pandas as pd
from patx import feature_extraction
from patx.data import load_remc_data
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

# Load the included REMC dataset
data = load_remc_data(series=("H3K4me3",))
input_series = data['X_list'][0]  # Single array
y = data['y']

print(f"Samples: {len(y)}, time points: {input_series.shape[1]}")  # (1841, 40)

# Split data
indices = np.arange(len(y))
train_indices, test_indices = train_test_split(
    indices, test_size=0.2, random_state=42, stratify=y
)

# Option 1: Pandas DataFrame (recommended)
input_series_train = pd.DataFrame(input_series[train_indices])
input_series_test = pd.DataFrame(input_series[test_indices])

# Option 2: NumPy array (also works)
# input_series_train = input_series[train_indices]
# input_series_test = input_series[test_indices]

y_train, y_test = pd.Series(y[train_indices]), y[test_indices]

# Extract patterns and train model
result = feature_extraction(
    input_series_train=input_series_train, 
    y_train=y_train, 
    input_series_test=input_series_test, 
    n_trials=100, 
    shift_tolerance=2,
    show_progress=False
)

# Get results
test_probabilities = result['model'].predict_proba(result['test_features'])
auc_score = roc_auc_score(y_test, test_probabilities)

print(f"Univariate: {len(result['patterns'])} patterns, AUC={auc_score:.4f}")
print(f"Features shape: {result['train_features'].shape}")
```

### Multivariate Time Series (Multiple Input Series)

For multiple time series datasets:

```python
from patx import feature_extraction
from patx.data import load_remc_data

# Load multiple input series
data = load_remc_data(series=("H3K4me3", "H3K4me1"))
input_series = data['X_list']  # List of arrays
y = data['y']
series_names = data['series_names']

print(f"Loaded {len(input_series)} input series: {series_names}")

# Split data
indices = np.arange(len(y))
train_indices, test_indices = train_test_split(
    indices, test_size=0.2, random_state=42, stratify=y
)

# Option 1: List of Pandas DataFrames (recommended)
input_series_train = [pd.DataFrame(X[train_indices]) for X in input_series]
input_series_test = [pd.DataFrame(X[test_indices]) for X in input_series]

# Option 2: List of NumPy arrays (also works)
# input_series_train = [X[train_indices] for X in input_series]
# input_series_test = [X[test_indices] for X in input_series]

y_train, y_test = y[train_indices], y[test_indices]

# Extract patterns from multiple input series
result = feature_extraction(
    input_series_train=input_series_train, 
    y_train=y_train, 
    input_series_test=input_series_test, 
    n_trials=100, 
    shift_tolerance=2,
    show_progress=False
)

test_probabilities = result['model'].predict_proba(result['test_features'])
auc_score = roc_auc_score(y_test, test_probabilities)

print(f"Multivariate: {len(result['patterns'])} patterns, AUC={auc_score:.4f}")
print(f"Pattern series indices: {[p['series_idx'] for p in result['patterns']]}")
print(f"Features shape: {result['train_features'].shape}")
```

### Using Initial Features

When you have additional features to include alongside pattern features:

```python
# Create some initial features (e.g., statistical features)
def create_statistical_features(X):
    return np.column_stack([
        np.mean(X, axis=1),      # Mean
        np.std(X, axis=1),       # Standard deviation
        np.max(X, axis=1),       # Maximum
        np.min(X, axis=1),       # Minimum
    ])

# Generate initial features for train and test
initial_features_train = create_statistical_features(input_series_train)
initial_features_test = create_statistical_features(input_series_test)

# Pass initial features to feature_extraction
result = feature_extraction(
    input_series_train=input_series_train, 
    y_train=y_train, 
    input_series_test=input_series_test,
    initial_features=(initial_features_train, initial_features_test),
    n_trials=100,
    shift_tolerance=2,
    show_progress=False
)

print(f"With initial features: {len(result['patterns'])} patterns")
print(f"Total features shape: {result['train_features'].shape}")  # Includes initial + pattern features
```


## Input Data Types

PatX supports multiple input data formats:

### Univariate Input (Single Time Series)

```python
import pandas as pd
import numpy as np
from patx import feature_extraction

# Your time series data (samples × time_points)
your_data = np.random.randn(1000, 50)  # 1000 samples, 50 time points
your_test_data = np.random.randn(200, 50)
y_train = np.random.randint(0, 2, 1000)  # Example target

# Option 1: Pandas DataFrame (recommended)
input_series_train = pd.DataFrame(your_data)
input_series_test = pd.DataFrame(your_test_data)

# Option 2: NumPy array (also works)
# input_series_train = your_data
# input_series_test = your_test_data

result = feature_extraction(
    input_series_train=input_series_train,
    y_train=y_train,
    input_series_test=input_series_test,
    n_trials=100,
    shift_tolerance=2
)
```

### Multivariate Input (Multiple Time Series)

```python
# Multiple time series data
series1 = np.random.randn(1000, 50)  # First time series
series2 = np.random.randn(1000, 50)  # Second time series
series3 = np.random.randn(1000, 50)  # Third time series

# Option 1: List of Pandas DataFrames (recommended)
input_series_train = [
    pd.DataFrame(series1[train_indices]),
    pd.DataFrame(series2[train_indices]),
    pd.DataFrame(series3[train_indices])
]
input_series_test = [
    pd.DataFrame(series1[test_indices]),
    pd.DataFrame(series2[test_indices]),
    pd.DataFrame(series3[test_indices])
]

# Option 2: List of NumPy arrays (also works)
# input_series_train = [series1[train_indices], series2[train_indices], series3[train_indices]]
# input_series_test = [series1[test_indices], series2[test_indices], series3[test_indices]]

result = feature_extraction(
    input_series_train=input_series_train, 
    y_train=y_train, 
    input_series_test=input_series_test, 
    n_trials=100,
    shift_tolerance=2
)

# Check which series each pattern came from
print(f"Pattern series indices: {[p['series_idx'] for p in result['patterns']]}")
```

## Pattern Generation

PatX uses B-spline pattern generation with 5 control points. The control points are distributed evenly across the time axis, and only their y-values are optimized to find patterns that work best for your target variable. 

### Shift Tolerance

The `shift_tolerance` parameter allows patterns to be more flexible by searching for the best match within a specified range around the starting position. This is useful when patterns might appear slightly shifted in different samples.

### Pattern Modes

PatX supports two pattern modes:
- **Relative mode**: Control points are normalized between 0 and 1, scaled relative to data range
- **Absolute mode**: Control points use absolute values within the data range

### Time Series Transformations

PatX automatically applies various transformations to your time series data to find the most effective patterns:

- **Raw**: Original time series data
- **Wavelet (db4, level 3/4)**: Wavelet decomposition using Daubechies-4 wavelets
- **FFT Magnitude**: Frequency domain magnitude spectrum
- **FFT Power**: Power spectral density
- **Derivative**: First derivative of the time series

The optimization process automatically selects the best transformation type for each pattern.

## Complete Examples

### Example 1: Univariate with NumPy Arrays

```python
import numpy as np
from patx import feature_extraction

# Generate sample data
np.random.seed(42)
X_train = np.random.randn(1000, 30)  # 1000 samples, 30 time points
X_test = np.random.randn(200, 30)
y_train = np.random.randint(0, 2, 1000)  # Binary classification
y_test = np.random.randint(0, 2, 200)

# Use NumPy arrays directly
result = feature_extraction(
    input_series_train=X_train,
    y_train=y_train,
    input_series_test=X_test,
    n_trials=50,
    shift_tolerance=1,
    show_progress=False
)

print(f"Found {len(result['patterns'])} patterns")
print(f"Pattern control points: {result['patterns'][0]['control_points']}")
print(f"Transform types: {[p['transform_type'] for p in result['patterns']]}")
```

### Example 2: Multivariate with Mixed Data Types

```python
import pandas as pd
import numpy as np
from patx import feature_extraction

# Multiple time series with different data types
series1 = np.random.randn(1000, 25)  # NumPy array
series2 = np.random.randn(1000, 25)  # NumPy array
series3 = np.random.randn(1000, 25)  # NumPy array

# Mix of DataFrames and arrays
input_series_train = [
    pd.DataFrame(series1),  # DataFrame
    series2,                # NumPy array
    pd.DataFrame(series3)   # DataFrame
]

input_series_test = [
    pd.DataFrame(series1[800:]),  # DataFrame
    series2[800:],                # NumPy array
    pd.DataFrame(series3[800:])   # DataFrame
]

result = feature_extraction(
    input_series_train=input_series_train,
    y_train=y_train,
    input_series_test=input_series_test,
    n_trials=100,
    shift_tolerance=2
)

print(f"Pattern series indices: {[p['series_idx'] for p in result['patterns']]}")
print(f"Pattern widths: {[p['width'] for p in result['patterns']]}")
print(f"Transform types: {[p['transform_type'] for p in result['patterns']]}")
```

### Example 3: With Custom Initial Features

```python
from patx import feature_extraction
from sklearn.preprocessing import StandardScaler

# Create custom initial features
def create_domain_features(X):
    """Create domain-specific features"""
    return np.column_stack([
        np.mean(X, axis=1),           # Mean
        np.std(X, axis=1),            # Standard deviation
        np.max(X, axis=1),            # Maximum
        np.min(X, axis=1),            # Minimum
        np.argmax(X, axis=1),         # Index of maximum
        np.argmin(X, axis=1),         # Index of minimum
        np.sum(X > 0, axis=1),        # Count of positive values
        np.sum(X < 0, axis=1),        # Count of negative values
    ])

# Generate initial features
initial_train = create_domain_features(input_series_train)
initial_test = create_domain_features(input_series_test)

# Normalize initial features
scaler = StandardScaler()
initial_train = scaler.fit_transform(initial_train)
initial_test = scaler.transform(initial_test)

# Extract patterns with initial features
result = feature_extraction(
    input_series_train=input_series_train,
    y_train=y_train,
    input_series_test=input_series_test,
    initial_features=(initial_train, initial_test),
    n_trials=150,
    shift_tolerance=3,
    show_progress=True
)

print(f"Total features: {result['train_features'].shape[1]}")
print(f"Initial features: {initial_train.shape[1]}")
print(f"Pattern features: {result['train_features'].shape[1] - initial_train.shape[1]}")
```

### Example 4: Regression Task

```python
# For regression tasks, PatX automatically detects the metric
y_train_reg = np.random.randn(1000)  # Continuous target
y_test_reg = np.random.randn(200)

result_reg = feature_extraction(
    input_series_train=input_series_train,
    y_train=y_train_reg,
    input_series_test=input_series_test,
    n_trials=100,
    shift_tolerance=1
)

# Get predictions
predictions = result_reg['model'].predict(result_reg['test_features'])
print(f"Regression RMSE: {np.sqrt(np.mean((y_test_reg - predictions)**2)):.4f}")
```

## API Reference

### pattern_to_features

Convert input data to feature values using pattern parameters with optional shift tolerance.

**Parameters:**
- `input_series`: 3D NumPy array (samples × series × time_points)
- `pattern_width`: Width of the pattern region
- `pattern_start`: Starting index of the pattern region
- `series_index`: Index of the input series to use (default: 0)
- `shift_tolerance`: Allow pattern to shift within this range to find best match (default: 0)
- `control_points`: List of control point values for B-spline generation (optional if pattern provided)
- `pattern`: Pre-computed B-spline pattern array (optional if control_points provided)

**Returns:**
- NumPy array of feature values (minimum RMSE between pattern and data across shift range, one per sample)

**Example:**
```python
from patx import pattern_to_features

control_points = [0.2, 0.5, 0.8, 0.3, 0.1]
features = pattern_to_features(
    input_series=X_train,
    pattern_width=20,
    pattern_start=5,
    series_index=0,
    shift_tolerance=3,
    control_points=control_points
)
```

### feature_extraction

The main function for extracting patterns from input series data.

**Parameters:**
- `input_series_train`: Training input series data (DataFrame/array for univariate, list of DataFrames/arrays for multivariate)
- `y_train`: Training targets (Series or array)
- `input_series_test`: Test input series data (same structure as `input_series_train`)
- `initial_features`: Optional initial features (array or tuple of train/test arrays)
- `model`: Optional model instance (defaults to LightGBM based on task)
- `metric`: Optional; defaults to 'auc' if None, supports 'auc', 'accuracy', 'rmse'
- `val_size`: Optional validation split ratio (default: 0.2)
- `n_trials`: Maximum number of optimization trials (default: 300)
- `n_control_points`: Number of B-spline control points (default: 5)
- `shift_tolerance`: Allow patterns to shift within this range to find best match (default: 0)
- `show_progress`: Show progress bar (default: True)

**Returns:**
A dictionary containing:
- `patterns`: list of pattern dictionaries, each containing:
  - `pattern`: B-spline pattern array
  - `start`: start index
  - `width`: pattern width
  - `series_idx`: input series index (for multivariate)
  - `control_points`: B-spline control points
  - `shift_tolerance`: shift tolerance used for this pattern
  - `pattern_mode`: pattern mode ('relative' or 'absolute')
  - `transform_type`: transformation type used ('raw', 'wavelet_db4_level3', 'wavelet_db4_level4', 'fft_magnitude', 'fft_power', 'derivative')
- `train_features`: training feature matrix for the ML model
- `test_features`: test feature matrix for the ML model
- `model`: the trained model

### Data

- `load_remc_data(series)`: Load the included REMC epigenomics dataset (multiple input series)
  - `series`: tuple of series names to load (default: `("H3K4me3", "H3K4me1")`)
  - Returns dictionary with `X_list`, `y`, `X`, and `series_names`

### Custom Models

You can use any model that has `fit()`, `predict()`, and `predict_proba()` methods. Here's an example with sklearn:

**Sklearn Classifier Example:**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.base import clone

class SklearnClassifierWrapper:
    def __init__(self, sklearn_model):
        self.sklearn_model = sklearn_model
    
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        self.sklearn_model.fit(X_train, y_train)
        return self
    
    def predict(self, X):
        return self.sklearn_model.predict(X)
    
    def predict_proba(self, X):
        return self.sklearn_model.predict_proba(X)
    
    def clone(self):
        return SklearnClassifierWrapper(clone(self.sklearn_model))

# Use custom model
model = SklearnClassifierWrapper(LogisticRegression())
result = feature_extraction(input_series_train, y_train, input_series_test, model=model)
```

This wrapper works with any sklearn classifier (RandomForest, SVM, etc.).

## Citation

If you use PatX in your research, please cite:

```bibtex
@software{patx,
  title={PatX: Pattern eXtraction for Time Series Feature Engineering},
  author={Wolber, J.},
  year={2025},
  url={https://github.com/Prgrmmrjns/patX}
}
```