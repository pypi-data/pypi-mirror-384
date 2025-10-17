"""
Wavelet Whittle Analysis module.

This module provides wavelet Whittle analysis for estimating the Hurst parameter
from time series data using wavelet-based Whittle likelihood estimation.
"""

from .whittle_estimator_unified import WaveletWhittleEstimator

__all__ = ["WaveletWhittleEstimator"]
