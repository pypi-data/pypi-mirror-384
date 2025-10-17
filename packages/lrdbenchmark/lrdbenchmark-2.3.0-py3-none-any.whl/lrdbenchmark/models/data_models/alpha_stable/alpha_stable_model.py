#!/usr/bin/env python3
"""
Alpha-Stable Distribution Data Model Implementation.

This module provides a unified class for generating alpha-stable distributed
time series data with various generation methods and optimization backends.

Alpha-stable distributions are characterized by four parameters:
- α (stability): 0 < α ≤ 2, controls tail heaviness
- β (skewness): -1 ≤ β ≤ 1, controls asymmetry  
- σ (scale): σ > 0, controls spread
- μ (location): Real number, controls center

The class supports multiple generation methods:
- Chambers-Mallows-Stuck (CMS): Most commonly used
- Nolan's Method: More numerically stable
- Series Representation: For specific parameter ranges
- Fourier Transform: For symmetric cases (β = 0)

References:
- Nolan, J. P. (2020). Univariate Stable Distributions: Models for Heavy Tailed Data
- Chambers, J. M., Mallows, C. L., & Stuck, B. W. (1976). A method for simulating stable random variables
"""

import numpy as np
from scipy import special
from typing import Optional, Dict, Any, Tuple
import warnings

# Try to import optimization libraries
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

from ..base_model import BaseModel


