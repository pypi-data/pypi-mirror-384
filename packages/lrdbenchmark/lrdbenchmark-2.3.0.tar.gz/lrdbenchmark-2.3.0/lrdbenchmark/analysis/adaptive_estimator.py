#!/usr/bin/env python3
"""
Adaptive Estimator Base Class for LRDBenchmark

This module provides a base class for estimators that automatically adapt
their computation framework based on the optimization backend system.
"""

import numpy as np
import time
import warnings
from typing import Dict, Any, Optional, Union, Callable, Tuple
from abc import ABC, abstractmethod

from .optimization_backend import (
    get_optimization_backend, 
    OptimizationFramework, 
    OptimizationBackend
)

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


class AdaptiveEstimator(ABC):
    """
    Base class for adaptive estimators that automatically select optimal
    computation frameworks based on data characteristics and hardware.
    """
    
    def __init__(self, 
                 estimator_name: str,
                 backend: Optional[OptimizationBackend] = None,
                 enable_profiling: bool = True):
        """
        Initialize the adaptive estimator.
        
        Parameters
        ----------
        estimator_name : str
            Name of the estimator
        backend : OptimizationBackend, optional
            Optimization backend to use. If None, uses global backend.
        enable_profiling : bool
            Whether to enable performance profiling
        """
        self.estimator_name = estimator_name
        self.backend = backend or get_optimization_backend()
        self.enable_profiling = enable_profiling
        self.parameters = {}
        self.results = {}
        
        # Performance tracking
        self.performance_history = []
        self.current_framework = None
        
    def estimate(self, data: Union[np.ndarray, list]) -> Dict[str, Any]:
        """
        Estimate parameters using the adaptive framework selection.
        
        Parameters
        ----------
        data : array-like
            Input time series data
            
        Returns
        -------
        dict
            Estimation results
        """
        data = np.asarray(data)
        n = len(data)
        
        # Get framework recommendation
        recommendation = self.backend.get_framework_recommendation(
            data_size=n, 
            computation_type=self.estimator_name
        )
        
        self.current_framework = OptimizationFramework(recommendation["recommended_framework"])
        
        # Select the appropriate implementation
        if self.current_framework == OptimizationFramework.JAX and JAX_AVAILABLE:
            try:
                result = self._estimate_jax(data)
                result["framework_used"] = "jax"
                result["framework_reasoning"] = recommendation["reasoning"]
            except Exception as e:
                warnings.warn(f"JAX implementation failed: {e}, falling back to NumPy")
                result = self._estimate_numpy(data)
                result["framework_used"] = "numpy_fallback"
                result["framework_reasoning"] = f"JAX failed: {str(e)}"
        elif self.current_framework == OptimizationFramework.NUMBA and NUMBA_AVAILABLE:
            try:
                result = self._estimate_numba(data)
                result["framework_used"] = "numba"
                result["framework_reasoning"] = recommendation["reasoning"]
            except Exception as e:
                warnings.warn(f"Numba implementation failed: {e}, falling back to NumPy")
                result = self._estimate_numpy(data)
                result["framework_used"] = "numpy_fallback"
                result["framework_reasoning"] = f"Numba failed: {str(e)}"
        else:
            result = self._estimate_numpy(data)
            result["framework_used"] = "numpy"
            result["framework_reasoning"] = recommendation["reasoning"]
        
        # Profile the computation if enabled
        if self.enable_profiling:
            self._profile_computation(data, result)
        
        # Store results
        self.results = result
        return result
    
    def _profile_computation(self, data: np.ndarray, result: Dict[str, Any]):
        """Profile the computation and update performance history."""
        if "execution_time" in result:
            profile = self.backend.profile_computation(
                func=lambda x: self._estimate_with_framework(x, self.current_framework),
                data=data,
                framework=self.current_framework,
                computation_type=self.estimator_name
            )
            self.performance_history.append(profile)
    
    def _estimate_with_framework(self, data: np.ndarray, framework: OptimizationFramework) -> Dict[str, Any]:
        """Estimate using a specific framework."""
        if framework == OptimizationFramework.JAX:
            return self._estimate_jax(data)
        elif framework == OptimizationFramework.NUMBA:
            return self._estimate_numba(data)
        else:
            return self._estimate_numpy(data)
    
    @abstractmethod
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of the estimator."""
        pass
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba implementation of the estimator."""
        # Default: fall back to NumPy implementation
        return self._estimate_numpy(data)
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX implementation of the estimator."""
        # Default: fall back to NumPy implementation
        return self._estimate_numpy(data)
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance information for this estimator."""
        if not self.performance_history:
            return {"message": "No performance data available"}
        
        frameworks_used = {}
        for profile in self.performance_history:
            framework = profile.framework.value
            if framework not in frameworks_used:
                frameworks_used[framework] = {
                    "count": 0,
                    "total_time": 0.0,
                    "success_rate": 0.0,
                    "avg_accuracy": 0.0
                }
            
            frameworks_used[framework]["count"] += 1
            frameworks_used[framework]["total_time"] += profile.execution_time
            if profile.success:
                frameworks_used[framework]["success_rate"] += 1
                frameworks_used[framework]["avg_accuracy"] += profile.accuracy
        
        # Calculate averages
        for framework in frameworks_used:
            count = frameworks_used[framework]["count"]
            frameworks_used[framework]["success_rate"] /= count
            frameworks_used[framework]["avg_accuracy"] /= count
            frameworks_used[framework]["avg_time"] = (
                frameworks_used[framework]["total_time"] / count
            )
        
        return {
            "estimator_name": self.estimator_name,
            "total_runs": len(self.performance_history),
            "frameworks_used": frameworks_used,
            "current_framework": self.current_framework.value if self.current_framework else None
        }
    
    def get_optimization_recommendation(self, data_size: int) -> Dict[str, Any]:
        """Get optimization recommendation for a given data size."""
        return self.backend.get_framework_recommendation(
            data_size=data_size,
            computation_type=self.estimator_name
        )


