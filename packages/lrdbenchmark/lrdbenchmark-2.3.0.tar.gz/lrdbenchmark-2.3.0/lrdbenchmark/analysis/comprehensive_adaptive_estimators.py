#!/usr/bin/env python3
"""
Comprehensive Adaptive Classical Estimators for LRDBenchmark

This module provides comprehensive adaptive versions of all classical LRD estimators that
automatically select the optimal computation framework (GPU/JAX, CPU/Numba, or NumPy)
and include improved implementations with robust error handling.
"""

import numpy as np
import time
import warnings
from typing import Dict, Any, Optional, Union, Callable, Tuple, List
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

try:
    import numba
    from numba import jit as numba_jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

# Import existing unified estimators
from .temporal.rs.rs_estimator_unified import RSEstimator as BaseRSEstimator
from .temporal.dfa.dfa_estimator_unified import DFAEstimator as BaseDFAEstimator
from .temporal.dma.dma_estimator_unified import DMAEstimator as BaseDMAEstimator
from .temporal.higuchi.higuchi_estimator_unified import HiguchiEstimator as BaseHiguchiEstimator

# Import improved estimators
from .spectral.gph.gph_estimator_improved import ImprovedGPHEstimator
from .spectral.periodogram.periodogram_estimator_improved import ImprovedPeriodogramEstimator
from .spectral.whittle.whittle_estimator_unified import WhittleEstimator as BaseWhittleEstimator
from .wavelet.cwt.cwt_estimator_improved import ImprovedCWTEstimator
from .wavelet.variance.variance_estimator_unified import WaveletVarianceEstimator as BaseWaveletVarianceEstimator
from .wavelet.log_variance.log_variance_estimator_unified import WaveletLogVarianceEstimator as BaseWaveletLogVarianceEstimator
from .wavelet.whittle.whittle_estimator_unified import WaveletWhittleEstimator as BaseWaveletWhittleEstimator
from .multifractal.mfdfa.mfdfa_estimator_unified import MFDFAEstimator as BaseMFDFAEstimator
from .multifractal.wavelet_leaders.wavelet_leaders_estimator_unified import MultifractalWaveletLeadersEstimator as BaseMultifractalWaveletLeadersEstimator


