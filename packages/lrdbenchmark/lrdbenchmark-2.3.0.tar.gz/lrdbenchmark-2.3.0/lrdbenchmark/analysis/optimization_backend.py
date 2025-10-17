#!/usr/bin/env python3
"""
Intelligent Optimization Backend for LRDBenchmark

This module provides an intelligent backend system that automatically selects
the optimal computation framework (GPU/JAX, CPU/Numba, or NumPy) based on:
- Data characteristics (size, type, complexity)
- Hardware availability (GPU, CPU cores)
- Performance profiling results
- Memory constraints

The system learns from performance data and adapts to different scenarios.
"""

import numpy as np
import time
import psutil
import warnings
from typing import Dict, Any, Optional, Callable, Tuple, List
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from pathlib import Path
import hashlib
from datetime import datetime, timedelta

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


class OptimizationFramework(Enum):
    """Available optimization frameworks."""
    NUMPY = "numpy"
    NUMBA = "numba"
    JAX = "jax"


@dataclass
class PerformanceProfile:
    """Performance profile for a specific computation."""
    framework: OptimizationFramework
    data_size: int
    execution_time: float
    memory_usage: float
    accuracy: float
    success: bool
    timestamp: float
    computation_type: str = "unknown"
    hardware_hash: str = ""
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'framework': self.framework.value,
            'data_size': self.data_size,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'accuracy': self.accuracy,
            'success': self.success,
            'timestamp': self.timestamp,
            'computation_type': self.computation_type,
            'hardware_hash': self.hardware_hash,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceProfile':
        """Create from dictionary."""
        return cls(
            framework=OptimizationFramework(data['framework']),
            data_size=data['data_size'],
            execution_time=data['execution_time'],
            memory_usage=data['memory_usage'],
            accuracy=data['accuracy'],
            success=data['success'],
            timestamp=data['timestamp'],
            computation_type=data.get('computation_type', 'unknown'),
            hardware_hash=data.get('hardware_hash', ''),
            error_message=data.get('error_message', '')
        )


@dataclass
class HardwareInfo:
    """Hardware information and capabilities."""
    cpu_cores: int
    memory_gb: float
    has_gpu: bool
    gpu_memory_gb: Optional[float]
    jax_available: bool
    numba_available: bool


