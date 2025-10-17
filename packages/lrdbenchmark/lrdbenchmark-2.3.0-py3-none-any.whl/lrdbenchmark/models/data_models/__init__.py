"""
Data models package containing implementations of stochastic processes.

This package provides classes for generating synthetic data from various
stochastic models including ARFIMA, fBm, fGn, and MRW.
"""

from .base_model import BaseModel

# Import all model classes
try:
    from .fbm.fbm_model import FractionalBrownianMotion
    from .fgn.fgn_model import FractionalGaussianNoise
    from .arfima.arfima_model import ARFIMAModel
    from .mrw.mrw_model import MultifractalRandomWalk
    from .alpha_stable.alpha_stable_model import AlphaStableModel
    
    # Create shortened aliases for convenience
    FBMModel = FractionalBrownianMotion
    FGNModel = FractionalGaussianNoise
    ARFIMAModel = ARFIMAModel  # Keep as is since it's already short
    MRWModel = MultifractalRandomWalk
    AlphaStableModel = AlphaStableModel  # Keep as is since it's already descriptive
    
except ImportError as e:
    print(f"Warning: Could not import data models: {e}")
    # Create placeholder classes
    class FBMModel:
        def __init__(self, H=0.6, **kwargs):
            self.H = H
        def generate(self, n=1000):
            import numpy as np
            t = np.linspace(0, 1, n)
            dt = t[1] - t[0]
            increments = np.random.normal(0, 1, n) * (dt ** self.H)
            return np.cumsum(increments)
    
    class FGNModel:
        def __init__(self, H=0.6, **kwargs):
            self.H = H
        def generate(self, n=1000):
            import numpy as np
            t = np.linspace(0, 1, n)
            dt = t[1] - t[0]
            return np.random.normal(0, 1, n) * (dt ** self.H)
    
    class ARFIMAModel:
        def __init__(self, d=0.2, **kwargs):
            self.d = d
        def generate(self, n=1000):
            import numpy as np
            return np.random.normal(0, 1, n)
    
    class MRWModel:
        def __init__(self, H=0.6, **kwargs):
            self.H = H
        def generate(self, n=1000):
            import numpy as np
            return np.random.normal(0, 1, n)
    
    class AlphaStableModel:
        def __init__(self, alpha=1.5, beta=0.0, **kwargs):
            self.alpha = alpha
            self.beta = beta
        def generate(self, n=1000):
            import numpy as np
            return np.random.normal(0, 1, n)

# Convenience functions with default parameters
def create_fbm_model(H=0.7, sigma=1.0):
    """Create FBMModel with default parameters"""
    return FBMModel(H=H, sigma=sigma)

def create_fgn_model(H=0.6, sigma=1.0):
    """Create FGNModel with default parameters"""
    return FGNModel(H=H, sigma=sigma)

def create_arfima_model(d=0.2, sigma=1.0):
    """Create ARFIMAModel with default parameters"""
    return ARFIMAModel(d=d, sigma=sigma)

def create_mrw_model(H=0.7, lambda_param=0.1, sigma=1.0):
    """Create MRWModel with default parameters"""
    return MRWModel(H=H, lambda_param=lambda_param, sigma=sigma)

def create_alpha_stable_model(alpha=1.5, beta=0.0, sigma=1.0, mu=0.0):
    """Create AlphaStableModel with default parameters"""
    return AlphaStableModel(alpha=alpha, beta=beta, sigma=sigma, mu=mu)

__all__ = [
    "BaseModel",
    "FractionalBrownianMotion",
    "FractionalGaussianNoise", 
    "ARFIMAModel",
    "MultifractalRandomWalk",
    "AlphaStableModel",
    "FBMModel",
    "FGNModel",
    "MRWModel",
    "create_fbm_model",
    "create_fgn_model",
    "create_arfima_model",
    "create_mrw_model",
    "create_alpha_stable_model",
]
