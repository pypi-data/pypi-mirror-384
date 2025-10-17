#!/usr/bin/env python3
"""
Adaptive Data Preprocessor for LRDBenchmark

This module provides adaptive data preprocessing based on data characteristics.
"""

import numpy as np
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class AdaptiveDataPreprocessor:
    """
    Adaptive data preprocessor that handles different data types and characteristics.
    
    This preprocessor automatically detects data characteristics and applies
    appropriate preprocessing strategies.
    """
    
    def __init__(self, 
                 outlier_threshold: float = 3.0,
                 winsorize_limits: Tuple[float, float] = (0.01, 0.99)):
        """
        Initialize the adaptive data preprocessor.
        
        Parameters
        ----------
        outlier_threshold : float
            Threshold for outlier detection (in IQR multiples)
        winsorize_limits : tuple
            Limits for winsorization (lower, upper percentiles)
        """
        self.outlier_threshold = outlier_threshold
        self.winsorize_limits = winsorize_limits
    
    def preprocess(self, data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Preprocess data based on its characteristics.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series data
            
        Returns
        -------
        tuple
            (processed_data, metadata)
        """
        data = np.asarray(data, dtype=np.float64)
        metadata = {'original_length': len(data)}
        
        # Clean data
        data_clean, clean_metadata = self._clean_data(data)
        metadata.update(clean_metadata)
        
        # Detect data type
        data_type = self._classify_data_type(data_clean)
        metadata['data_type'] = data_type
        
        # Apply appropriate preprocessing
        if data_type == 'heavy_tailed':
            data_processed, proc_metadata = self._preprocess_heavy_tailed(data_clean)
        elif data_type == 'trended':
            data_processed, proc_metadata = self._preprocess_trended(data_clean)
        elif data_type == 'outliers':
            data_processed, proc_metadata = self._preprocess_outliers(data_clean)
        else:
            data_processed, proc_metadata = self._preprocess_normal(data_clean)
        
        metadata.update(proc_metadata)
        
        return data_processed, metadata
    
    def _clean_data(self, data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Clean data by removing NaN and infinite values."""
        original_length = len(data)
        
        # Remove NaN and infinite values
        mask = np.isfinite(data)
        data_clean = data[mask]
        
        removed_count = original_length - len(data_clean)
        
        return data_clean, {
            'cleaned_length': len(data_clean),
            'removed_values': removed_count,
            'removal_ratio': removed_count / original_length if original_length > 0 else 0
        }
    
    def _classify_data_type(self, data: np.ndarray) -> str:
        """Classify the type of data based on its characteristics."""
        if len(data) < 10:
            return 'insufficient'
        
        # Check for heavy tails
        if self._is_heavy_tailed(data):
            return 'heavy_tailed'
        
        # Check for significant trends
        if self._has_significant_trend(data):
            return 'trended'
        
        # Check for outliers
        if self._has_outliers(data):
            return 'outliers'
        
        return 'normal'
    
    def _is_heavy_tailed(self, data: np.ndarray) -> bool:
        """Detect if data is heavy-tailed."""
        try:
            # Check kurtosis
            kurtosis = np.mean(((data - np.mean(data)) / np.std(data))**4) - 3
            if kurtosis > 10:  # High kurtosis threshold
                return True
        except:
            pass
        
        # Check for extreme values
        q99 = np.percentile(data, 99)
        q1 = np.percentile(data, 1)
        extreme_ratio = np.sum((data > q99) | (data < q1)) / len(data)
        
        return extreme_ratio > 0.02  # 2% extreme values threshold
    
    def _has_significant_trend(self, data: np.ndarray) -> bool:
        """Detect if data has significant trends."""
        if len(data) < 10:
            return False
        
        try:
            # Simple linear trend test
            x = np.arange(len(data))
            slope, _ = np.polyfit(x, data, 1)
            
            # Check if trend is significant relative to data variance
            trend_significance = abs(slope) * len(data) / np.std(data)
            return trend_significance > 2.0  # Threshold for significance
        except:
            return False
    
    def _has_outliers(self, data: np.ndarray) -> bool:
        """Detect if data has significant outliers."""
        if len(data) < 10:
            return False
        
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        outlier_threshold = self.outlier_threshold * iqr
        
        outliers = np.sum((data < q1 - outlier_threshold) | (data > q3 + outlier_threshold))
        outlier_ratio = outliers / len(data)
        
        return outlier_ratio > 0.01  # 1% outliers threshold
    
    def _preprocess_heavy_tailed(self, data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Preprocess heavy-tailed data."""
        # Winsorize extreme values
        q1, q99 = np.percentile(data, [self.winsorize_limits[0] * 100, self.winsorize_limits[1] * 100])
        data_winsorized = np.clip(data, q1, q99)
        
        # Log transform if all positive
        if np.all(data_winsorized > 0):
            data_log = np.log(data_winsorized + 1e-8)
            return data_log, {
                "method": "winsorize_log", 
                "q1": q1, 
                "q99": q99,
                "winsorized_count": np.sum((data < q1) | (data > q99))
            }
        else:
            return data_winsorized, {
                "method": "winsorize", 
                "q1": q1, 
                "q99": q99,
                "winsorized_count": np.sum((data < q1) | (data > q99))
            }
    
    def _preprocess_trended(self, data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Preprocess data with trends."""
        # Detrend using linear regression
        x = np.arange(len(data))
        slope, intercept = np.polyfit(x, data, 1)
        trend = slope * x + intercept
        data_detrended = data - trend
        
        return data_detrended, {
            "method": "detrend",
            "trend_slope": slope,
            "trend_intercept": intercept
        }
    
    def _preprocess_outliers(self, data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Preprocess data with outliers."""
        # Winsorize outliers
        q1, q3 = np.percentile(data, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - self.outlier_threshold * iqr
        upper_bound = q3 + self.outlier_threshold * iqr
        
        data_winsorized = np.clip(data, lower_bound, upper_bound)
        
        return data_winsorized, {
            "method": "winsorize_outliers",
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "winsorized_count": np.sum((data < lower_bound) | (data > upper_bound))
        }
    
    def _preprocess_normal(self, data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Preprocess normal data (minimal processing)."""
        # Just standardize
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if std_val > 0:
            data_standardized = (data - mean_val) / std_val
        else:
            data_standardized = data - mean_val
        
        return data_standardized, {
            "method": "standardize",
            "mean": mean_val,
            "std": std_val
        }