class OptimizationBackend:
    """
    Intelligent optimization backend that automatically selects the best
    computation framework based on data characteristics and hardware.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, enable_profiling: bool = True):
        """
        Initialize the optimization backend.
        
        Parameters
        ----------
        cache_dir : str, optional
            Directory to cache performance profiles. If None, uses default.
        enable_profiling : bool, default=True
            Whether to enable performance profiling and caching
        """
        self.cache_dir = self._initialise_cache_dir(cache_dir)
        self.enable_profiling = enable_profiling
        self.cache_file = self.cache_dir / 'performance_cache.json'
        self.failure_cache = self.cache_dir / 'failure_cache.json'
        
        self.performance_profiles: List[PerformanceProfile] = []
        self.framework_failures: Dict[str, List[Dict[str, Any]]] = {}
        self.hardware_info = self._detect_hardware()
        self.framework_weights = self._initialize_framework_weights()
        
        # Load persistent data
        if self.enable_profiling:
            self._load_performance_cache()
            self._load_failure_cache()
        
        # Performance thresholds (in seconds)
        self.performance_thresholds = {
            'small_data': 0.001,    # < 1000 points
            'medium_data': 0.01,    # 1000-10000 points
            'large_data': 0.1,      # > 10000 points
        }

        self.initialization_summary = {
            "cache_dir": str(self.cache_dir),
            "hardware": {
                "cpu_cores": self.hardware_info.cpu_cores,
                "memory_gb": self.hardware_info.memory_gb,
                "has_gpu": self.hardware_info.has_gpu,
                "jax_available": self.hardware_info.jax_available,
                "numba_available": self.hardware_info.numba_available,
            },
        }

    def _initialise_cache_dir(self, cache_dir: Optional[str]) -> Path:
        """Determine a writable cache directory without noisy side effects."""

        candidates: List[Path] = []

        if cache_dir:
            candidates.append(Path(cache_dir))
        else:
            env_dir = os.environ.get("LRDBENCHMARK_CACHE_DIR")
            if env_dir:
                candidates.append(Path(env_dir))
            try:
                candidates.append(Path.home() / ".lrdbenchmark" / "optimization_cache")
            except Exception:
                pass
            candidates.append(Path.cwd() / ".lrdbenchmark" / "optimization_cache")

        for directory in candidates:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                return directory
            except OSError:
                continue

        raise RuntimeError("Unable to determine a writable cache directory for optimization backend")
    
    def _detect_hardware(self) -> HardwareInfo:
        """Detect available hardware capabilities."""
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 1
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        gpu_memory_gb = None
        if HAS_GPU and JAX_AVAILABLE:
            try:
                # Try to get GPU memory info
                gpu_memory_gb = 8.0  # Default assumption, could be improved
            except:
                gpu_memory_gb = None
        
        return HardwareInfo(
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            has_gpu=HAS_GPU,
            gpu_memory_gb=gpu_memory_gb,
            jax_available=JAX_AVAILABLE,
            numba_available=NUMBA_AVAILABLE
        )
    
    def _initialize_framework_weights(self) -> Dict[OptimizationFramework, float]:
        """Initialize framework selection weights based on hardware."""
        weights = {
            OptimizationFramework.NUMPY: 1.0,
            OptimizationFramework.NUMBA: 1.0,
            OptimizationFramework.JAX: 1.0
        }
        
        # Adjust weights based on hardware
        if self.hardware_info.has_gpu and JAX_AVAILABLE:
            weights[OptimizationFramework.JAX] = 2.0  # Prefer JAX for GPU
        elif NUMBA_AVAILABLE:
            weights[OptimizationFramework.NUMBA] = 1.5  # Prefer Numba for CPU
        
        return weights
    
    def select_optimal_framework(self, 
                                data_size: int, 
                                computation_type: str,
                                memory_requirement: Optional[float] = None) -> OptimizationFramework:
        """
        Select the optimal framework for a given computation.
        
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
        # Check for recent failures
        for framework in OptimizationFramework:
            failures = self._get_framework_failures(framework.value)
            recent_failures = [f for f in failures if time.time() - f['timestamp'] < 3600]  # Last hour
            if len(recent_failures) > 5:  # Too many recent failures
                print(f"⚠️ Framework {framework.value} has {len(recent_failures)} recent failures, skipping")
                continue
        
        # Check memory constraints
        if memory_requirement and memory_requirement > self.hardware_info.memory_gb * 0.8:
            return OptimizationFramework.NUMPY  # Fallback to NumPy for memory safety
        
        # Get performance predictions for each framework
        predictions = {}
        for framework in OptimizationFramework:
            if self._is_framework_available(framework):
                predictions[framework] = self._predict_performance(
                    framework, data_size, computation_type
                )
        
        if not predictions:
            return OptimizationFramework.NUMPY
        
        # Select framework with best predicted performance
        best_framework = max(predictions.keys(), key=lambda f: predictions[f])
        
        # Apply hardware-specific adjustments
        if data_size < 100:
            # Very small data: NumPy is often fastest due to overhead
            best_framework = OptimizationFramework.NUMPY
        elif data_size > 10000 and self.hardware_info.has_gpu:
            # Large data with GPU: prefer JAX
            if OptimizationFramework.JAX in predictions:
                best_framework = OptimizationFramework.JAX
        
        return best_framework
    
    def _get_hardware_hash(self) -> str:
        """Get a hash representing current hardware configuration."""
        hw_info = f"{self.hardware_info.cpu_cores}_{self.hardware_info.memory_gb}_{self.hardware_info.has_gpu}"
        return hashlib.md5(hw_info.encode()).hexdigest()[:8]
    
    def _load_performance_cache(self):
        """Load performance data from persistent cache."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Load profiles
            for profile_data in data.get('profiles', []):
                profile = PerformanceProfile.from_dict(profile_data)
                self.performance_profiles.append(profile)
            
            # Clean old profiles (older than 30 days)
            cutoff_time = time.time() - (30 * 24 * 60 * 60)  # 30 days
            self.performance_profiles = [
                p for p in self.performance_profiles 
                if p.timestamp > cutoff_time
            ]
            
            print(f"Loaded {len(self.performance_profiles)} performance profiles from cache")
            
        except Exception as e:
            warnings.warn(f"Failed to load performance cache: {e}")
    
    def _save_performance_cache(self):
        """Save performance data to persistent cache."""
        try:
            data = {
                'profiles': [p.to_dict() for p in self.performance_profiles],
                'last_updated': time.time(),
                'hardware_hash': self._get_hardware_hash()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            warnings.warn(f"Failed to save performance cache: {e}")
    
    def _load_failure_cache(self):
        """Load framework failure data from cache."""
        if not self.failure_cache.exists():
            return
        
        try:
            with open(self.failure_cache, 'r') as f:
                self.framework_failures = json.load(f)
        except Exception as e:
            warnings.warn(f"Failed to load failure cache: {e}")
            self.framework_failures = {}
    
    def _save_failure_cache(self):
        """Save framework failure data to cache."""
        try:
            with open(self.failure_cache, 'w') as f:
                json.dump(self.framework_failures, f, indent=2)
        except Exception as e:
            warnings.warn(f"Failed to save failure cache: {e}")
    
    def _record_framework_failure(self, framework: str, error_message: str):
        """Record a framework failure."""
        if framework not in self.framework_failures:
            self.framework_failures[framework] = []
        
        self.framework_failures[framework].append({
            'timestamp': time.time(),
            'error': error_message
        })
        
        # Keep only recent failures (last 100)
        self.framework_failures[framework] = self.framework_failures[framework][-100:]
        
        self._save_failure_cache()
    
    def _get_framework_failures(self, framework: str) -> List[Dict[str, Any]]:
        """Get recent failures for a framework."""
        return self.framework_failures.get(framework, [])
    
    def _is_framework_available(self, framework: OptimizationFramework) -> bool:
        """Check if a framework is available."""
        if framework == OptimizationFramework.JAX:
            return JAX_AVAILABLE
        elif framework == OptimizationFramework.NUMBA:
            return NUMBA_AVAILABLE
        else:
            return True  # NumPy is always available
    
    def _predict_performance(self, 
                           framework: OptimizationFramework, 
                           data_size: int, 
                           computation_type: str) -> float:
        """
        Predict performance score for a framework based on historical data.
        
        Returns
        -------
        float
            Performance score (higher is better)
        """
        # Get relevant historical data
        relevant_profiles = [
            p for p in self.performance_profiles
            if p.framework == framework and p.success
        ]
        
        if not relevant_profiles:
            # No historical data, use default weights
            return self.framework_weights[framework]
        
        # Calculate weighted performance score
        scores = []
        for profile in relevant_profiles:
            # Normalize execution time (lower is better)
            time_score = 1.0 / (1.0 + profile.execution_time)
            # Accuracy weight
            accuracy_score = profile.accuracy
            # Combine scores
            score = time_score * accuracy_score
            scores.append(score)
        
        return np.mean(scores) if scores else self.framework_weights[framework]
    
    def profile_computation(self, 
                          func: Callable, 
                          data: np.ndarray, 
                          framework: OptimizationFramework,
                          computation_type: str = "unknown") -> PerformanceProfile:
        """
        Profile a computation and record performance metrics.
        
        Parameters
        ----------
        func : Callable
            Function to profile
        data : np.ndarray
            Input data
        framework : OptimizationFramework
            Framework used
        computation_type : str
            Type of computation
            
        Returns
        -------
        PerformanceProfile
            Performance profile of the computation
        """
        data_size = len(data) if hasattr(data, '__len__') else 1
        
        # Measure memory before
        process = psutil.Process()
        memory_before = process.memory_info().rss / (1024**2)  # MB
        
        # Time the computation
        start_time = time.time()
        try:
            result = func(data)
            success = True
            execution_time = time.time() - start_time
            
            # Calculate accuracy (simplified - could be improved)
            accuracy = 1.0  # Default accuracy, could be calculated based on result quality
            
        except Exception as e:
            success = False
            execution_time = time.time() - start_time
            accuracy = 0.0
            result = None
            warnings.warn(f"Computation failed with {framework.value}: {e}")
        
        # Measure memory after
        memory_after = process.memory_info().rss / (1024**2)  # MB
        memory_usage = memory_after - memory_before
        
        profile = PerformanceProfile(
            framework=framework,
            data_size=data_size,
            execution_time=execution_time,
            memory_usage=memory_usage,
            accuracy=accuracy,
            success=success,
            timestamp=time.time(),
            computation_type=computation_type,
            hardware_hash=self._get_hardware_hash(),
            error_message=str(e) if not success else ""
        )
        
        # Store the profile
        if self.enable_profiling:
            self.performance_profiles.append(profile)
            # Save to persistent cache every 10 profiles
            if len(self.performance_profiles) % 10 == 0:
                self._save_performance_cache()
        
        # Record failures
        if not success:
            self._record_framework_failure(framework.value, str(e))
        
        return profile
    
    def get_framework_recommendation(self, 
                                   data_size: int, 
                                   computation_type: str = "general") -> Dict[str, Any]:
        """
        Get a detailed recommendation for framework selection.
        
        Returns
        -------
        dict
            Recommendation with framework, reasoning, and performance predictions
        """
        optimal_framework = self.select_optimal_framework(data_size, computation_type)
        
        # Get performance predictions for all available frameworks
        predictions = {}
        for framework in OptimizationFramework:
            if self._is_framework_available(framework):
                predictions[framework.value] = self._predict_performance(
                    framework, data_size, computation_type
                )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(optimal_framework, data_size, computation_type)
        
        return {
            "recommended_framework": optimal_framework.value,
            "reasoning": reasoning,
            "performance_predictions": predictions,
            "hardware_info": {
                "cpu_cores": self.hardware_info.cpu_cores,
                "memory_gb": self.hardware_info.memory_gb,
                "has_gpu": self.hardware_info.has_gpu,
                "jax_available": self.hardware_info.jax_available,
                "numba_available": self.hardware_info.numba_available
            },
            "data_size": data_size,
            "computation_type": computation_type
        }
    
    def _generate_reasoning(self, 
                          framework: OptimizationFramework, 
                          data_size: int, 
                          computation_type: str) -> str:
        """Generate human-readable reasoning for framework selection."""
        if framework == OptimizationFramework.JAX:
            if data_size > 10000:
                return f"JAX selected for large dataset (n={data_size}) with GPU acceleration"
            else:
                return f"JAX selected for {computation_type} computation with GPU support"
        elif framework == OptimizationFramework.NUMBA:
            if data_size > 1000:
                return f"Numba selected for medium dataset (n={data_size}) with JIT compilation"
            else:
                return f"Numba selected for {computation_type} computation with CPU optimization"
        else:
            return f"NumPy selected as fallback for {computation_type} computation"
    
    def _get_hardware_hash(self) -> str:
        """Get a hash representing current hardware configuration."""
        hw_info = f"{self.hardware_info.cpu_cores}_{self.hardware_info.memory_gb}_{self.hardware_info.has_gpu}"
        return hashlib.md5(hw_info.encode()).hexdigest()[:8]
    
    def _load_performance_cache(self):
        """Load performance data from persistent cache."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Load profiles
            for profile_data in data.get('profiles', []):
                profile = PerformanceProfile.from_dict(profile_data)
                self.performance_profiles.append(profile)
            
            # Clean old profiles (older than 30 days)
            cutoff_time = time.time() - (30 * 24 * 60 * 60)  # 30 days
            self.performance_profiles = [
                p for p in self.performance_profiles 
                if p.timestamp > cutoff_time
            ]
            
            print(f"Loaded {len(self.performance_profiles)} performance profiles from cache")
            
        except Exception as e:
            warnings.warn(f"Failed to load performance cache: {e}")
    
    def _save_performance_cache(self):
        """Save performance data to persistent cache."""
        try:
            data = {
                'profiles': [p.to_dict() for p in self.performance_profiles],
                'last_updated': time.time(),
                'hardware_hash': self._get_hardware_hash()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            warnings.warn(f"Failed to save performance cache: {e}")
    
    def _load_failure_cache(self):
        """Load framework failure data from cache."""
        if not self.failure_cache.exists():
            return
        
        try:
            with open(self.failure_cache, 'r') as f:
                self.framework_failures = json.load(f)
        except Exception as e:
            warnings.warn(f"Failed to load failure cache: {e}")
            self.framework_failures = {}
    
    def _save_failure_cache(self):
        """Save framework failure data to cache."""
        try:
            with open(self.failure_cache, 'w') as f:
                json.dump(self.framework_failures, f, indent=2)
        except Exception as e:
            warnings.warn(f"Failed to save failure cache: {e}")
    
    def _record_framework_failure(self, framework: str, error_message: str):
        """Record a framework failure."""
        if framework not in self.framework_failures:
            self.framework_failures[framework] = []
        
        self.framework_failures[framework].append({
            'timestamp': time.time(),
            'error': error_message
        })
        
        # Keep only recent failures (last 100)
        self.framework_failures[framework] = self.framework_failures[framework][-100:]
        
        self._save_failure_cache()
    
    def _get_framework_failures(self, framework: str) -> List[Dict[str, Any]]:
        """Get recent failures for a framework."""
        return self.framework_failures.get(framework, [])
    
    def _load_performance_cache_legacy(self):
        """Load cached performance profiles from disk (legacy method)."""
        cache_file = self.cache_dir / "performance_profiles.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        profile = PerformanceProfile(
                            framework=OptimizationFramework(item['framework']),
                            data_size=item['data_size'],
                            execution_time=item['execution_time'],
                            memory_usage=item['memory_usage'],
                            accuracy=item['accuracy'],
                            success=item['success'],
                            timestamp=item['timestamp']
                        )
                        self.performance_profiles.append(profile)
                print(f"Loaded {len(self.performance_profiles)} cached performance profiles")
            except Exception as e:
                warnings.warn(f"Failed to load performance cache: {e}")
    
    def save_performance_cache(self):
        """Save performance profiles to disk."""
        cache_file = self.cache_dir / "performance_profiles.json"
        try:
            data = []
            for profile in self.performance_profiles:
                data.append({
                    'framework': profile.framework.value,
                    'data_size': profile.data_size,
                    'execution_time': profile.execution_time,
                    'memory_usage': profile.memory_usage,
                    'accuracy': profile.accuracy,
                    'success': profile.success,
                    'timestamp': profile.timestamp
                })
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {len(self.performance_profiles)} performance profiles to cache")
        except Exception as e:
            warnings.warn(f"Failed to save performance cache: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance data."""
        if not self.performance_profiles:
            return {"message": "No performance data available"}
        
        summary = {}
        for framework in OptimizationFramework:
            profiles = [p for p in self.performance_profiles if p.framework == framework]
            if profiles:
                successful = [p for p in profiles if p.success]
                summary[framework.value] = {
                    "total_runs": len(profiles),
                    "success_rate": len(successful) / len(profiles),
                    "avg_execution_time": np.mean([p.execution_time for p in successful]) if successful else 0,
                    "avg_accuracy": np.mean([p.accuracy for p in successful]) if successful else 0,
                    "data_size_range": (min(p.data_size for p in profiles), max(p.data_size for p in profiles))
                }
        
        return summary


# Global backend instance
_global_backend = None

def get_optimization_backend() -> OptimizationBackend:
    """Get the global optimization backend instance."""
    global _global_backend
    if _global_backend is None:
        _global_backend = OptimizationBackend()
    return _global_backend

def set_optimization_backend(backend: OptimizationBackend):
    """Set the global optimization backend instance."""
    global _global_backend
    _global_backend = backend
