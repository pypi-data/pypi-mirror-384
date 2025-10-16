"""
PATX: Pattern eXtraction for time series data using B-splines.

This package provides tools for extracting B-spline patterns from time series data
using hyperparameter optimization with Hyperopt.
"""

from .core import feature_extraction, pattern_to_features
from .models import LightGBMModelWrapper

__version__ = "0.4.0"
__all__ = ["feature_extraction", "pattern_to_features", "LightGBMModelWrapper"]
