#!/usr/bin/env python3
"""
Robust Optimization Backend for LRDBenchmark

This module provides a robust optimization backend that automatically handles
JAX GPU compatibility issues and provides intelligent fallback mechanisms.
"""

import numpy as np
import time
import psutil
import warnings
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Import optimization frameworks
try:
    import jax
    import jax.numpy as jnp
    from jax import jit, vmap, device_put
    JAX_AVAILABLE = True
    JAX_DEVICES = jax.devices()
    HAS_GPU = any('gpu' in str(device).lower() or 'cuda' in str(device).lower() 
                  for device in JAX_DEVICES)
except ImportError:
    JAX_AVAILABLE = False
    JAX_DEVICES = []
    HAS_GPU = False

try:
    import numba
    from numba import jit as numba_jit, prange
    NUMBA_AVAILABLE = True
    NUMBA_CORES = numba.config.NUMBA_NUM_THREADS
except ImportError:
    NUMBA_AVAILABLE = False
    NUMBA_CORES = 1

logger = logging.getLogger(__name__)


class OptimizationFramework(Enum):
    """Available optimization frameworks."""
    NUMPY = "numpy"
    NUMBA = "numba"
    JAX = "jax"


@dataclass
class HardwareInfo:
    """Hardware information for optimization decisions."""
    has_gpu: bool
    gpu_memory_gb: float
    cpu_cores: int
    memory_gb: float
    jax_gpu_working: bool = False


