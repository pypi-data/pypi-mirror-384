"""
LRDBenchmark: Long-Range Dependence Benchmarking Toolkit

A comprehensive toolkit for benchmarking long-range dependence estimators
on synthetic and real-world time series data.
"""

__version__ = "2.3.0"
__author__ = "LRDBench Development Team"
__email__ = "lrdbench@example.com"

# Core data models
try:
    from .models.data_models import FBMModel, FGNModel, ARFIMAModel, MRWModel
except ImportError as e:
    print(f"Warning: Could not import data models: {e}")
    FBMModel = None
    FGNModel = None
    ARFIMAModel = None
    MRWModel = None

# Classical estimators
try:
    from .analysis.temporal.rs.rs_estimator_unified import RSEstimator
    from .analysis.temporal.dfa.dfa_estimator_unified import DFAEstimator
    from .analysis.spectral.whittle.whittle_estimator_unified import WhittleEstimator
    from .analysis.spectral.gph.gph_estimator_unified import GPHEstimator
except ImportError as e:
    print(f"Warning: Could not import classical estimators: {e}")
    RSEstimator = None
    DFAEstimator = None
    WhittleEstimator = None
    GPHEstimator = None

# Machine Learning estimators
try:
    from .analysis.machine_learning import (
        RandomForestEstimator,
        SVREstimator,
        GradientBoostingEstimator,
        CNNEstimator,
        LSTMEstimator,
        GRUEstimator,
        TransformerEstimator,
    )
except ImportError as e:
    print(f"Warning: Could not import ML estimators: {e}")
    RandomForestEstimator = None
    SVREstimator = None
    GradientBoostingEstimator = None
    CNNEstimator = None
    LSTMEstimator = None
    GRUEstimator = None
    TransformerEstimator = None

# Neural Network Factory
try:
    from .analysis.machine_learning.neural_network_factory import NeuralNetworkFactory
except ImportError as e:
    print(f"Warning: Could not import neural network factory: {e}")
    NeuralNetworkFactory = None

# GPU utilities
try:
    from .gpu import is_available as gpu_is_available, get_device_info, clear_cache, suggest_batch_size, get_safe_device
    from .gpu_memory import get_gpu_memory_info, clear_gpu_cache, monitor_gpu_memory
except ImportError as e:
    print(f"Warning: Could not import GPU utilities: {e}")
    gpu_is_available = lambda: False
    get_device_info = lambda: {'available': False}
    clear_cache = lambda: None
    suggest_batch_size = lambda data_size, seq_len: min(32, data_size)
    get_safe_device = lambda use_gpu=False: 'cpu'
    get_gpu_memory_info = lambda: {'torch_available': False, 'jax_available': False}
    clear_gpu_cache = lambda: None
    monitor_gpu_memory = lambda op_name="operation": None

# Main exports
__all__ = [
    # Data models
    "FBMModel",
    "FGNModel", 
    "ARFIMAModel",
    "MRWModel",
    # Classical estimators
    "RSEstimator",
    "DFAEstimator",
    "WhittleEstimator",
    "GPHEstimator",
    # Machine Learning estimators
    "RandomForestEstimator",
    "SVREstimator",
    "GradientBoostingEstimator",
    "CNNEstimator",
    "LSTMEstimator",
    "GRUEstimator",
    "TransformerEstimator",
    # Neural Network Factory
    "NeuralNetworkFactory",
    # GPU utilities
    "gpu_is_available",
    "get_device_info", 
    "clear_cache",
    "suggest_batch_size",
    "get_safe_device",
    "get_gpu_memory_info",
    "clear_gpu_cache",
    "monitor_gpu_memory",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]
