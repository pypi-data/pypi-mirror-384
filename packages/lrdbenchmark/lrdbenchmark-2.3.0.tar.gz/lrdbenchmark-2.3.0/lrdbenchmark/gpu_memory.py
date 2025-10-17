"""
GPU memory management utilities for LRDBenchmark.

This module provides comprehensive GPU memory management including
monitoring, cleanup, and batch size optimization.
"""

import numpy as np
import warnings
import gc
import time
from typing import Dict, Any, Optional, Union, List, Tuple
from contextlib import contextmanager


class GPUMemoryManager:
    """GPU memory management utilities."""
    
    def __init__(self):
        self._torch_available = None
        self._jax_available = None
    
    def _check_torch(self):
        """Check if PyTorch is available."""
        if self._torch_available is None:
            try:
                import torch
                self._torch_available = torch.cuda.is_available()
            except ImportError:
                self._torch_available = False
        return self._torch_available
    
    def _check_jax(self):
        """Check if JAX is available."""
        if self._jax_available is None:
            try:
                import jax
                self._jax_available = len(jax.devices()) > 0
            except ImportError:
                self._jax_available = False
        return self._jax_available
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get GPU memory information."""
        info = {
            'torch_available': False,
            'jax_available': False,
            'torch_memory_allocated': 0.0,
            'torch_memory_cached': 0.0,
            'torch_memory_free': 0.0,
            'torch_memory_total': 0.0
        }
        
        if self._check_torch():
            try:
                import torch
                info['torch_available'] = True
                info['torch_memory_allocated'] = torch.cuda.memory_allocated() / (1024**3)
                info['torch_memory_cached'] = torch.cuda.memory_reserved() / (1024**3)
                
                if torch.cuda.device_count() > 0:
                    props = torch.cuda.get_device_properties(0)
                    info['torch_memory_total'] = props.total_memory / (1024**3)
                    info['torch_memory_free'] = info['torch_memory_total'] - info['torch_memory_allocated']
            except Exception as e:
                warnings.warn(f"Error getting PyTorch memory info: {e}")
        
        if self._check_jax():
            info['jax_available'] = True
        
        return info
    
    def clear_cache(self):
        """Clear GPU memory cache."""
        if self._check_torch():
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception as e:
                warnings.warn(f"Error clearing PyTorch cache: {e}")
        
        if self._check_jax():
            try:
                import jax
                jax.clear_caches()
            except Exception as e:
                warnings.warn(f"Error clearing JAX cache: {e}")
        
        # Force garbage collection
        gc.collect()
    
    def suggest_batch_size(self, data_size: int, sequence_length: int, 
                          memory_usage_factor: float = 0.8) -> int:
        """Suggest optimal batch size based on available GPU memory."""
        if not self._check_torch():
            return min(32, data_size)
        
        try:
            import torch
            memory_info = self.get_memory_info()
            
            if memory_info['torch_memory_free'] > 0:
                # Rough estimation: 1GB can handle ~1000 samples of length 1000
                estimated_samples = int(memory_info['torch_memory_free'] * 1000 * memory_usage_factor)
                suggested = min(estimated_samples // sequence_length, data_size, 128)
                return max(1, suggested)
            else:
                return min(32, data_size)
        except Exception:
            return min(32, data_size)
    
    def monitor_memory(self, operation_name: str = "operation"):
        """Context manager for monitoring GPU memory usage."""
        return self._MemoryMonitor(self, operation_name)
    
    class _MemoryMonitor:
        """Context manager for memory monitoring."""
        
        def __init__(self, manager, operation_name):
            self.manager = manager
            self.operation_name = operation_name
            self.start_memory = None
        
        def __enter__(self):
            self.start_memory = self.manager.get_memory_info()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            end_memory = self.manager.get_memory_info()
            
            if self.start_memory and end_memory:
                memory_used = (end_memory['torch_memory_allocated'] - 
                             self.start_memory['torch_memory_allocated'])
                
                if memory_used > 0.1:  # More than 100MB
                    print(f"{self.operation_name} used {memory_used:.2f}GB GPU memory")


# Global GPU memory manager instance
_gpu_memory_manager = GPUMemoryManager()


@contextmanager
def gpu_memory_context(clear_before: bool = True, clear_after: bool = True):
    """Context manager for GPU memory management."""
    if clear_before:
        _gpu_memory_manager.clear_cache()
    
    try:
        yield _gpu_memory_manager
    finally:
        if clear_after:
            _gpu_memory_manager.clear_cache()


def get_gpu_memory_info() -> Dict[str, Any]:
    """Get GPU memory information."""
    return _gpu_memory_manager.get_memory_info()


def clear_gpu_cache():
    """Clear GPU memory cache."""
    _gpu_memory_manager.clear_cache()


def suggest_batch_size(data_size: int, sequence_length: int) -> int:
    """Suggest optimal batch size based on available GPU memory."""
    return _gpu_memory_manager.suggest_batch_size(data_size, sequence_length)


def monitor_gpu_memory(operation_name: str = "operation"):
    """Monitor GPU memory usage for an operation."""
    return _gpu_memory_manager.monitor_memory(operation_name)
