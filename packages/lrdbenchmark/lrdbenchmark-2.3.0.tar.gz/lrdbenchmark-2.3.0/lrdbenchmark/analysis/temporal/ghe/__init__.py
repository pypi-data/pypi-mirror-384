"""
GHE (Generalized Hurst Exponent) Estimator Module.

This module provides the GHE estimator for analyzing the scaling properties
of time series data and estimating the generalized Hurst exponent.

Based on the paper:
"Typical Algorithms for Estimating Hurst Exponent of Time Sequence: A Data Analyst's Perspective"
by HONG-YAN ZHANG, ZHI-QIANG FENG, SI-YU FENG, AND YU ZHOU
IEEE ACCESS 2024, DOI: 10.1109/ACCESS.2024.3512542
"""

from .ghe_estimator_unified import GHEEstimator

__all__ = ['GHEEstimator']