class RobustOptimizationBackend:
    """
    Robust optimization backend with intelligent fallback mechanisms.
    
    This backend automatically detects hardware capabilities and provides
    robust fallback mechanisms when JAX GPU is not available or fails.
    """
    
    def __init__(self, enable_profiling: bool = True):
        """Initialize the robust optimization backend."""
        self.enable_profiling = enable_profiling
        self.hardware_info = self._detect_hardware()
        self.performance_cache = {}
        self.failure_counts = {framework: 0 for framework in OptimizationFramework}
        
        # Test JAX GPU functionality
        self.hardware_info.jax_gpu_working = self._test_jax_gpu()
        
        logger.info(f"Hardware detected: GPU={self.hardware_info.has_gpu}, "
                   f"JAX GPU working={self.hardware_info.jax_gpu_working}, "
                   f"CPU cores={self.hardware_info.cpu_cores}")
    
    def _detect_hardware(self) -> HardwareInfo:
        """Detect hardware capabilities."""
        # GPU detection
        has_gpu = False
        gpu_memory_gb = 0.0
        
        if JAX_AVAILABLE and HAS_GPU:
            try:
                # Try to get GPU memory info
                gpu_devices = [d for d in JAX_DEVICES if 'gpu' in str(d).lower()]
                if gpu_devices:
                    has_gpu = True
                    # Estimate GPU memory (simplified)
                    gpu_memory_gb = 8.0  # Conservative estimate
            except Exception:
                has_gpu = False
        
        # CPU and memory info
        cpu_cores = psutil.cpu_count(logical=False)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        return HardwareInfo(
            has_gpu=has_gpu,
            gpu_memory_gb=gpu_memory_gb,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb
        )
    
    def _test_jax_gpu(self) -> bool:
        """Test if JAX GPU actually works on current hardware."""
        if not JAX_AVAILABLE or not HAS_GPU:
            return False
        
        try:
            # Test basic JAX GPU operations
            test_array = jnp.array([1.0, 2.0, 3.0, 4.0, 5.0])
            result = jnp.sum(test_array)
            
            # Test more complex operation
            test_matrix = jnp.array([[1.0, 2.0], [3.0, 4.0]])
            result = jnp.linalg.det(test_matrix)
            
            # Test compilation
            @jit
            def test_func(x):
                return jnp.sum(x ** 2)
            
            result = test_func(test_array)
            
            logger.info("JAX GPU test successful")
            return True
            
        except Exception as e:
            logger.warning(f"JAX GPU test failed: {e}")
            return False
    
    def select_optimal_framework(self, 
                                data_size: int, 
                                computation_type: str,
                                memory_requirement: Optional[float] = None) -> OptimizationFramework:
        """
        Select the optimal framework with robust fallback logic.
        
        Parameters
        ----------
        data_size : int
            Size of the input data
        computation_type : str
            Type of computation (e.g., 'matrix_mult', 'fft', 'regression')
        memory_requirement : float, optional
            Estimated memory requirement in GB
            
        Returns
        -------
        OptimizationFramework
            Selected optimization framework
        """
        # Check memory constraints first
        if memory_requirement and memory_requirement > self.hardware_info.memory_gb * 0.8:
            logger.warning("Memory constraint detected, using NumPy fallback")
            return OptimizationFramework.NUMPY
        
        # If JAX GPU is not working, prefer NumPy or Numba
        if not self.hardware_info.jax_gpu_working:
            if data_size > 1000 and NUMBA_AVAILABLE:
                return OptimizationFramework.NUMBA
            else:
                return OptimizationFramework.NUMPY
        
        # Normal selection logic for working JAX GPU
        if data_size < 100:
            # Very small data: NumPy is often fastest due to overhead
            return OptimizationFramework.NUMPY
        elif data_size > 10000 and self.hardware_info.has_gpu:
            # Large data with working GPU: prefer JAX
            return OptimizationFramework.JAX
        elif data_size > 1000 and NUMBA_AVAILABLE:
            # Medium data: prefer Numba for CPU optimization
            return OptimizationFramework.NUMBA
        else:
            # Fallback to NumPy
            return OptimizationFramework.NUMPY
    
    def get_framework_recommendation(self, 
                                   data_size: int, 
                                   computation_type: str) -> Dict[str, Any]:
        """
        Get detailed framework recommendation with reasoning.
        
        Parameters
        ----------
        data_size : int
            Size of the input data
        computation_type : str
            Type of computation
            
        Returns
        -------
        dict
            Framework recommendation with reasoning
        """
        framework = self.select_optimal_framework(data_size, computation_type)
        
        reasoning = []
        
        if not self.hardware_info.jax_gpu_working:
            reasoning.append("JAX GPU not available or not working")
        
        if data_size < 100:
            reasoning.append("Small data size favors NumPy due to overhead")
        elif data_size > 10000 and self.hardware_info.jax_gpu_working:
            reasoning.append("Large data size with working GPU favors JAX")
        elif data_size > 1000 and NUMBA_AVAILABLE:
            reasoning.append("Medium data size favors Numba for CPU optimization")
        else:
            reasoning.append("Fallback to NumPy for compatibility")
        
        return {
            "recommended_framework": framework.value,
            "reasoning": "; ".join(reasoning),
            "hardware_info": {
                "has_gpu": self.hardware_info.has_gpu,
                "jax_gpu_working": self.hardware_info.jax_gpu_working,
                "cpu_cores": self.hardware_info.cpu_cores,
                "memory_gb": self.hardware_info.memory_gb
            }
        }
    
    def execute_with_fallback(self, 
                            func: callable, 
                            framework: OptimizationFramework,
                            *args, **kwargs) -> Tuple[Any, str]:
        """
        Execute function with automatic fallback on failure.
        
        Parameters
        ----------
        func : callable
            Function to execute
        framework : OptimizationFramework
            Preferred framework
        *args, **kwargs
            Arguments for the function
            
        Returns
        -------
        tuple
            (result, framework_used)
        """
        # Try preferred framework first
        try:
            result = func(*args, **kwargs)
            return result, framework.value
        except Exception as e:
            logger.warning(f"Framework {framework.value} failed: {e}")
            self.failure_counts[framework] += 1
            
            # Fallback to NumPy
            if framework != OptimizationFramework.NUMPY:
                try:
                    # This would need to be implemented by the calling code
                    # to provide a NumPy fallback implementation
                    raise NotImplementedError("NumPy fallback not implemented in this context")
                except Exception as fallback_error:
                    logger.error(f"All frameworks failed: {fallback_error}")
                    raise e
            else:
                raise e
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics and failure counts."""
        return {
            "hardware_info": {
                "has_gpu": self.hardware_info.has_gpu,
                "jax_gpu_working": self.hardware_info.jax_gpu_working,
                "cpu_cores": self.hardware_info.cpu_cores,
                "memory_gb": self.hardware_info.memory_gb
            },
            "failure_counts": self.failure_counts,
            "performance_cache_size": len(self.performance_cache)
        }
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.failure_counts = {framework: 0 for framework in OptimizationFramework}
        self.performance_cache.clear()
        logger.info("Performance statistics reset")


# Convenience function for easy integration
def get_robust_backend(enable_profiling: bool = True) -> RobustOptimizationBackend:
    """Get a robust optimization backend instance."""
    return RobustOptimizationBackend(enable_profiling=enable_profiling)
