"""
Machine Learning Estimators for Long-Range Dependence Analysis

This package provides machine learning-based approaches for estimating
Hurst parameters and long-range dependence characteristics from time series data.
"""

# Import unified estimators with error handling
try:
    from .random_forest_estimator_unified import RandomForestEstimator
except ImportError:
    RandomForestEstimator = None

try:
    from .svr_estimator_unified import SVREstimator
except ImportError:
    SVREstimator = None

try:
    from .gradient_boosting_estimator_unified import GradientBoostingEstimator
except ImportError:
    GradientBoostingEstimator = None

try:
    from .cnn_estimator_unified import CNNEstimator
except ImportError:
    CNNEstimator = None

try:
    from .lstm_estimator_unified import LSTMEstimator
except ImportError:
    LSTMEstimator = None

try:
    from .gru_estimator_unified import GRUEstimator
except ImportError:
    GRUEstimator = None

try:
    from .transformer_estimator_unified import TransformerEstimator
except ImportError:
    TransformerEstimator = None

try:
    from .neural_network_factory import NeuralNetworkFactory
except ImportError:
    NeuralNetworkFactory = None

__all__ = [
    "RandomForestEstimator",
    "SVREstimator", 
    "GradientBoostingEstimator",
    "CNNEstimator",
    "LSTMEstimator",
    "GRUEstimator",
    "TransformerEstimator",
    "NeuralNetworkFactory",
]
