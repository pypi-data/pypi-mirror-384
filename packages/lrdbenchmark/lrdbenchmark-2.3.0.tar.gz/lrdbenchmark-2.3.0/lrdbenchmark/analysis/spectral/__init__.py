"""
Spectral analysis estimators for LRDBench.

This module provides various spectral estimators for analyzing long-range dependence
in time series data using frequency domain methods.
"""

# Import unified estimators
from .gph.gph_estimator_unified import GPHEstimator
from .periodogram.periodogram_estimator_unified import PeriodogramEstimator
from .whittle.whittle_estimator_unified import WhittleEstimator

__all__ = [
    "GPHEstimator",
    "PeriodogramEstimator",
    "WhittleEstimator",
]
