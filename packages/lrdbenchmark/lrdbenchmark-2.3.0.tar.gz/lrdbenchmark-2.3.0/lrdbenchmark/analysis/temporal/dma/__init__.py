"""
Detrended Moving Average (DMA) subpackage.

Exposes the `DMAEstimator` for estimating the Hurst parameter using
the Detrended Moving Average method.
"""

from .dma_estimator_unified import DMAEstimator

__all__ = ["DMAEstimator"]
