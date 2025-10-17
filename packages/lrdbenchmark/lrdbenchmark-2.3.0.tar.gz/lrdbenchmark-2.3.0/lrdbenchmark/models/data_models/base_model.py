"""
Base model class for all stochastic processes.

This module provides the abstract base class that all stochastic models
should inherit from, ensuring consistent interface and functionality.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
import numpy as np


class BaseModel(ABC):
    """
    Abstract base class for all stochastic models.

    This class defines the interface that all stochastic models must implement,
    including methods for parameter validation, data generation, and model
    information retrieval.
    """

    def __init__(self, **kwargs):
        """
        Initialize the base model.

        Parameters
        ----------
        **kwargs : dict
            Model-specific parameters
        """
        self.parameters = kwargs
        self._validate_parameters()

    @abstractmethod
    def _validate_parameters(self) -> None:
        """
        Validate model parameters.

        This method should be implemented by each model to ensure
        that the provided parameters are valid for the specific model.
        """
        pass

    @abstractmethod
    def generate(self, n: int, seed: Optional[int] = None) -> np.ndarray:
        """
        Generate synthetic data from the model.

        Parameters
        ----------
        n : int
            Length of the time series to generate
        seed : int, optional
            Random seed for reproducibility

        Returns
        -------
        np.ndarray
            Generated time series of length n
        """
        pass
    
    def generate_batch(self, n_series: int, n_points: int, seed: Optional[int] = None) -> np.ndarray:
        """
        Generate multiple time series from the model.

        Parameters
        ----------
        n_series : int
            Number of time series to generate
        n_points : int
            Length of each time series
        seed : int, optional
            Random seed for reproducibility

        Returns
        -------
        np.ndarray
            Generated time series array of shape (n_series, n_points)
        """
        if seed is not None:
            np.random.seed(seed)
        
        batch = np.zeros((n_series, n_points))
        for i in range(n_series):
            # Use different seed for each series to ensure independence
            series_seed = seed + i if seed is not None else None
            batch[i] = self.generate(n_points, seed=series_seed)
        
        return batch
    
    def generate_streaming(self, n: int, chunk_size: int = 1000, seed: Optional[int] = None):
        """
        Generate data in streaming fashion for very large datasets.

        Parameters
        ----------
        n : int
            Total length of the time series to generate
        chunk_size : int, default=1000
            Size of each chunk
        seed : int, optional
            Random seed for reproducibility

        Yields
        ------
        np.ndarray
            Chunks of generated data
        """
        if seed is not None:
            np.random.seed(seed)
        
        for start in range(0, n, chunk_size):
            end = min(start + chunk_size, n)
            chunk_length = end - start
            yield self.generate(chunk_length, seed=seed + start if seed is not None else None)

    @abstractmethod
    def get_theoretical_properties(self) -> Dict[str, Any]:
        """
        Get theoretical properties of the model.

        Returns
        -------
        dict
            Dictionary containing theoretical properties such as
            autocorrelation function, power spectral density, etc.
        """
        pass

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current model parameters.

        Returns
        -------
        dict
            Current model parameters
        """
        return self.parameters.copy()

    def set_parameters(self, **kwargs) -> None:
        """
        Set model parameters.

        Parameters
        ----------
        **kwargs : dict
            New parameter values
        """
        self.parameters.update(kwargs)
        self._validate_parameters()

    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}({self.parameters})"

    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"{self.__class__.__name__}(parameters={self.parameters})"
