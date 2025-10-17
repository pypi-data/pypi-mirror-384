"""
Alpha-Stable Distribution Data Model Module.

This module provides the AlphaStableModel class for generating heavy-tailed
time series data using alpha-stable distributions.

Alpha-stable distributions are characterized by four parameters:
- α (stability): 0 < α ≤ 2, controls tail heaviness
- β (skewness): -1 ≤ β ≤ 1, controls asymmetry
- σ (scale): σ > 0, controls spread
- μ (location): Real number, controls center

The model supports multiple generation methods:
- Chambers-Mallows-Stuck (CMS): Most commonly used
- Nolan's Method: More numerically stable
- Series Representation: For specific parameter ranges
- Fourier Transform: For symmetric cases (β = 0)
"""

from .alpha_stable_model import AlphaStableModel

__all__ = ['AlphaStableModel']