class AdaptiveRS(AdaptiveEstimator):
    """Adaptive R/S estimator with automatic framework selection."""
    
    def __init__(self, 
                 min_block_size: int = 10,
                 max_block_size: Optional[int] = None,
                 num_blocks: int = 10,
                 **kwargs):
        super().__init__("rs_analysis", **kwargs)
        self.parameters = {
            "min_block_size": min_block_size,
            "max_block_size": max_block_size,
            "num_blocks": num_blocks,
        }
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of R/S estimation."""
        n = len(data)
        
        # Set max block size if not provided
        if self.parameters["max_block_size"] is None:
            self.parameters["max_block_size"] = n // 4
        
        # Generate block sizes
        block_sizes = np.logspace(
            np.log10(self.parameters["min_block_size"]),
            np.log10(self.parameters["max_block_size"]),
            self.parameters["num_blocks"],
            dtype=int
        )
        
        # Ensure block sizes are unique and valid
        block_sizes = np.unique(block_sizes)
        block_sizes = block_sizes[block_sizes <= n // 2]
        
        if len(block_sizes) < 3:
            raise ValueError("Insufficient valid block sizes for analysis")
        
        # Calculate R/S values for each block size
        rs_values = []
        for block_size in block_sizes:
            rs_val = self._calculate_rs_numpy(data, block_size)
            rs_values.append(rs_val)
        
        rs_values = np.array(rs_values)
        
        # Filter out invalid values
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Insufficient valid R/S values for analysis")
        
        valid_block_sizes = block_sizes[valid_mask]
        valid_rs_values = rs_values[valid_mask]
        
        # Log-log regression
        log_block_sizes = np.log(valid_block_sizes)
        log_rs_values = np.log(valid_rs_values)
        
        # Linear regression
        coeffs = np.polyfit(log_block_sizes, log_rs_values, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        
        # Calculate R-squared
        y_pred = slope * log_block_sizes + intercept
        ss_res = np.sum((log_rs_values - y_pred) ** 2)
        ss_tot = np.sum((log_rs_values - np.mean(log_rs_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Hurst parameter is the slope
        hurst_parameter = slope
        
        return {
            "hurst_parameter": float(hurst_parameter),
            "r_squared": float(r_squared),
            "slope": float(slope),
            "intercept": float(intercept),
            "block_sizes": valid_block_sizes.tolist(),
            "rs_values": valid_rs_values.tolist(),
            "log_block_sizes": log_block_sizes.tolist(),
            "log_rs_values": log_rs_values.tolist(),
            "execution_time": 0.0,  # Will be measured by profiling
            "method": "numpy"
        }
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of R/S estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        # Use Numba-optimized calculation
        n = len(data)
        
        # Set max block size if not provided
        if self.parameters["max_block_size"] is None:
            self.parameters["max_block_size"] = n // 4
        
        # Generate block sizes
        block_sizes = np.logspace(
            np.log10(self.parameters["min_block_size"]),
            np.log10(self.parameters["max_block_size"]),
            self.parameters["num_blocks"],
            dtype=int
        )
        
        # Ensure block sizes are unique and valid
        block_sizes = np.unique(block_sizes)
        block_sizes = block_sizes[block_sizes <= n // 2]
        
        if len(block_sizes) < 3:
            raise ValueError("Insufficient valid block sizes for analysis")
        
        # Calculate R/S values using Numba-optimized function
        rs_values = []
        for block_size in block_sizes:
            rs_val = self._calculate_rs_numba(data, block_size)
            rs_values.append(rs_val)
        
        rs_values = np.array(rs_values)
        
        # Filter out invalid values
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Insufficient valid R/S values for analysis")
        
        valid_block_sizes = block_sizes[valid_mask]
        valid_rs_values = rs_values[valid_mask]
        
        # Log-log regression
        log_block_sizes = np.log(valid_block_sizes)
        log_rs_values = np.log(valid_rs_values)
        
        # Linear regression
        coeffs = np.polyfit(log_block_sizes, log_rs_values, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        
        # Calculate R-squared
        y_pred = slope * log_block_sizes + intercept
        ss_res = np.sum((log_rs_values - y_pred) ** 2)
        ss_tot = np.sum((log_rs_values - np.mean(log_rs_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Hurst parameter is the slope
        hurst_parameter = slope
        
        return {
            "hurst_parameter": float(hurst_parameter),
            "r_squared": float(r_squared),
            "slope": float(slope),
            "intercept": float(intercept),
            "block_sizes": valid_block_sizes.tolist(),
            "rs_values": valid_rs_values.tolist(),
            "log_block_sizes": log_block_sizes.tolist(),
            "log_rs_values": log_rs_values.tolist(),
            "execution_time": 0.0,
            "method": "numba"
        }
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of R/S estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        # Convert to JAX arrays
        data_jax = jnp.array(data)
        
        # Use JAX-optimized calculation
        n = len(data)
        
        # Set max block size if not provided
        if self.parameters["max_block_size"] is None:
            self.parameters["max_block_size"] = n // 4
        
        # Generate block sizes
        block_sizes = np.logspace(
            np.log10(self.parameters["min_block_size"]),
            np.log10(self.parameters["max_block_size"]),
            self.parameters["num_blocks"],
            dtype=int
        )
        
        # Ensure block sizes are unique and valid
        block_sizes = np.unique(block_sizes)
        block_sizes = block_sizes[block_sizes <= n // 2]
        
        if len(block_sizes) < 3:
            raise ValueError("Insufficient valid block sizes for analysis")
        
        # Calculate R/S values using JAX-optimized function
        rs_values = []
        for block_size in block_sizes:
            rs_val = self._calculate_rs_jax(data_jax, block_size)
            rs_values.append(rs_val)
        
        rs_values = np.array(rs_values)
        
        # Filter out invalid values
        valid_mask = (rs_values > 0) & ~np.isnan(rs_values)
        if np.sum(valid_mask) < 3:
            raise ValueError("Insufficient valid R/S values for analysis")
        
        valid_block_sizes = block_sizes[valid_mask]
        valid_rs_values = rs_values[valid_mask]
        
        # Log-log regression
        log_block_sizes = np.log(valid_block_sizes)
        log_rs_values = np.log(valid_rs_values)
        
        # Linear regression
        coeffs = np.polyfit(log_block_sizes, log_rs_values, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        
        # Calculate R-squared
        y_pred = slope * log_block_sizes + intercept
        ss_res = np.sum((log_rs_values - y_pred) ** 2)
        ss_tot = np.sum((log_rs_values - np.mean(log_rs_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Hurst parameter is the slope
        hurst_parameter = slope
        
        return {
            "hurst_parameter": float(hurst_parameter),
            "r_squared": float(r_squared),
            "slope": float(slope),
            "intercept": float(intercept),
            "block_sizes": valid_block_sizes.tolist(),
            "rs_values": valid_rs_values.tolist(),
            "log_block_sizes": log_block_sizes.tolist(),
            "log_rs_values": log_rs_values.tolist(),
            "execution_time": 0.0,
            "method": "jax"
        }
    
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
        
        return self._numba_calculate_rs(data, block_size)
    
    def _calculate_rs_jax(self, data: jnp.ndarray, block_size: int) -> float:
        """Calculate R/S value for a given block size using JAX optimization."""
        if not JAX_AVAILABLE:
            return self._calculate_rs_numpy(np.array(data), block_size)
        
        n = len(data)
        n_blocks = n // block_size
        
        if n_blocks == 0:
            return float(jnp.nan)
        
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
            return float(jnp.nan)
        
        return float(jnp.mean(jnp.array(rs_values)))
    
    @staticmethod
    @numba_jit(nopython=True, cache=True)
    def _numba_calculate_rs(data: np.ndarray, block_size: int) -> float:
        """Numba JIT-compiled R/S calculation for maximum performance."""
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
            mean_val = 0.0
            for j in range(block_size):
                mean_val += block_data[j]
            mean_val /= block_size
            
            dev = np.zeros(block_size)
            for j in range(block_size):
                dev[j] = block_data[j] - mean_val
            
            cum_dev = np.zeros(block_size)
            cum_dev[0] = dev[0]
            for j in range(1, block_size):
                cum_dev[j] = cum_dev[j-1] + dev[j]
            
            # Calculate range
            min_val = cum_dev[0]
            max_val = cum_dev[0]
            for j in range(1, block_size):
                if cum_dev[j] < min_val:
                    min_val = cum_dev[j]
                if cum_dev[j] > max_val:
                    max_val = cum_dev[j]
            R = max_val - min_val
            
            # Calculate standard deviation
            sum_sq = 0.0
            for j in range(block_size):
                diff = dev[j]
                sum_sq += diff * diff
            S = np.sqrt(sum_sq / (block_size - 1))
            
            if S > 0:
                rs_values.append(R / S)
        
        if len(rs_values) == 0:
            return np.nan
        
        # Calculate mean
        total = 0.0
        for val in rs_values:
            total += val
        return total / len(rs_values)
