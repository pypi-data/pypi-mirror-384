"""
Robustness Module for LRDBenchmark

This module provides robust implementations and fallback mechanisms
for handling extreme values, heavy-tailed data, and hardware compatibility issues.
"""

from .robust_feature_extractor import RobustFeatureExtractor
from .adaptive_preprocessor import AdaptiveDataPreprocessor
from .robust_optimization_backend import RobustOptimizationBackend

__all__ = [
    "RobustFeatureExtractor",
    "AdaptiveDataPreprocessor", 
    "RobustOptimizationBackend"
]