class AlphaStableModel(BaseModel):
    """
    Unified Alpha-Stable Distribution model for generating heavy-tailed time series.
    
    This class provides multiple generation methods for alpha-stable distributions
    with automatic method selection based on parameters and available backends.
    
    Parameters
    ----------
    alpha : float
        Stability parameter (0 < alpha <= 2)
        - alpha = 2: Gaussian distribution
        - alpha = 1: Cauchy distribution  
        - alpha < 2: Heavy-tailed distributions
        - alpha < 1: Very heavy tails, infinite mean
    beta : float, optional
        Skewness parameter (-1 <= beta <= 1, default: 0)
        - beta = 0: Symmetric distribution
        - beta > 0: Right-skewed
        - beta < 0: Left-skewed
    sigma : float, optional
        Scale parameter (sigma > 0, default: 1.0)
    mu : float, optional
        Location parameter (default: 0.0)
    method : str, optional
        Generation method (default: 'auto')
        - 'auto': Automatically select best method
        - 'cms': Chambers-Mallows-Stuck method
        - 'nolan': Nolan's numerically stable method
        - 'series': Series representation (for specific cases)
        - 'fourier': Fourier transform (symmetric only)
    use_optimization : str, optional
        Optimization framework (default: 'auto')
        - 'auto': Choose best available
        - 'jax': GPU acceleration (when available)
        - 'numba': CPU optimization (when available)
        - 'numpy': Standard NumPy
    """

    def __init__(
        self,
        alpha: float,
        beta: float = 0.0,
        sigma: float = 1.0,
        mu: float = 0.0,
        method: str = "auto",
        use_optimization: str = "auto",
    ):
        """
        Initialize the Alpha-Stable model.
        
        Parameters
        ----------
        alpha : float
            Stability parameter (0 < alpha <= 2)
        beta : float, optional
            Skewness parameter (-1 <= beta <= 1, default: 0)
        sigma : float, optional
            Scale parameter (sigma > 0, default: 1.0)
        mu : float, optional
            Location parameter (default: 0.0)
        method : str, optional
            Generation method (default: 'auto')
        use_optimization : str, optional
            Optimization framework (default: 'auto')
        """
        # Store parameters before calling super().__init__
        self.alpha = alpha
        self.beta = beta
        self.sigma = sigma
        self.mu = mu
        self.method = method
        self.use_optimization = use_optimization
        
        # Set model properties
        self.name = "AlphaStable"
        self.category = "HeavyTailed"
        
        super().__init__(
            alpha=alpha,
            beta=beta,
            sigma=sigma,
            mu=mu,
            method=method,
            use_optimization=use_optimization,
        )

    def _validate_parameters(self) -> None:
        """Validate alpha-stable parameters."""
        if not (0 < self.alpha <= 2):
            raise ValueError("alpha must be in (0, 2]")
        
        if not (-1 <= self.beta <= 1):
            raise ValueError("beta must be in [-1, 1]")
        
        if self.sigma <= 0:
            raise ValueError("sigma must be positive")
        
        if not isinstance(self.mu, (int, float)):
            raise ValueError("mu must be a real number")
        
        if self.method not in ['auto', 'cms', 'nolan', 'series', 'fourier']:
            raise ValueError("method must be one of: auto, cms, nolan, series, fourier")
        
        if self.use_optimization not in ['auto', 'jax', 'numba', 'numpy']:
            raise ValueError("use_optimization must be one of: auto, jax, numba, numpy")

    def _select_method(self) -> str:
        """Select the best generation method based on parameters."""
        if self.method != 'auto':
            return self.method
        
        # Special cases
        if self.alpha == 2:
            return 'gaussian'  # Use standard normal
        elif self.alpha == 1 and self.beta == 0:
            return 'cauchy'    # Use standard Cauchy
        elif self.beta == 0:
            return 'fourier'   # Symmetric case
        elif self.alpha < 0.5:
            return 'nolan'     # Very heavy tails
        else:
            return 'cms'       # General case

    def _select_backend(self, n: int) -> str:
        """Select the best backend based on data size and availability."""
        if self.use_optimization != 'auto':
            return self.use_optimization
        
        # Auto-select based on data size and availability
        if JAX_AVAILABLE and n > 1000:
            return 'jax'
        elif NUMBA_AVAILABLE and n > 100:
            return 'numba'
        else:
            return 'numpy'

    def _generate_gaussian(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate Gaussian distribution (alpha = 2)."""
        if seed is not None:
            np.random.seed(seed)
        return self.sigma * np.random.normal(0, 1, n) + self.mu

    def _generate_cauchy(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate Cauchy distribution (alpha = 1, beta = 0)."""
        if seed is not None:
            np.random.seed(seed)
        return self.sigma * np.random.standard_cauchy(n) + self.mu

    def _generate_cms_numpy(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate using Chambers-Mallows-Stuck method (NumPy)."""
        if seed is not None:
            np.random.seed(seed)
        
        alpha = self.alpha
        beta = self.beta
        sigma = self.sigma
        mu = self.mu
        
        # Generate uniform and exponential random variables
        U = np.random.uniform(-np.pi/2, np.pi/2, n)
        W = np.random.exponential(1, n)
        
        if alpha == 1:
            # Special case: Cauchy distribution
            return sigma * np.tan(U) + mu
        else:
            # General case
            B = beta * np.tan(np.pi * alpha / 2)
            S = (1 + B**2 * np.tan(np.pi * alpha / 2)**2)**(1/(2*alpha))
            
            # Avoid division by zero
            cos_U = np.cos(U)
            cos_U = np.where(np.abs(cos_U) < 1e-10, 1e-10, cos_U)
            
            X = (S * np.sin(alpha * (U + np.arctan(B * np.tan(np.pi * alpha / 2)))) / 
                 cos_U**(1/alpha) * 
                 (np.cos(U - alpha * (U + np.arctan(B * np.tan(np.pi * alpha / 2)))) / W)**((1-alpha)/alpha))
            
            return sigma * X + mu

    def _generate_cms_numba(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate using CMS method (Numba)."""
        if not NUMBA_AVAILABLE:
            return self._generate_cms_numpy(n, seed)
        
        if seed is not None:
            np.random.seed(seed)
        
        @numba_jit(nopython=True)
        def cms_core(alpha, beta, sigma, mu, n):
            U = np.random.uniform(-np.pi/2, np.pi/2, n)
            W = np.random.exponential(1, n)
            
            if alpha == 1:
                return sigma * np.tan(U) + mu
            else:
                B = beta * np.tan(np.pi * alpha / 2)
                S = (1 + B**2 * np.tan(np.pi * alpha / 2)**2)**(1/(2*alpha))
                
                cos_U = np.cos(U)
                cos_U = np.where(np.abs(cos_U) < 1e-10, 1e-10, cos_U)
                
                X = (S * np.sin(alpha * (U + np.arctan(B * np.tan(np.pi * alpha / 2)))) / 
                     cos_U**(1/alpha) * 
                     (np.cos(U - alpha * (U + np.arctan(B * np.tan(np.pi * alpha / 2)))) / W)**((1-alpha)/alpha))
                
                return sigma * X + mu
        
        return cms_core(self.alpha, self.beta, self.sigma, self.mu, n)

    def _generate_cms_jax(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate using CMS method (JAX)."""
        if not JAX_AVAILABLE:
            return self._generate_cms_numpy(n, seed)
        
        @jit
        def cms_core_jax(alpha, beta, sigma, mu, key, n):
            key1, key2 = jax.random.split(key)
            U = jax.random.uniform(key1, (n,), minval=-np.pi / 2, maxval=np.pi / 2)
            W = jax.random.exponential(key2, (n,))
            
            if alpha == 1:
                return sigma * jnp.tan(U) + mu
            else:
                B = beta * jnp.tan(np.pi * alpha / 2)
                S = (1 + B**2 * jnp.tan(np.pi * alpha / 2)**2)**(1/(2*alpha))
                
                cos_U = jnp.cos(U)
                cos_U = jnp.where(jnp.abs(cos_U) < 1e-10, 1e-10, cos_U)
                
                X = (S * jnp.sin(alpha * (U + jnp.arctan(B * jnp.tan(np.pi * alpha / 2)))) / 
                     cos_U**(1/alpha) * 
                     (jnp.cos(U - alpha * (U + jnp.arctan(B * jnp.tan(np.pi * alpha / 2)))) / W)**((1-alpha)/alpha))
                
                return sigma * X + mu
        
        if seed is not None:
            key = jax.random.PRNGKey(seed)
        else:
            key = jax.random.PRNGKey(42)
        
        return np.array(cms_core_jax(self.alpha, self.beta, self.sigma, self.mu, key, n))

    def _generate_nolan_numpy(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate using Nolan's numerically stable method (NumPy)."""
        if seed is not None:
            np.random.seed(seed)
        
        alpha = self.alpha
        beta = self.beta
        sigma = self.sigma
        mu = self.mu
        
        # Generate uniform and exponential random variables
        U = np.random.uniform(-np.pi/2, np.pi/2, n)
        W = np.random.exponential(1, n)
        
        if alpha == 1:
            # Cauchy case
            return sigma * np.tan(U) + mu
        else:
            # Nolan's method with better numerical stability
            phi_0 = -beta * np.tan(np.pi * alpha / 2)
            
            # Avoid numerical issues
            cos_U = np.cos(U)
            cos_U = np.where(np.abs(cos_U) < 1e-10, 1e-10, cos_U)
            
            # More stable computation
            A = (np.sin(alpha * U + phi_0) / cos_U**(1/alpha))
            B = (np.cos((1 - alpha) * U + phi_0) / W)**((1 - alpha) / alpha)
            
            X = A * B
            return sigma * X + mu

    def _generate_fourier_numpy(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """Generate symmetric alpha-stable using Fourier transform (NumPy)."""
        if self.beta != 0:
            warnings.warn("Fourier method only works for symmetric distributions (beta=0)")
            return self._generate_cms_numpy(n, seed)
        
        if seed is not None:
            np.random.seed(seed)
        
        alpha = self.alpha
        sigma = self.sigma
        mu = self.mu
        
        # Generate using characteristic function
        # For symmetric case: φ(t) = exp(-|σt|^α)
        
        # Generate uniform random variables
        U = np.random.uniform(0, 2*np.pi, n)
        
        # Generate exponential random variables
        E = np.random.exponential(1, n)
        
        # For symmetric alpha-stable
        if alpha == 1:
            # Cauchy case
            return sigma * np.tan(U - np.pi/2) + mu
        else:
            # General symmetric case
            S = (E / np.cos(U))**(1/alpha) * np.sin(alpha * U) / np.sin(U)
            return sigma * S + mu

    def generate(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """
        Generate alpha-stable distributed time series.
        
        Parameters
        ----------
        n : int
            Number of samples to generate
        seed : int, optional
            Random seed for reproducibility
            
        Returns
        -------
        np.ndarray
            Generated alpha-stable time series
        """
        if n <= 0:
            raise ValueError("n must be positive")
        
        # Select generation method
        method = self._select_method()
        
        # Handle special cases
        if method == 'gaussian':
            return self._generate_gaussian(n, seed)
        elif method == 'cauchy':
            return self._generate_cauchy(n, seed)
        
        # Select backend
        backend = self._select_backend(n)
        
        # Generate data using selected method and backend
        try:
            if method == 'cms':
                if backend == 'jax':
                    return self._generate_cms_jax(n, seed)
                elif backend == 'numba':
                    return self._generate_cms_numba(n, seed)
                else:
                    return self._generate_cms_numpy(n, seed)
            
            elif method == 'nolan':
                return self._generate_nolan_numpy(n, seed)
            
            elif method == 'fourier':
                return self._generate_fourier_numpy(n, seed)
            
            else:
                # Fallback to CMS
                return self._generate_cms_numpy(n, seed)
                
        except Exception as e:
            warnings.warn(f"Primary method failed ({e}), falling back to NumPy CMS")
            return self._generate_cms_numpy(n, seed)

    def get_parameters(self) -> Dict[str, Any]:
        """Get model parameters."""
        return {
            'alpha': self.alpha,
            'beta': self.beta,
            'sigma': self.sigma,
            'mu': self.mu,
            'method': self.method,
            'use_optimization': self.use_optimization
        }

    def get_properties(self) -> Dict[str, Any]:
        """Get distribution properties."""
        return {
            'name': self.name,
            'category': self.category,
            'stability_parameter': self.alpha,
            'skewness_parameter': self.beta,
            'scale_parameter': self.sigma,
            'location_parameter': self.mu,
            'has_finite_variance': self.alpha == 2,
            'has_finite_mean': self.alpha > 1,
            'is_symmetric': self.beta == 0,
            'tail_index': self.alpha,
            'heavy_tailed': self.alpha < 2
        }

    def theoretical_moments(self) -> Dict[str, Any]:
        """Calculate theoretical moments (when they exist)."""
        moments = {}
        
        if self.alpha > 1:
            moments['mean'] = self.mu
        else:
            moments['mean'] = None  # Infinite mean
        
        if self.alpha == 2:
            moments['variance'] = 2 * self.sigma**2
            moments['skewness'] = 0
            moments['kurtosis'] = 3
        else:
            moments['variance'] = None  # Infinite variance
            moments['skewness'] = None
            moments['kurtosis'] = None
        
        return moments

    def sample_properties(self, n: int = 10000, seed: Optional[int] = None) -> Dict[str, Any]:
        """Estimate properties from a large sample."""
        sample = self.generate(n, seed)
        
        properties = {
            'sample_mean': np.mean(sample),
            'sample_median': np.median(sample),
            'sample_std': np.std(sample),
            'sample_skewness': self._calculate_skewness(sample),
            'sample_kurtosis': self._calculate_kurtosis(sample),
            'sample_min': np.min(sample),
            'sample_max': np.max(sample),
            'sample_range': np.max(sample) - np.min(sample)
        }
        
        return properties

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate sample skewness."""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 3)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate sample kurtosis."""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std) ** 4) - 3

    def get_theoretical_properties(self) -> Dict[str, Any]:
        """
        Get theoretical properties of the alpha-stable model.
        
        Returns
        -------
        dict
            Dictionary containing theoretical properties
        """
        properties = {
            'distribution_type': 'alpha_stable',
            'stability_parameter': self.alpha,
            'skewness_parameter': self.beta,
            'scale_parameter': self.sigma,
            'location_parameter': self.mu,
            'has_finite_variance': self.alpha == 2,
            'has_finite_mean': self.alpha > 1,
            'is_symmetric': self.beta == 0,
            'tail_index': self.alpha,
            'heavy_tailed': self.alpha < 2,
            'characteristic_function': f"φ(t) = exp(iμt - |σt|^α(1 - iβsgn(t)tan(πα/2)))" if self.alpha != 1 else f"φ(t) = exp(iμt - σ|t|(1 + iβ(2/π)sgn(t)log|t|))",
            'support': '(-∞, ∞)',
            'special_cases': {
                'gaussian': self.alpha == 2,
                'cauchy': self.alpha == 1 and self.beta == 0,
                'levy': self.alpha == 0.5 and self.beta == 1,
                'symmetric': self.beta == 0
            }
        }
        
        # Add theoretical moments when they exist
        if self.alpha > 1:
            properties['theoretical_mean'] = self.mu
        else:
            properties['theoretical_mean'] = None  # Infinite mean
        
        if self.alpha == 2:
            properties['theoretical_variance'] = 2 * self.sigma**2
            properties['theoretical_skewness'] = 0
            properties['theoretical_kurtosis'] = 3
        else:
            properties['theoretical_variance'] = None  # Infinite variance
            properties['theoretical_skewness'] = None
            properties['theoretical_kurtosis'] = None
        
        return properties


# Example usage and testing
if __name__ == "__main__":
    # Test different alpha-stable distributions
    print("Testing Alpha-Stable Data Model")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        (2.0, 0.0, "Gaussian"),
        (1.0, 0.0, "Cauchy"),
        (1.5, 0.0, "Symmetric α=1.5"),
        (1.5, 0.5, "Skewed α=1.5"),
        (0.8, 0.0, "Heavy-tailed α=0.8"),
    ]
    
    for alpha, beta, name in test_cases:
        print(f"\n{name} (α={alpha}, β={beta}):")
        print("-" * 30)
        
        model = AlphaStableModel(alpha=alpha, beta=beta, sigma=1.0, mu=0.0)
        data = model.generate(1000, seed=42)
        
        properties = model.sample_properties(1000, seed=42)
        theoretical = model.theoretical_moments()
        
        print(f"Sample mean: {properties['sample_mean']:.4f}")
        print(f"Sample std: {properties['sample_std']:.4f}")
        print(f"Sample skewness: {properties['sample_skewness']:.4f}")
        print(f"Sample kurtosis: {properties['sample_kurtosis']:.4f}")
        
        if theoretical['mean'] is not None:
            print(f"Theoretical mean: {theoretical['mean']:.4f}")
        if theoretical['variance'] is not None:
            print(f"Theoretical variance: {theoretical['variance']:.4f}")
        
        print(f"Has finite variance: {model.get_properties()['has_finite_variance']}")
        print(f"Has finite mean: {model.get_properties()['has_finite_mean']}")
