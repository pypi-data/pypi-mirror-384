"""
Periodogram estimator subpackage.

Exposes the `PeriodogramEstimator` for estimating long-memory parameters
from the low-frequency slope of the power spectrum.
"""

from .periodogram_estimator_unified import PeriodogramEstimator

__all__ = ["PeriodogramEstimator"]