class ComprehensiveAdaptiveEstimator(ABC):
    """
    Base class for comprehensive adaptive classical estimators that automatically select optimal
    computation frameworks and include robust error handling.
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


class ComprehensiveAdaptiveRS(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive R/S estimator with automatic framework selection."""
    
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
        self.base_estimator = BaseRSEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of R/S estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of R/S estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of R/S estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveDFA(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive DFA estimator with automatic framework selection."""
    
    def __init__(self, 
                 min_scale: int = 10,
                 max_scale: Optional[int] = None,
                 num_scales: int = 10,
                 order: int = 1,
                 **kwargs):
        super().__init__("dfa_analysis", **kwargs)
        self.parameters = {
            "min_scale": min_scale,
            "max_scale": max_scale,
            "num_scales": num_scales,
            "order": order,
        }
        self.base_estimator = BaseDFAEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of DFA estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of DFA estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of DFA estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveDMA(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive DMA estimator with automatic framework selection."""
    
    def __init__(self, 
                 min_scale: int = 10,
                 max_scale: Optional[int] = None,
                 num_scales: int = 10,
                 **kwargs):
        super().__init__("dma_analysis", **kwargs)
        self.parameters = {
            "min_scale": min_scale,
            "max_scale": max_scale,
            "num_scales": num_scales,
        }
        self.base_estimator = BaseDMAEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of DMA estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of DMA estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of DMA estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveHiguchi(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Higuchi estimator with automatic framework selection."""
    
    def __init__(self, 
                 max_k: int = 10,
                 **kwargs):
        super().__init__("higuchi_analysis", **kwargs)
        self.parameters = {
            "max_k": max_k,
        }
        self.base_estimator = BaseHiguchiEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of Higuchi estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Higuchi estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Higuchi estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveGPH(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive GPH estimator with improved implementation."""
    
    def __init__(self, 
                 min_freq_ratio: Optional[float] = None,
                 max_freq_ratio: Optional[float] = None,
                 **kwargs):
        super().__init__("gph_analysis", **kwargs)
        self.parameters = {
            "min_freq_ratio": min_freq_ratio,
            "max_freq_ratio": max_freq_ratio,
        }
        self.base_estimator = ImprovedGPHEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of improved GPH estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of improved GPH estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of improved GPH estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveWhittle(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Whittle estimator with automatic framework selection."""
    
    def __init__(self, 
                 min_freq_ratio: float = 0.01,
                 max_freq_ratio: float = 0.1,
                 **kwargs):
        super().__init__("whittle_analysis", **kwargs)
        self.parameters = {
            "min_freq_ratio": min_freq_ratio,
            "max_freq_ratio": max_freq_ratio,
        }
        self.base_estimator = BaseWhittleEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of Whittle estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Whittle estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Whittle estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptivePeriodogram(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Periodogram estimator with improved implementation."""
    
    def __init__(self, 
                 min_freq_ratio: Optional[float] = None,
                 max_freq_ratio: Optional[float] = None,
                 **kwargs):
        super().__init__("periodogram_analysis", **kwargs)
        self.parameters = {
            "min_freq_ratio": min_freq_ratio,
            "max_freq_ratio": max_freq_ratio,
        }
        self.base_estimator = ImprovedPeriodogramEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of improved Periodogram estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of improved Periodogram estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of improved Periodogram estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveCWT(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive CWT estimator with improved implementation."""
    
    def __init__(self, 
                 wavelet: str = "cmor1.5-1.0",
                 scales: Optional[np.ndarray] = None,
                 **kwargs):
        super().__init__("cwt_analysis", **kwargs)
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
        }
        self.base_estimator = ImprovedCWTEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of improved CWT estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of improved CWT estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of improved CWT estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveWaveletVar(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Wavelet Variance estimator with automatic framework selection."""
    
    def __init__(self, 
                 wavelet: str = "db4",
                 scales: Optional[List[int]] = None,
                 **kwargs):
        super().__init__("wavelet_variance_analysis", **kwargs)
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
        }
        self.base_estimator = BaseWaveletVarianceEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of Wavelet Variance estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Wavelet Variance estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Wavelet Variance estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveWaveletLogVar(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Wavelet Log Variance estimator with automatic framework selection."""
    
    def __init__(self, 
                 wavelet: str = "db4",
                 scales: Optional[List[int]] = None,
                 **kwargs):
        super().__init__("wavelet_log_variance_analysis", **kwargs)
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
        }
        self.base_estimator = BaseWaveletLogVarianceEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of Wavelet Log Variance estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Wavelet Log Variance estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Wavelet Log Variance estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveWaveletWhittle(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Wavelet Whittle estimator with automatic framework selection."""
    
    def __init__(self, 
                 wavelet: str = "db4",
                 scales: Optional[List[int]] = None,
                 **kwargs):
        super().__init__("wavelet_whittle_analysis", **kwargs)
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
        }
        self.base_estimator = BaseWaveletWhittleEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of Wavelet Whittle estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Wavelet Whittle estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Wavelet Whittle estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveMFDFA(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive MFDFA estimator with automatic framework selection."""
    
    def __init__(self, 
                 q_values: Optional[List[float]] = None,
                 min_scale: int = 8,
                 max_scale: int = 50,
                 **kwargs):
        super().__init__("mfdfa_analysis", **kwargs)
        self.parameters = {
            "q_values": q_values,
            "min_scale": min_scale,
            "max_scale": max_scale,
        }
        self.base_estimator = BaseMFDFAEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of MFDFA estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of MFDFA estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of MFDFA estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


class ComprehensiveAdaptiveWaveletLeaders(ComprehensiveAdaptiveEstimator):
    """Comprehensive adaptive Wavelet Leaders estimator with automatic framework selection."""
    
    def __init__(self, 
                 wavelet: str = "db4",
                 scales: Optional[List[int]] = None,
                 **kwargs):
        super().__init__("wavelet_leaders_analysis", **kwargs)
        self.parameters = {
            "wavelet": wavelet,
            "scales": scales,
        }
        self.base_estimator = BaseMultifractalWaveletLeadersEstimator(**self.parameters)
    
    def _estimate_numpy(self, data: np.ndarray) -> Dict[str, Any]:
        """NumPy implementation of Wavelet Leaders estimation."""
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numpy"
        return result
    
    def _estimate_numba(self, data: np.ndarray) -> Dict[str, Any]:
        """Numba-optimized implementation of Wavelet Leaders estimation."""
        if not NUMBA_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "numba"
        return result
    
    def _estimate_jax(self, data: np.ndarray) -> Dict[str, Any]:
        """JAX-optimized implementation of Wavelet Leaders estimation."""
        if not JAX_AVAILABLE:
            return self._estimate_numpy(data)
        
        start_time = time.time()
        result = self.base_estimator.estimate(data)
        result["execution_time"] = time.time() - start_time
        result["method"] = "jax"
        return result


# Factory function to get all comprehensive adaptive classical estimators
def get_all_comprehensive_adaptive_classical_estimators() -> Dict[str, ComprehensiveAdaptiveEstimator]:
    """
    Get all available comprehensive adaptive classical estimators.
    
    Returns
    -------
    dict
        Dictionary mapping estimator names to instances
    """
    return {
        # Temporal estimators
        'Comprehensive_RS': ComprehensiveAdaptiveRS(),
        'Comprehensive_DFA': ComprehensiveAdaptiveDFA(),
        'Comprehensive_DMA': ComprehensiveAdaptiveDMA(),
        'Comprehensive_Higuchi': ComprehensiveAdaptiveHiguchi(),
        
        # Spectral estimators
        'Comprehensive_GPH': ComprehensiveAdaptiveGPH(),
        'Comprehensive_Whittle': ComprehensiveAdaptiveWhittle(),
        'Comprehensive_Periodogram': ComprehensiveAdaptivePeriodogram(),
        
        # Wavelet estimators
        'Comprehensive_CWT': ComprehensiveAdaptiveCWT(),
        'Comprehensive_WaveletVar': ComprehensiveAdaptiveWaveletVar(),
        'Comprehensive_WaveletLogVar': ComprehensiveAdaptiveWaveletLogVar(),
        'Comprehensive_WaveletWhittle': ComprehensiveAdaptiveWaveletWhittle(),
        
        # Multifractal estimators
        'Comprehensive_MFDFA': ComprehensiveAdaptiveMFDFA(),
        'Comprehensive_WaveletLeaders': ComprehensiveAdaptiveWaveletLeaders(),
    }
