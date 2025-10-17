"""
GPU utilities for LRDBenchmark.

This module provides GPU availability checking and memory management utilities.
"""

import warnings
from typing import Optional, Dict, Any


def is_available() -> bool:
    """
    Check if GPU acceleration is available.
    
    Returns
    -------
    bool
        True if GPU is available and working, False otherwise.
    """
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_device_info() -> Dict[str, Any]:
    """
    Get detailed GPU device information.
    
    Returns
    -------
    dict
        Dictionary containing GPU information including:
        - available: bool
        - device_count: int
        - device_name: str
        - memory_total: float (GB)
        - memory_allocated: float (GB)
        - memory_free: float (GB)
    """
    info = {
        'available': False,
        'device_count': 0,
        'device_name': None,
        'memory_total': 0.0,
        'memory_allocated': 0.0,
        'memory_free': 0.0
    }
    
    if not is_available():
        return info
    
    try:
        import torch
        
        info['available'] = True
        info['device_count'] = torch.cuda.device_count()
        
        if torch.cuda.device_count() > 0:
            info['device_name'] = torch.cuda.get_device_name(0)
            
            # Memory information
            memory_total = torch.cuda.get_device_properties(0).total_memory
            memory_allocated = torch.cuda.memory_allocated(0)
            memory_free = memory_total - memory_allocated
            
            info['memory_total'] = memory_total / (1024**3)  # Convert to GB
            info['memory_allocated'] = memory_allocated / (1024**3)
            info['memory_free'] = memory_free / (1024**3)
            
    except Exception as e:
        warnings.warn(f"Error getting GPU info: {e}")
    
    return info


def clear_cache() -> None:
    """
    Clear GPU memory cache.
    
    This function safely clears GPU memory cache if available.
    """
    if is_available():
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception as e:
            warnings.warn(f"Error clearing GPU cache: {e}")


def suggest_batch_size(data_size: int, sequence_length: int) -> int:
    """
    Suggest optimal batch size based on available GPU memory.
    
    Parameters
    ----------
    data_size : int
        Number of data points
    sequence_length : int
        Length of sequences
        
    Returns
    -------
    int
        Suggested batch size
    """
    if not is_available():
        return min(32, data_size)
    
    try:
        import torch
        
        # Get available memory
        memory_free = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)
        memory_free_gb = memory_free / (1024**3)
        
        # Rough estimation: 1GB can handle ~1000 samples of length 1000
        estimated_samples = int(memory_free_gb * 1000)
        
        # Conservative estimate
        suggested = min(estimated_samples // sequence_length, data_size, 128)
        
        return max(1, suggested)
        
    except Exception:
        return min(32, data_size)


def get_safe_device(use_gpu: bool = False) -> str:
    """
    Get a safe device string for PyTorch operations.
    
    Parameters
    ----------
    use_gpu : bool, default=False
        Whether to attempt GPU usage
        
    Returns
    -------
    str
        Device string ('cuda' or 'cpu')
    """
    if not use_gpu:
        return 'cpu'
    
    if not is_available():
        warnings.warn("GPU requested but not available, using CPU")
        return 'cpu'
    
    try:
        import torch
        # Test GPU with small operation
        test_tensor = torch.zeros(1).to('cuda')
        _ = test_tensor + 1
        _ = test_tensor.cpu()
        return 'cuda'
    except Exception as e:
        warnings.warn(f"GPU test failed: {e}, using CPU")
        return 'cpu'
