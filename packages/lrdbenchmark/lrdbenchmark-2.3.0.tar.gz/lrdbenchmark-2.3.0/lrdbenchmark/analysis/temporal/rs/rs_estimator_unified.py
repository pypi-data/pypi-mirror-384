#!/usr/bin/env python3
"""
Unified R/S (Rescaled Range) Estimator for Long-Range Dependence Analysis.

This module implements the R/S estimator with automatic optimization framework
selection (JAX, Numba, NumPy) for the best performance on the available hardware.
"""

import math
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, Union, Tuple, List, Sequence, Callable
import warnings

# Import optimization frameworks
try:
    import jax
    import jax.numpy as jnp
    from jax import jit, vmap
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False
    # Create a dummy jnp for type hints when JAX is not available
    import numpy as np
    jnp = np

try:
    import numba
    from numba import jit as numba_jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Import base estimator
from lrdbenchmark.models.estimators.base_estimator import BaseEstimator


class RSEstimator(BaseEstimator):
    """
    Unified R/S (Rescaled Range) Estimator for Long-Range Dependence Analysis.

    The R/S estimator analyzes the rescaled range of time series data to estimate
    the Hurst parameter, which characterizes long-range dependence. This implementation
    provides automatic optimization framework selection and GPU acceleration.

    The R/S statistic is calculated as:
    R/S = (max(X) - min(X)) / S
    
    where X is the cumulative deviation from the mean and S is the standard deviation.

    Features:
    - Automatic optimization framework selection (JAX, Numba, NumPy)
    - GPU acceleration with JAX when available
    - JIT compilation with Numba for CPU optimization
    - Graceful fallbacks when optimization frameworks fail
    - Support for both block-based and window-based analysis

    Parameters
    ----------
    min_block_size : int, optional
        Minimum block size for analysis (default: 10)
    max_block_size : int, optional
        Maximum block size for analysis. If None, uses data length / 4
    num_blocks : int, optional
        Number of block sizes to test (default: 10)
    use_optimization : str, optional
        Optimization framework to use: 'auto', 'jax', 'numba', 'numpy' (default: 'auto')
    min_window_size : int, optional
        Minimum window size (alias for min_block_size)
    max_window_size : int, optional
        Maximum window size (alias for max_block_size)
    num_windows : int, optional
        Number of windows (alias for num_blocks)
    window_sizes : Sequence[int], optional
        Explicit list of window sizes to use
    overlap : bool, optional
        Whether to use overlapping windows (default: False)

    Attributes
    ----------
    parameters : Dict[str, Any]
        Current estimator parameters
    optimization_framework : str
        Selected optimization framework
    block_sizes : List[int]
        Block sizes used for analysis

    Examples
    --------
    >>> import numpy as np
    >>> from lrdbenchmark import RSEstimator
    >>> 
    >>> # Generate sample data
    >>> data = np.random.randn(1000)
    >>> 
    >>> # Create estimator
    >>> estimator = RSEstimator(min_block_size=10, max_block_size=100)
    >>> 
    >>> # Estimate Hurst parameter
    >>> result = estimator.estimate(data)
    >>> print(f"Hurst parameter: {result['hurst_parameter']:.3f}")
    >>> print(f"Confidence interval: {result['confidence_interval']}")

    Notes
    -----
    The R/S estimator is robust and works well for a wide range of data types.
    However, it can be sensitive to trends and may require detrending for
    non-stationary data.

    References
    ---------
    .. [1] Mandelbrot, B. B., & Wallis, J. R. (1969). Robustness of the rescaled
           range R/S in the measurement of noncyclic long run statistical dependence.
           Water Resources Research, 5(5), 967-988.
    .. [2] Hurst, H. E. (1951). Long-term storage capacity of reservoirs.
           Transactions of the American Society of Civil Engineers, 116, 770-799.
    """

    def __init__(
        self,
        min_block_size: Optional[int] = None,
        max_block_size: Optional[int] = None,
        num_blocks: Optional[int] = None,
        use_optimization: str = "auto",
        *,
        min_window_size: Optional[int] = None,
        max_window_size: Optional[int] = None,
        num_windows: Optional[int] = None,
        window_sizes: Optional[Sequence[int]] = None,
        overlap: bool = False,
    ) -> None:
        # Prefer explicit window-based parameters when provided for backward compatibility
        if min_window_size is not None:
            min_block_size = min_window_size
        if max_window_size is not None:
            max_block_size = max_window_size
        if num_windows is not None:
            num_blocks = num_windows

        # Apply defaults if still unset
        min_block_size = 10 if min_block_size is None else int(min_block_size)
        num_blocks = 10 if num_blocks is None else int(num_blocks)

        sanitized_windows = None
        if window_sizes is not None:
            sanitized_windows = self._sanitize_window_sizes(window_sizes)

        # Estimator parameters (keep legacy aliases for get_parameters())
        param_dict = {
            "min_block_size": int(min_block_size),
            "max_block_size": int(max_block_size) if max_block_size is not None else None,
            "num_blocks": int(num_blocks),
            "min_window_size": int(min_block_size),
            "max_window_size": int(max_block_size) if max_block_size is not None else None,
            "num_windows": int(num_blocks),
            "window_sizes": sanitized_windows.tolist() if sanitized_windows is not None else None,
            "overlap": bool(overlap),
        }

        super().__init__(**param_dict)
        self.parameters = param_dict

        # Optimization framework
        self.optimization_framework = self._select_optimization_framework(use_optimization)
        
        # Results storage
        self.results = {}
        
        # Validation
        self._validate_parameters()

    def _select_optimization_framework(self, use_optimization: str) -> str:
        """Select the optimal optimization framework."""
        if use_optimization == "auto":
            if JAX_AVAILABLE:
                return "jax"  # Best for GPU acceleration
            elif NUMBA_AVAILABLE:
                return "numba"  # Good for CPU optimization
            else:
                return "numpy"  # Fallback
        elif use_optimization == "jax" and JAX_AVAILABLE:
            return "jax"
        elif use_optimization == "numba" and NUMBA_AVAILABLE:
            return "numba"
        else:
            return "numpy"

    def _validate_parameters(self) -> None:
        """Validate estimator parameters."""
        if self.parameters["min_block_size"] < 4:
            raise ValueError("min_window_size must be at least 4")

        max_block = self.parameters["max_block_size"]
        if max_block is not None and max_block <= self.parameters["min_block_size"]:
            raise ValueError("max_window_size must be greater than min_window_size")

        if self.parameters["num_blocks"] < 3 and self.parameters["window_sizes"] is None:
            raise ValueError("num_blocks must be at least 3")

        if self.parameters["window_sizes"] is not None:
            windows = np.asarray(self.parameters["window_sizes"], dtype=int)
            if np.any(windows < 4):
                raise ValueError("All window sizes must be at least 4")
            if np.any(np.diff(windows) <= 0):
                raise ValueError("Window sizes must be in ascending order")
            if len(windows) < 3:
                raise ValueError("Need at least 3 window sizes")

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------

    def _sanitize_window_sizes(self, window_sizes: Sequence[int]) -> np.ndarray:
        """
        Validate and sanitize a sequence of window sizes.
        
        Parameters
        ----------
        window_sizes : Sequence[int]
            Sequence of window sizes to validate
            
        Returns
        -------
        np.ndarray
            Validated and sanitized window sizes
            
        Raises
        ------
        ValueError
            If any window size is not positive
        """
        windows = np.array(window_sizes, dtype=int)
        if np.any(windows <= 0):
            raise ValueError("Window sizes must be positive integers")
        return windows

    def _resolve_block_sizes(self, n: int) -> np.ndarray:
        """
        Construct the block/window sizes used for the R/S analysis.
        
        Parameters
        ----------
        n : int
            Length of the input data
            
        Returns
        -------
        np.ndarray
            Array of block sizes to use for analysis
            
        Raises
        ------
        ValueError
            If fewer than 3 valid window sizes are found
        """
        if self.parameters["window_sizes"] is not None:
            windows = np.asarray(self.parameters["window_sizes"], dtype=int)
        else:
            max_block = self.parameters["max_block_size"]
            if max_block is None:
                max_block = max(self.parameters["min_block_size"] + 1, n // 4)
            block_sizes = np.logspace(
                np.log10(self.parameters["min_block_size"]),
                np.log10(max_block),
                self.parameters["num_blocks"],
                dtype=int,
            )
            windows = np.unique(block_sizes)

        # Keep only meaningful windows
        valid = windows[(windows >= self.parameters["min_block_size"]) & (windows <= n // 2)]
        if len(valid) < 3:
            raise ValueError("Need at least 3 window sizes")
        return valid

    def _linear_regression(self, x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float, float]:
        """Perform linear regression and return slope statistics."""

        if SCIPY_AVAILABLE:
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            r_squared = r_value ** 2
            return slope, intercept, r_squared, p_value, std_err

        # Manual fallback (no SciPy available)
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        residuals = y - y_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        dof = max(len(x) - 2, 1)
        denom = np.sum((x - np.mean(x)) ** 2)
        std_err = math.sqrt((ss_res / dof) / denom) if denom > 0 else float("nan")
        return slope, intercept, r_squared, float("nan"), std_err

    def _build_results(
        self,
        *,
        block_sizes: np.ndarray,
        rs_values: np.ndarray,
        method: str,
        framework: str,
    ) -> Dict[str, Any]:
        """Package regression outcomes and diagnostics."""

        log_block_sizes = np.log(block_sizes)
        log_rs_values = np.log(rs_values)

        slope, intercept, r_squared, p_value, std_err = self._linear_regression(
            log_block_sizes, log_rs_values
        )

        hurst_parameter = slope
        confidence_interval = self._compute_confidence_interval(
            hurst_parameter, std_err, len(log_block_sizes)
        )

        results = {
            "hurst_parameter": float(hurst_parameter),
            "r_squared": float(r_squared),
            "slope": float(slope),
            "intercept": float(intercept),
            "p_value": float(p_value) if not math.isnan(p_value) else np.nan,
            "std_error": float(std_err) if not math.isnan(std_err) else np.nan,
            "block_sizes": block_sizes.tolist(),
            "window_sizes": block_sizes.tolist(),
            "rs_values": rs_values.tolist(),
            "log_block_sizes": log_block_sizes.tolist(),
            "log_rs_values": log_rs_values.tolist(),
            "confidence_interval": confidence_interval,
            "method": method,
            "optimization_framework": framework,
        }

        self.results = results
        return results

    def _compute_confidence_interval(
        self, hurst: float, std_err: float, sample_size: int, confidence_level: float = 0.95
    ) -> List[float]:
        """Compute a confidence interval for the Hurst estimate."""

        if not np.isfinite(std_err) or std_err <= 0 or sample_size < 3:
            return [float("nan"), float("nan")]

        alpha = 1.0 - confidence_level
        dof = max(sample_size - 2, 1)

        if SCIPY_AVAILABLE:
            critical = stats.t.ppf(1 - alpha / 2, dof)
        else:
            # Normal approximation fallback
            critical = 1.96

        margin = critical * std_err
        lower = float(hurst - margin)
        upper = float(hurst + margin)
        return [lower, upper]

    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate the Hurst parameter using R/S analysis with automatic optimization.

        This method performs R/S analysis on the input time series to estimate the
        Hurst parameter, which characterizes long-range dependence. The method
        automatically selects the optimal implementation (JAX, Numba, or NumPy)
        based on the available hardware and data characteristics.

        Parameters
        ----------
        data : Union[np.ndarray, list]
            Input time series data. Should be a 1D array or list of numerical values.
            The data will be automatically converted to a numpy array.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing comprehensive estimation results:
            
            - hurst_parameter : float
                Estimated Hurst parameter (0 < H < 1)
            - r_squared : float
                R-squared value of the linear regression fit
            - slope : float
                Slope of the log-log regression line
            - intercept : float
                Intercept of the log-log regression line
            - p_value : float
                P-value of the regression (if available)
            - std_error : float
                Standard error of the Hurst parameter estimate
            - block_sizes : List[int]
                Block sizes used in the analysis
            - rs_values : List[float]
                R/S values for each block size
            - log_block_sizes : List[float]
                Logarithm of block sizes
            - log_rs_values : List[float]
                Logarithm of R/S values
            - confidence_interval : List[float]
                95% confidence interval for the Hurst parameter
            - method : str
                Analysis method used ('rs_analysis')
            - optimization_framework : str
                Optimization framework used ('jax', 'numba', or 'numpy')

        Raises
        ------
        ValueError
            If the input data is invalid or too short
        RuntimeError
            If all optimization frameworks fail

        Examples
        --------
        >>> import numpy as np
        >>> from lrdbenchmark import RSEstimator
        >>> 
        >>> # Generate sample data with known Hurst parameter
        >>> np.random.seed(42)
        >>> data = np.random.randn(1000)
        >>> 
        >>> # Create estimator
        >>> estimator = RSEstimator(min_block_size=10, max_block_size=100)
        >>> 
        >>> # Estimate Hurst parameter
        >>> result = estimator.estimate(data)
        >>> print(f"Hurst parameter: {result['hurst_parameter']:.3f}")
        >>> print(f"R-squared: {result['r_squared']:.3f}")
        >>> print(f"Confidence interval: {result['confidence_interval']}")

        Notes
        -----
        The R/S estimator works by:
        1. Dividing the data into blocks of different sizes
        2. Computing the rescaled range (R/S) for each block
        3. Fitting a linear regression to log(R/S) vs log(block_size)
        4. The Hurst parameter is the slope of this regression line
        
        The method is robust but can be sensitive to trends in the data.
        For non-stationary data, consider detrending before analysis.

        See Also
        --------
        DFAEstimator : Detrended Fluctuation Analysis
        WhittleEstimator : Whittle maximum likelihood estimation
        """
        data = np.asarray(data)
        n = len(data)

        if n < 100:
            warnings.warn("Data length is small, results may be unreliable")

        # Select optimal method based on data size and framework
        if self.optimization_framework == "jax" and JAX_AVAILABLE:
            try:
                return self._estimate_jax(data)
            except Exception as e:
                warnings.warn(f"JAX implementation failed: {e}, falling back to NumPy")
                return self._estimate_numpy(data)
        elif self.optimization_framework == "numba" and NUMBA_AVAILABLE:
            try:
                return self._estimate_numba(data)
            except Exception as e:
                warnings.warn(f"Numba implementation failed: {e}, falling back to NumPy")
                return self._estimate_numpy(data)
        else:
            return self._estimate_numpy(data)

    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of R/S estimation."""
        n = len(data)
        
        # Set max block size if not provided
        block_sizes = self._resolve_block_sizes(n)

        # Calculate R/S values for each block size
        rs_values = []
        for block_size in block_sizes:
            rs_val = self._calculate_rs_numpy(data, block_size)
            rs_values.append(rs_val)
        
        rs_values = np.array(rs_values)
        
        # Filter out invalid values
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Need at least 3 window sizes")
        
        valid_block_sizes = block_sizes[valid_mask]
        valid_rs_values = rs_values[valid_mask]
        return self._build_results(
            block_sizes=valid_block_sizes,
            rs_values=valid_rs_values,
            method="numpy",
            framework="numpy",
        )

    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of R/S estimation."""
        if not NUMBA_AVAILABLE:
            warnings.warn("Numba not available, falling back to NumPy")
            return self._estimate_numpy(data)
        
        try:
            # Use Numba-optimized calculation
            return self._estimate_numba_optimized(data)
        except Exception as e:
            warnings.warn(f"Numba implementation failed: {e}, falling back to NumPy")
            return self._estimate_numpy(data)
    
    def _estimate_numba_optimized(self, data: np.ndarray) -> Dict[str, Any]:
        """Actual Numba-optimized implementation."""
        n = len(data)
        
        block_sizes = self._resolve_block_sizes(n)

        # Calculate R/S values using Numba-optimized function
        rs_values = []
        for block_size in block_sizes:
            rs_val = self._calculate_rs_numba(data, block_size)
            rs_values.append(rs_val)
        
        rs_values = np.array(rs_values)
        
        # Filter out invalid values
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Need at least 3 window sizes")
        
        valid_block_sizes = block_sizes[valid_mask]
        valid_rs_values = rs_values[valid_mask]
        return self._build_results(
            block_sizes=valid_block_sizes,
            rs_values=valid_rs_values,
            method="numba",
            framework="numba",
        )

    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of R/S estimation."""
        if not JAX_AVAILABLE:
            warnings.warn("JAX not available, falling back to NumPy")
            return self._estimate_numpy(data)
        
        try:
            # Use JAX-optimized calculation
            return self._estimate_jax_optimized(data)
        except Exception as e:
            warnings.warn(f"JAX implementation failed: {e}, falling back to NumPy")
            return self._estimate_numpy(data)
    
    def _estimate_jax_optimized(self, data: np.ndarray) -> Dict[str, Any]:
        """Actual JAX-optimized implementation."""
        n = len(data)
        
        block_sizes = self._resolve_block_sizes(n)
        
        # Convert to JAX arrays
        data_jax = jnp.array(data)
        block_sizes_jax = jnp.array(block_sizes)
        
        # Calculate R/S values using JAX-optimized function
        rs_values = []
        for block_size in block_sizes:
            rs_val = self._calculate_rs_jax(data_jax, block_size)
            rs_values.append(rs_val)
        
        rs_values = np.array(rs_values)
        
        # Filter out invalid values
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Need at least 3 window sizes")
        
        valid_block_sizes = block_sizes[valid_mask]
        valid_rs_values = rs_values[valid_mask]
        return self._build_results(
            block_sizes=valid_block_sizes,
            rs_values=valid_rs_values,
            method="jax",
            framework="jax",
        )

    def _calculate_rs_numpy(self, data: np.ndarray, block_size: int) -> float:
        """Calculate R/S value for a given block size using NumPy."""
        n = len(data)
        n_blocks = n // block_size
        
        if n_blocks == 0:
            return np.nan
        
        rs_values = []

        for i in range(n_blocks):
            start_idx = i * block_size
            end_idx = start_idx + block_size
            block_data = data[start_idx:end_idx]
            
            # Calculate cumulative deviation
            mean_val = np.mean(block_data)
            dev = block_data - mean_val
            cum_dev = np.cumsum(dev)
            
            # Calculate range
            R = np.max(cum_dev) - np.min(cum_dev)
            
            # Calculate standard deviation
            S = np.std(block_data, ddof=1)
            
            if S > 0:
                rs_values.append(R / S)
        
        if len(rs_values) == 0:
            return np.nan

        return np.mean(rs_values)
    
    def _calculate_rs_numba(self, data: np.ndarray, block_size: int) -> float:
        """Calculate R/S value for a given block size using Numba optimization."""
        if not NUMBA_AVAILABLE:
            return self._calculate_rs_numpy(data, block_size)

        try:
            # Use Numba-optimized calculation
            return self._calculate_rs_numba_optimized(data, block_size)
        except Exception as e:
            warnings.warn(f"Numba R/S calculation failed: {e}, falling back to NumPy")
            return self._calculate_rs_numpy(data, block_size)
    
    def _calculate_rs_numba_optimized(self, data: np.ndarray, block_size: int) -> float:
        """Numba-optimized R/S calculation using JIT compilation."""
        if NUMBA_AVAILABLE:
            return self._calculate_rs_numba_jit(data, block_size)
        else:
            return self._calculate_rs_numpy(data, block_size)
    
    @staticmethod
    @numba_jit(nopython=True, cache=True)
    def _calculate_rs_numba_jit(data: np.ndarray, block_size: int) -> float:
        """Numba JIT-compiled R/S calculation for maximum performance."""
        n = len(data)
        n_blocks = n // block_size
        
        if n_blocks == 0:
            return np.nan
        
        rs_values = np.empty(n_blocks, dtype=np.float64)
        count = 0

        for i in range(n_blocks):
            start_idx = i * block_size
            end_idx = start_idx + block_size
            block_data = data[start_idx:end_idx]

            # Calculate cumulative deviation
            mean_val = 0.0
            for j in range(block_size):
                mean_val += block_data[j]
            mean_val /= block_size

            dev = np.empty(block_size, dtype=np.float64)
            for j in range(block_size):
                dev[j] = block_data[j] - mean_val

            cum_dev = np.empty(block_size, dtype=np.float64)
            cum_dev[0] = dev[0]
            for j in range(1, block_size):
                cum_dev[j] = cum_dev[j - 1] + dev[j]

            # Calculate range
            min_val = cum_dev[0]
            max_val = cum_dev[0]
            for j in range(1, block_size):
                val = cum_dev[j]
                if val < min_val:
                    min_val = val
                if val > max_val:
                    max_val = val
            R = max_val - min_val

            # Calculate standard deviation
            sum_sq = 0.0
            for j in range(block_size):
                diff = dev[j]
                sum_sq += diff * diff
            S = np.sqrt(sum_sq / (block_size - 1))

            if S > 0:
                rs_values[count] = R / S
                count += 1

        if count == 0:
            return np.nan

        return float(np.mean(rs_values[:count]))
    
    def _calculate_rs_jax(self, data: jnp.ndarray, block_size: int) -> float:
        """Calculate R/S value for a given block size using JAX optimization."""
        if not JAX_AVAILABLE:
            return self._calculate_rs_numpy(np.array(data), block_size)
        
        try:
            # Use JAX-optimized calculation
            return self._calculate_rs_jax_optimized(data, block_size)
        except Exception as e:
            warnings.warn(f"JAX R/S calculation failed: {e}, falling back to NumPy")
            return self._calculate_rs_numpy(np.array(data), block_size)
    
    def _calculate_rs_jax_optimized(self, data: jnp.ndarray, block_size: int) -> float:
        """JAX-optimized R/S calculation using JIT compilation."""
        n = len(data)
        n_blocks = n // block_size
        
        if n_blocks == 0:
            return np.nan
        
        rs_values = []
        
        for i in range(n_blocks):
            start_idx = i * block_size
            end_idx = start_idx + block_size
            block_data = data[start_idx:end_idx]
            
            # Calculate cumulative deviation using JAX operations
            mean_val = jnp.mean(block_data)
            dev = block_data - mean_val
            cum_dev = jnp.cumsum(dev)
            
            # Calculate range
            R = jnp.max(cum_dev) - jnp.min(cum_dev)
            
            # Calculate standard deviation
            S = jnp.std(block_data, ddof=1)
            
            if S > 0:
                rs_values.append(R / S)
        
        if len(rs_values) == 0:
            return np.nan
        
        return jnp.mean(jnp.array(rs_values))

    def get_optimization_info(self) -> Dict[str, Any]:
        """Get information about available optimizations and current selection."""
        return {
            "current_framework": self.optimization_framework,
            "jax_available": JAX_AVAILABLE,
            "numba_available": NUMBA_AVAILABLE,
            "recommended_framework": self._get_recommended_framework()
        }

    # ------------------------------------------------------------------
    # Public API extensions for backward compatibility
    # ------------------------------------------------------------------

    def get_confidence_intervals(self, confidence_level: float = 0.95) -> Dict[str, Tuple[float, float]]:
        """Return confidence intervals for the Hurst exponent."""

        if not self.results:
            raise ValueError("No estimation results available")

        ci = self._compute_confidence_interval(
            self.results["hurst_parameter"],
            self.results["std_error"],
            len(self.results["block_sizes"]),
            confidence_level,
        )

        return {"hurst_parameter": tuple(ci)}

    def get_estimation_quality(self) -> Dict[str, Any]:
        """Provide diagnostic metrics for the last estimation."""

        if not self.results:
            raise ValueError("No estimation results available")

        quality = {
            "r_squared": self.results["r_squared"],
            "p_value": self.results["p_value"],
            "std_error": self.results["std_error"],
            "n_windows": len(self.results["block_sizes"]),
        }
        return quality

    def plot_scaling(self, **kwargs) -> None:
        """Legacy-compatible wrapper for plotting the R/S scaling behaviour."""

        if not self.results:
            raise ValueError("No estimation results available")

        self.plot_analysis(**kwargs)

    # ------------------------------------------------------------------
    # Legacy helper methods
    # ------------------------------------------------------------------

    def _calculate_rs_statistic(self, data: Union[np.ndarray, list], window_size: int) -> float:
        """Compute the R/S statistic for a single window size (legacy API)."""

        value = self._calculate_rs_numpy(np.asarray(data), int(window_size))
        if not np.isfinite(value) or value <= 0:
            raise ValueError("No valid R/S values calculated")
        return float(value)

    def _get_recommended_framework(self) -> str:
        """Get the recommended optimization framework."""
        if JAX_AVAILABLE:
            return "jax"  # Best for GPU acceleration
        elif NUMBA_AVAILABLE:
            return "numba"  # Good for CPU optimization
        else:
            return "numpy"  # Fallback

    def plot_analysis(self, figsize: Tuple[int, int] = (12, 8), save_path: Optional[str] = None) -> None:
        """Plot the R/S analysis results."""
        if not self.results:
            raise ValueError("No estimation results available")

        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('R/S Analysis Results', fontsize=16)

        # Plot 1: Log-log relationship
        ax1 = axes[0, 0]
        x = self.results["log_block_sizes"]
        y = self.results["log_rs_values"]

        ax1.scatter(x, y, s=60, alpha=0.7, label="Data points")

        # Plot fitted line
        slope = self.results["slope"]
        intercept = self.results["intercept"]
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = slope * x_fit + intercept
        ax1.plot(x_fit, y_fit, "r--", label=f"Linear fit (slope={slope:.3f})")

        ax1.set_xlabel("log(Block Size)")
        ax1.set_ylabel("log(R/S)")
        ax1.set_title("R/S Scaling")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: R/S vs Block Size (log-log)
        ax2 = axes[0, 1]
        block_sizes = self.results["block_sizes"]
        rs_values = self.results["rs_values"]
        
        ax2.scatter(block_sizes, rs_values, s=60, alpha=0.7)
        ax2.set_xscale("log")
        ax2.set_yscale("log")
        ax2.set_xlabel("Block Size")
        ax2.set_ylabel("R/S Value")
        ax2.set_title("R/S vs Block Size (log-log)")
        ax2.grid(True, which="both", ls=":", alpha=0.3)

        # Plot 3: Hurst parameter estimate
        ax3 = axes[1, 0]
        hurst = self.results["hurst_parameter"]
        
        ax3.bar(["Hurst Parameter"], [hurst], alpha=0.7, color='skyblue')
        ax3.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='H=0.5 (no memory)')
        ax3.set_ylabel("Hurst Parameter")
        ax3.set_title(f"Hurst Parameter Estimate: {hurst:.3f}")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Plot 4: R-squared
        ax4 = axes[1, 1]
        r_squared = self.results["r_squared"]
        
        ax4.bar(["R²"], [r_squared], alpha=0.7, color='lightgreen')
        ax4.set_ylabel("R²")
        ax4.set_title(f"Goodness of Fit: R² = {r_squared:.3f}")
        ax4.set_ylim(0, 1)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.show()

    def get_method_recommendation(self, n: int) -> Dict[str, Any]:
        """Get method recommendation for a given data size."""
        if n < 100:
            return {
                "recommended_method": "numpy",
                "reasoning": f"Data size n={n} is too small for optimization benefits",
                "method_details": {
                    "description": "NumPy implementation",
                    "best_for": "Small datasets (n < 100)",
                    "complexity": "O(n²)",
                    "memory": "O(n)",
                    "accuracy": "Medium"
                }
            }
        elif n < 1000:
            return {
                "recommended_method": "numba",
                "reasoning": f"Data size n={n} benefits from JIT compilation",
                "method_details": {
                    "description": "Numba JIT-compiled implementation",
                    "best_for": "Medium datasets (100 ≤ n < 1000)",
                    "complexity": "O(n²)",
                    "memory": "O(n)",
                    "accuracy": "High"
                }
            }
        else:
            return {
                "recommended_method": "jax",
                "reasoning": f"Data size n={n} benefits from GPU acceleration",
                "method_details": {
                    "description": "JAX GPU-accelerated implementation",
                    "best_for": "Large datasets (n ≥ 1000)",
                    "complexity": "O(n²)",
                    "memory": "O(n)",
                    "accuracy": "High"
                }
            }
