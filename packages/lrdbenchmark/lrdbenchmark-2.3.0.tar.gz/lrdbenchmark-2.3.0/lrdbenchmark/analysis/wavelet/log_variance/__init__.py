"""
Wavelet Log Variance Analysis module.

This module provides wavelet log variance analysis for estimating the Hurst parameter
from time series data using wavelet decomposition with log-transformed variances.
"""

from .log_variance_estimator_unified import WaveletLogVarianceEstimator

__all__ = ["WaveletLogVarianceEstimator"]
