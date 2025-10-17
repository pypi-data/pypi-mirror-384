"""
Rescaled Range (R/S) Analysis subpackage.

Exposes the `RSEstimator` for estimating the Hurst parameter using
the classic R/S (Rescaled Range) method.
"""

from .rs_estimator_unified import RSEstimator

__all__ = ["RSEstimator"]
