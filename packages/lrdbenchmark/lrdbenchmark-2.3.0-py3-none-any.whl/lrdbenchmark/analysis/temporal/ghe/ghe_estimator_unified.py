#!/usr/bin/env python3
"""
Unified GHE (Generalized Hurst Exponent) Estimator for Long-Range Dependence Analysis.

This module implements the GHE estimator based on the paper:
"Typical Algorithms for Estimating Hurst Exponent of Time Sequence: A Data Analyst's Perspective"
by HONG-YAN ZHANG, ZHI-QIANG FENG, SI-YU FENG, AND YU ZHOU
IEEE ACCESS 2024, DOI: 10.1109/ACCESS.2024.3512542

The GHE method analyzes the scaling properties of time series data by computing
q-th order moments of increments and estimating the generalized Hurst exponent.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, Union, Tuple, List
import warnings
from scipy import stats
from scipy.optimize import curve_fit

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

# Import base estimator
try:
    from lrdbenchmark.models.estimators.base_estimator import BaseEstimator
except ImportError:
    # Fallback if base estimator not available
    class BaseEstimator:
        def __init__(self, **kwargs):
            self.parameters = kwargs
            self.results = {}


class GHEEstimator(BaseEstimator):
    """
    Unified GHE (Generalized Hurst Exponent) Estimator for Long-Range Dependence Analysis.

    The GHE estimator analyzes the scaling properties of time series data by computing
    q-th order moments of increments and estimating the generalized Hurst exponent.

    Features:
    - Automatic framework selection (JAX, Numba, NumPy)
    - Multiple q values for multifractal analysis
    - Robust error handling and fallback mechanisms
    - Comprehensive result reporting
    - Visualization capabilities

    Parameters
    ----------
    q_values : array-like, optional
        Array of q values for multifractal analysis. Default: [1, 2, 3, 4, 5]
    tau_min : int, optional
        Minimum time lag. Default: 2
    tau_max : int, optional
        Maximum time lag. Default: min(N//4, 50) where N is data length
    tau_step : int, optional
        Step size for time lags. Default: 1
    use_jax : bool, optional
        Force JAX backend if available. Default: None (auto-select)
    use_numba : bool, optional
        Force Numba backend if available. Default: None (auto-select)
    """

    def __init__(self, **kwargs):
        """
        Initialize the GHE estimator.

        Parameters
        ----------
        **kwargs : dict
            Estimator parameters
        """
        super().__init__(**kwargs)
        
        # Set default parameters
        self.parameters.setdefault('q_values', np.array([1, 2, 3, 4, 5]))
        self.parameters.setdefault('tau_min', 2)
        self.parameters.setdefault('tau_max', None)
        self.parameters.setdefault('tau_step', 1)
        self.parameters.setdefault('use_jax', None)
        self.parameters.setdefault('use_numba', None)
        
        # Initialize results
        self.results = {}
        self.name = "GHE"
        self.category = "Temporal"
        
        # Validate parameters
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate estimator parameters."""
        q_values = self.parameters['q_values']
        if not isinstance(q_values, (list, np.ndarray)):
            raise ValueError("q_values must be a list or numpy array")
        
        q_values = np.array(q_values)
        if len(q_values) == 0:
            raise ValueError("q_values cannot be empty")
        
        if np.any(q_values <= 0):
            raise ValueError("All q_values must be positive")
        
        if self.parameters['tau_min'] < 1:
            raise ValueError("tau_min must be at least 1")
        
        if self.parameters['tau_step'] < 1:
            raise ValueError("tau_step must be at least 1")

    def _compute_qth_moments_numpy(self, data: np.ndarray, q_values: np.ndarray, 
                                 tau_values: np.ndarray) -> np.ndarray:
        """
        Compute q-th order moments using NumPy.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        q_values : np.ndarray
            Array of q values
        tau_values : np.ndarray
            Array of time lags
        
        Returns
        -------
        np.ndarray
            Array of shape (len(q_values), len(tau_values)) containing q-th moments
        """
        N = len(data)
        moments = np.zeros((len(q_values), len(tau_values)))
        
        for i, q in enumerate(q_values):
            for j, tau in enumerate(tau_values):
                if tau >= N:
                    moments[i, j] = np.nan
                    continue
                
                # Compute increments
                increments = data[tau:] - data[:-tau]
                
                # Compute q-th moment
                if q == 1:
                    moments[i, j] = np.mean(np.abs(increments))
                else:
                    moments[i, j] = np.mean(np.abs(increments) ** q)
        
        return moments

    def _compute_qth_moments_numba(self, data: np.ndarray, q_values: np.ndarray, 
                                 tau_values: np.ndarray) -> np.ndarray:
        """
        Compute q-th order moments using Numba.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        q_values : np.ndarray
            Array of q values
        tau_values : np.ndarray
            Array of time lags
        
        Returns
        -------
        np.ndarray
            Array of shape (len(q_values), len(tau_values)) containing q-th moments
        """
        if not NUMBA_AVAILABLE:
            return self._compute_qth_moments_numpy(data, q_values, tau_values)
        
        @numba_jit(nopython=True, parallel=True)
        def compute_moments_numba(data, q_values, tau_values):
            N = len(data)
            n_q = len(q_values)
            n_tau = len(tau_values)
            moments = np.zeros((n_q, n_tau))
            
            for i in prange(n_q):
                q = q_values[i]
                for j in prange(n_tau):
                    tau = int(tau_values[j])
                    if tau >= N:
                        moments[i, j] = np.nan
                        continue
                    
                    # Compute increments
                    increments = data[tau:] - data[:-tau]
                    
                    # Compute q-th moment
                    if q == 1.0:
                        moments[i, j] = np.mean(np.abs(increments))
                    else:
                        moments[i, j] = np.mean(np.abs(increments) ** q)
            
            return moments
        
        return compute_moments_numba(data, q_values, tau_values)

    def _compute_qth_moments_jax(self, data: np.ndarray, q_values: np.ndarray, 
                               tau_values: np.ndarray) -> np.ndarray:
        """
        Compute q-th order moments using JAX.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data
        q_values : np.ndarray
            Array of q values
        tau_values : np.ndarray
            Array of time lags
        
        Returns
        -------
        np.ndarray
            Array of shape (len(q_values), len(tau_values)) containing q-th moments
        """
        if not JAX_AVAILABLE:
            return self._compute_qth_moments_numpy(data, q_values, tau_values)
        
        @jit
        def compute_moments_jax(data, q_values, tau_values):
            N = len(data)
            moments = jnp.zeros((len(q_values), len(tau_values)))
            
            def compute_for_tau(tau_idx):
                tau = tau_values[tau_idx]
                if tau >= N:
                    return jnp.full(len(q_values), jnp.nan)
                
                # Compute increments
                increments = data[tau:] - data[:-tau]
                
                # Compute q-th moments for all q values
                def compute_for_q(q_idx):
                    q = q_values[q_idx]
                    if q == 1.0:
                        return jnp.mean(jnp.abs(increments))
                    else:
                        return jnp.mean(jnp.abs(increments) ** q)
                
                return jnp.array([compute_for_q(i) for i in range(len(q_values))])
            
            return jnp.array([compute_for_tau(i) for i in range(len(tau_values))]).T
        
        return np.array(compute_moments_jax(data, q_values, tau_values))

    def _estimate_hurst_exponents(self, tau_values: np.ndarray, moments: np.ndarray, 
                                q_values: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Estimate Hurst exponents from q-th moments.
        
        Parameters
        ----------
        tau_values : np.ndarray
            Array of time lags
        moments : np.ndarray
            Array of q-th moments
        q_values : np.ndarray
            Array of q values
        
        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            Hurst exponents, R-squared values, and standard errors
        """
        hurst_exponents = np.zeros(len(q_values))
        r_squared = np.zeros(len(q_values))
        std_errors = np.zeros(len(q_values))
        
        for i, q in enumerate(q_values):
            # Get valid data points (non-NaN)
            valid_mask = ~np.isnan(moments[i, :])
            if np.sum(valid_mask) < 2:
                hurst_exponents[i] = np.nan
                r_squared[i] = np.nan
                std_errors[i] = np.nan
                continue
            
            tau_valid = tau_values[valid_mask]
            moments_valid = moments[i, valid_mask]
            
            # Log transform for linear regression
            log_tau = np.log(tau_valid)
            log_moments = np.log(moments_valid)
            
            # Linear regression: log(K_q(tau)) = q*H(q)*log(tau) + C
            # So: log_moments = q*H(q)*log_tau + C
            # Therefore: H(q) = slope / q
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(log_tau, log_moments)
                hurst_exponents[i] = slope / q
                r_squared[i] = r_value ** 2
                std_errors[i] = std_err / q
            except:
                hurst_exponents[i] = np.nan
                r_squared[i] = np.nan
                std_errors[i] = np.nan
        
        return hurst_exponents, r_squared, std_errors

    def _select_backend(self, data_length: int) -> str:
        """
        Select the best available backend for computation.
        
        Parameters
        ----------
        data_length : int
            Length of the input data
        
        Returns
        -------
        str
            Selected backend ('jax', 'numba', or 'numpy')
        """
        use_jax = self.parameters['use_jax']
        use_numba = self.parameters['use_numba']
        
        if use_jax is True and JAX_AVAILABLE:
            return 'jax'
        elif use_numba is True and NUMBA_AVAILABLE:
            return 'numba'
        elif use_jax is False and use_numba is False:
            return 'numpy'
        
        # Auto-select based on data size and availability
        if JAX_AVAILABLE and data_length > 1000:
            return 'jax'
        elif NUMBA_AVAILABLE and data_length > 100:
            return 'numba'
        else:
            return 'numpy'

    def estimate(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Estimate the generalized Hurst exponent using the GHE method.
        
        Parameters
        ----------
        data : np.ndarray
            Time series data to analyze
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing estimation results
        """
        # Validate input
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        if len(data) < 10:
            raise ValueError("Data must have at least 10 points")
        
        # Get parameters
        q_values = np.array(self.parameters['q_values'])
        tau_min = self.parameters['tau_min']
        tau_max = self.parameters['tau_max'] or min(len(data) // 4, 50)
        tau_step = self.parameters['tau_step']
        
        # Generate time lags
        tau_values = np.arange(tau_min, tau_max + 1, tau_step)
        
        if len(tau_values) < 2:
            raise ValueError("Not enough time lags for analysis")
        
        # Select backend
        backend = self._select_backend(len(data))
        
        # Compute q-th moments
        try:
            if backend == 'jax':
                moments = self._compute_qth_moments_jax(data, q_values, tau_values)
            elif backend == 'numba':
                moments = self._compute_qth_moments_numba(data, q_values, tau_values)
            else:
                moments = self._compute_qth_moments_numpy(data, q_values, tau_values)
        except Exception as e:
            warnings.warn(f"Backend {backend} failed, falling back to NumPy: {e}")
            moments = self._compute_qth_moments_numpy(data, q_values, tau_values)
            backend = 'numpy'
        
        # Estimate Hurst exponents
        hurst_exponents, r_squared, std_errors = self._estimate_hurst_exponents(
            tau_values, moments, q_values
        )
        
        # Compute average Hurst exponent (for q=2, which corresponds to standard Hurst)
        q2_idx = np.where(np.abs(q_values - 2.0) < 1e-6)[0]
        if len(q2_idx) > 0:
            main_hurst = hurst_exponents[q2_idx[0]]
        else:
            # If q=2 not available, use the closest q value
            q2_idx = np.argmin(np.abs(q_values - 2.0))
            main_hurst = hurst_exponents[q2_idx]
        
        # Store results
        self.results = {
            'hurst_parameter': main_hurst,
            'generalized_hurst_exponents': hurst_exponents,
            'q_values': q_values,
            'tau_values': tau_values,
            'moments': moments,
            'r_squared': r_squared,
            'std_errors': std_errors,
            'backend_used': backend,
            'success': True,
            'method': 'GHE',
            'data_length': len(data),
            'n_tau': len(tau_values),
            'n_q': len(q_values)
        }
        
        return self.results

    def plot_scaling_behavior(self, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Plot the scaling behavior of q-th moments.
        
        Parameters
        ----------
        figsize : Tuple[int, int], optional
            Figure size. Default: (12, 8)
        
        Returns
        -------
        matplotlib.figure.Figure
            The created figure
        """
        if not self.results or not self.results.get('success', False):
            raise ValueError("No successful estimation results available")
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle('GHE Scaling Behavior Analysis', fontsize=16)
        
        q_values = self.results['q_values']
        tau_values = self.results['tau_values']
        moments = self.results['moments']
        hurst_exponents = self.results['generalized_hurst_exponents']
        
        # Plot 1: Log-log plot of moments vs tau
        ax1 = axes[0, 0]
        for i, q in enumerate(q_values):
            valid_mask = ~np.isnan(moments[i, :])
            if np.sum(valid_mask) > 1:
                ax1.loglog(tau_values[valid_mask], moments[i, valid_mask], 
                          'o-', label=f'q={q:.1f}', alpha=0.7)
        ax1.set_xlabel('Time Lag τ')
        ax1.set_ylabel('K_q(τ)')
        ax1.set_title('Scaling of q-th Moments')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Hurst exponents vs q
        ax2 = axes[0, 1]
        valid_mask = ~np.isnan(hurst_exponents)
        ax2.plot(q_values[valid_mask], hurst_exponents[valid_mask], 'bo-', linewidth=2, markersize=6)
        ax2.axhline(y=0.5, color='r', linestyle='--', alpha=0.7, label='H=0.5 (no correlation)')
        ax2.set_xlabel('q')
        ax2.set_ylabel('H(q)')
        ax2.set_title('Generalized Hurst Exponent')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: R-squared values
        ax3 = axes[1, 0]
        r_squared = self.results['r_squared']
        valid_mask = ~np.isnan(r_squared)
        ax3.bar(q_values[valid_mask], r_squared[valid_mask], alpha=0.7)
        ax3.set_xlabel('q')
        ax3.set_ylabel('R²')
        ax3.set_title('Goodness of Fit (R²)')
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Standard errors
        ax4 = axes[1, 1]
        std_errors = self.results['std_errors']
        valid_mask = ~np.isnan(std_errors)
        ax4.bar(q_values[valid_mask], std_errors[valid_mask], alpha=0.7)
        ax4.set_xlabel('q')
        ax4.set_ylabel('Standard Error')
        ax4.set_title('Estimation Uncertainty')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def get_multifractal_spectrum(self) -> Dict[str, np.ndarray]:
        """
        Compute the multifractal spectrum from generalized Hurst exponents.
        
        Returns
        -------
        Dict[str, np.ndarray]
            Dictionary containing multifractal spectrum parameters
        """
        if not self.results or not self.results.get('success', False):
            raise ValueError("No successful estimation results available")
        
        q_values = self.results['q_values']
        hurst_exponents = self.results['generalized_hurst_exponents']
        
        # Remove NaN values
        valid_mask = ~np.isnan(hurst_exponents)
        q_valid = q_values[valid_mask]
        h_valid = hurst_exponents[valid_mask]
        
        if len(q_valid) < 3:
            return {'alpha': np.array([]), 'f_alpha': np.array([])}
        
        # Compute multifractal spectrum
        # α = H(q) + q * H'(q)
        # f(α) = q * α - τ(q)
        # where τ(q) = q * H(q) - 1
        
        # Compute derivatives using finite differences
        if len(q_valid) > 1:
            dH_dq = np.gradient(h_valid, q_valid)
            alpha = h_valid + q_valid * dH_dq
            tau_q = q_valid * h_valid - 1
            f_alpha = q_valid * alpha - tau_q
        else:
            alpha = h_valid
            f_alpha = np.zeros_like(alpha)
        
        return {
            'alpha': alpha,
            'f_alpha': f_alpha,
            'q_values': q_valid,
            'hurst_exponents': h_valid
        }


# Example usage and testing
if __name__ == "__main__":
    # Generate test data
    np.random.seed(42)
    N = 1000
    
    # Generate fractional Brownian motion
    H_true = 0.7
    t = np.linspace(0, 1, N)
    fbm = np.cumsum(np.random.normal(0, 1, N) * (t[1] - t[0]) ** H_true)
    
    # Test GHE estimator
    ghe = GHEEstimator(q_values=[1, 2, 3, 4, 5], tau_min=2, tau_max=50)
    results = ghe.estimate(fbm)
    
    print("GHE Estimation Results:")
    print(f"Main Hurst Parameter (q=2): {results['hurst_parameter']:.4f}")
    print(f"True Hurst Parameter: {H_true:.4f}")
    print(f"Backend Used: {results['backend_used']}")
    print(f"Generalized Hurst Exponents: {results['generalized_hurst_exponents']}")
    
    # Plot results
    fig = ghe.plot_scaling_behavior()
    plt.show()
