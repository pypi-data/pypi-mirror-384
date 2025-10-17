#!/usr/bin/env python3
"""
Robust Feature Extractor for LRDBenchmark

This module provides robust feature extraction methods that handle extreme values,
heavy-tailed data, and NaN values gracefully.
"""

import numpy as np
import warnings
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from scipy.fft import fft, fftfreq
import logging

logger = logging.getLogger(__name__)


class RobustFeatureExtractor:
    """
    Robust feature extractor that handles extreme values and heavy-tailed data.
    
    This extractor uses robust statistical measures and provides fallback
    mechanisms for handling extreme values that would break standard methods.
    """
    
    def __init__(self, 
                 outlier_threshold: float = 3.0,
                 winsorize_limits: Tuple[float, float] = (0.01, 0.99),
                 min_data_length: int = 10):
        """
        Initialize the robust feature extractor.
        
        Parameters
        ----------
        outlier_threshold : float
            Threshold for outlier detection (in IQR multiples)
        winsorize_limits : tuple
            Limits for winsorization (lower, upper percentiles)
        min_data_length : int
            Minimum data length required for feature extraction
        """
        self.outlier_threshold = outlier_threshold
        self.winsorize_limits = winsorize_limits
        self.min_data_length = min_data_length
    
    def extract_features(self, data: np.ndarray, 
                        feature_types: Optional[List[str]] = None) -> np.ndarray:
        """
        Extract robust features from time series data.
        
        Parameters
        ----------
        data : np.ndarray
            Input time series data
        feature_types : list, optional
            Types of features to extract. If None, extracts all available types.
            
        Returns
        -------
        np.ndarray
            Feature vector
        """
        data = np.asarray(data, dtype=np.float64)
        
        # Validate input
        if len(data) < self.min_data_length:
            logger.warning(f"Data too short ({len(data)} < {self.min_data_length}), returning zeros")
            return np.zeros(50)  # Return fixed-size zero vector
        
        # Check for NaN or infinite values
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            logger.warning("Data contains NaN or infinite values, cleaning...")
            data = self._clean_data(data)
        
        # Default feature types if not specified
        if feature_types is None:
            feature_types = ['robust_stats', 'autocorr', 'spectral', 'dfa', 'wavelet']
        
        features = []
        
        for feature_type in feature_types:
            try:
                if feature_type == 'robust_stats':
                    features.extend(self._extract_robust_statistics(data))
                elif feature_type == 'autocorr':
                    features.extend(self._extract_robust_autocorrelation(data))
                elif feature_type == 'spectral':
                    features.extend(self._extract_robust_spectral(data))
                elif feature_type == 'dfa':
                    features.extend(self._extract_robust_dfa(data))
                elif feature_type == 'wavelet':
                    features.extend(self._extract_robust_wavelet(data))
                else:
                    logger.warning(f"Unknown feature type: {feature_type}")
            except Exception as e:
                logger.warning(f"Failed to extract {feature_type} features: {e}")
                # Add zeros for failed feature type
                if feature_type == 'robust_stats':
                    features.extend([0.0] * 15)
                elif feature_type == 'autocorr':
                    features.extend([0.0] * 5)
                elif feature_type == 'spectral':
                    features.extend([0.0] * 8)
                elif feature_type == 'dfa':
                    features.extend([0.0] * 6)
                elif feature_type == 'wavelet':
                    features.extend([0.0] * 6)
        
        return np.array(features)
    
    def _clean_data(self, data: np.ndarray) -> np.ndarray:
        """Clean data by removing NaN and infinite values."""
        # Remove NaN and infinite values
        mask = np.isfinite(data)
        if np.sum(mask) < self.min_data_length:
            logger.error("Too few finite values after cleaning")
            return np.zeros(self.min_data_length)
        
        return data[mask]
    
    def _extract_robust_statistics(self, data: np.ndarray) -> List[float]:
        """Extract robust statistical features."""
        features = []
        
        # Robust central tendency measures
        features.extend([
            np.median(data),  # More robust than mean
            np.percentile(data, 25),  # Q1
            np.percentile(data, 75),  # Q3
            np.percentile(data, 10),  # P10
            np.percentile(data, 90),  # P90
        ])
        
        # Robust measures of spread
        iqr = np.percentile(data, 75) - np.percentile(data, 25)
        mad = np.median(np.abs(data - np.median(data)))  # Median Absolute Deviation
        
        features.extend([
            iqr,
            mad,
            iqr / np.median(np.abs(data)) if np.median(np.abs(data)) > 0 else 0,  # Robust CV
            np.percentile(data, 95) - np.percentile(data, 5),  # 90% range
        ])
        
        # Robust skewness and kurtosis
        try:
            # Use robust measures
            q1, q2, q3 = np.percentile(data, [25, 50, 75])
            robust_skew = (q3 - 2*q2 + q1) / (q3 - q1) if q3 != q1 else 0
            features.append(robust_skew)
            
            # Robust kurtosis using percentiles
            p10, p90 = np.percentile(data, [10, 90])
            robust_kurt = (q3 - q1) / (p90 - p10) if p90 != p10 else 1
            features.append(robust_kurt)
        except:
            features.extend([0.0, 1.0])
        
        # Outlier ratio
        q1, q3 = np.percentile(data, [25, 75])
        outlier_threshold = self.outlier_threshold * (q3 - q1)
        outliers = np.sum((data < q1 - outlier_threshold) | (data > q3 + outlier_threshold))
        features.append(outliers / len(data))
        
        # Data range and extremes
        features.extend([
            np.max(data) - np.min(data),  # Range
            np.max(np.abs(data)),  # Max absolute value
            np.sum(np.abs(data) > 3 * mad) / len(data) if mad > 0 else 0,  # Extreme value ratio
        ])
        
        return features
    
    def _extract_robust_autocorrelation(self, data: np.ndarray) -> List[float]:
        """Extract robust autocorrelation features."""
        features = []
        lags = [1, 2, 5, 10, 20]
        
        for lag in lags:
            if len(data) > lag:
                try:
                    # Use Spearman correlation (more robust to outliers)
                    corr, _ = stats.spearmanr(data[:-lag], data[lag:])
                    features.append(corr if not np.isnan(corr) else 0.0)
                except:
                    features.append(0.0)
            else:
                features.append(0.0)
        
        return features
    
    def _extract_robust_spectral(self, data: np.ndarray) -> List[float]:
        """Extract robust spectral features."""
        features = []
        
        if len(data) < 4:
            return [0.0] * 8
        
        try:
            # Winsorize data before FFT to reduce impact of extreme values
            data_winsorized = self._winsorize_data(data)
            
            # FFT
            fft_vals = np.abs(fft(data_winsorized))
            freqs = fftfreq(len(data_winsorized))
            
            # Only use positive frequencies
            positive_mask = freqs > 0
            if np.sum(positive_mask) < 2:
                return [0.0] * 8
            
            fft_positive = fft_vals[positive_mask]
            freqs_positive = freqs[positive_mask]
            
            # Robust spectral features
            features.extend([
                np.median(fft_positive),  # Median power
                np.percentile(fft_positive, 75) - np.percentile(fft_positive, 25),  # IQR
                np.max(fft_positive),  # Peak power
                np.argmax(fft_positive) / len(fft_positive),  # Normalized peak frequency
            ])
            
            # Spectral slope (robust)
            if len(freqs_positive) > 2:
                log_freqs = np.log(freqs_positive + 1e-8)
                log_fft = np.log(fft_positive + 1e-8)
                
                # Use robust regression
                try:
                    slope, _ = stats.linregress(log_freqs, log_fft)
                    features.append(slope)
                except:
                    features.append(-1.0)
            else:
                features.append(-1.0)
            
            # Spectral centroid
            if np.sum(fft_positive) > 0:
                centroid = np.sum(freqs_positive * fft_positive) / np.sum(fft_positive)
                features.append(centroid)
            else:
                features.append(0.0)
            
            # Spectral rolloff (90th percentile)
            sorted_fft = np.sort(fft_positive)
            rolloff_idx = int(0.9 * len(sorted_fft))
            features.append(sorted_fft[rolloff_idx] if rolloff_idx < len(sorted_fft) else sorted_fft[-1])
            
            # Spectral bandwidth
            if np.sum(fft_positive) > 0:
                centroid = np.sum(freqs_positive * fft_positive) / np.sum(fft_positive)
                bandwidth = np.sqrt(np.sum(((freqs_positive - centroid) ** 2) * fft_positive) / np.sum(fft_positive))
                features.append(bandwidth)
            else:
                features.append(0.0)
            
        except Exception as e:
            logger.warning(f"Spectral feature extraction failed: {e}")
            features = [0.0] * 8
        
        return features
    
    def _extract_robust_dfa(self, data: np.ndarray) -> List[float]:
        """Extract robust Detrended Fluctuation Analysis features."""
        features = []
        
        if len(data) < 20:
            return [0.0] * 6
        
        try:
            # Simplified DFA implementation
            scales = [4, 8, 16, 32]
            fluctuations = []
            
            for scale in scales:
                if len(data) >= scale * 4:  # Need enough data
                    # Divide data into segments
                    n_segments = len(data) // scale
                    if n_segments < 2:
                        fluctuations.append(0.0)
                        continue
                    
                    # Calculate fluctuation for this scale
                    fluctuation = self._calculate_dfa_fluctuation(data, scale, n_segments)
                    fluctuations.append(fluctuation)
                else:
                    fluctuations.append(0.0)
            
            features.extend(fluctuations)
            
            # DFA slope (if we have enough points)
            valid_fluctuations = [(scales[i], f) for i, f in enumerate(fluctuations) if f > 0]
            if len(valid_fluctuations) >= 2:
                scales_vals, fluct_vals = zip(*valid_fluctuations)
                log_scales = np.log(scales_vals)
                log_fluct = np.log(fluct_vals)
                
                try:
                    slope, _ = stats.linregress(log_scales, log_fluct)
                    features.append(slope)
                except:
                    features.append(0.0)
            else:
                features.append(0.0)
            
        except Exception as e:
            logger.warning(f"DFA feature extraction failed: {e}")
            features = [0.0] * 6
        
        return features
    
    def _calculate_dfa_fluctuation(self, data: np.ndarray, scale: int, n_segments: int) -> float:
        """Calculate DFA fluctuation for a given scale."""
        try:
            # Reshape data into segments
            segments = data[:n_segments * scale].reshape(n_segments, scale)
            fluctuations = []
            
            for segment in segments:
                # Detrend by removing linear trend
                x = np.arange(len(segment))
                trend = np.polyfit(x, segment, 1)
                detrended = segment - (trend[0] * x + trend[1])
                
                # Calculate fluctuation
                fluctuation = np.sqrt(np.mean(detrended ** 2))
                fluctuations.append(fluctuation)
            
            return np.mean(fluctuations)
        except:
            return 0.0
    
    def _extract_robust_wavelet(self, data: np.ndarray) -> List[float]:
        """Extract robust wavelet features."""
        features = []
        
        if len(data) < 8:
            return [0.0] * 6
        
        try:
            # Simplified wavelet analysis using differences
            # This is a simplified version - full wavelet would require pywt
            
            # First level differences (approximating high-pass filter)
            diff1 = np.diff(data)
            if len(diff1) > 0:
                features.extend([
                    np.median(np.abs(diff1)),
                    np.std(diff1),
                    np.sum(np.abs(diff1) > 2 * np.std(diff1)) / len(diff1)
                ])
            else:
                features.extend([0.0, 0.0, 0.0])
            
            # Second level differences
            if len(diff1) > 1:
                diff2 = np.diff(diff1)
                features.extend([
                    np.median(np.abs(diff2)),
                    np.std(diff2),
                    np.sum(np.abs(diff2) > 2 * np.std(diff2)) / len(diff2)
                ])
            else:
                features.extend([0.0, 0.0, 0.0])
            
        except Exception as e:
            logger.warning(f"Wavelet feature extraction failed: {e}")
            features = [0.0] * 6
        
        return features
    
    def _winsorize_data(self, data: np.ndarray) -> np.ndarray:
        """Winsorize data to reduce impact of extreme values."""
        lower_limit = np.percentile(data, self.winsorize_limits[0] * 100)
        upper_limit = np.percentile(data, self.winsorize_limits[1] * 100)
        
        return np.clip(data, lower_limit, upper_limit)
    
    def get_feature_names(self, feature_types: Optional[List[str]] = None) -> List[str]:
        """Get names of features that would be extracted."""
        if feature_types is None:
            feature_types = ['robust_stats', 'autocorr', 'spectral', 'dfa', 'wavelet']
        
        names = []
        
        if 'robust_stats' in feature_types:
            names.extend([
                'median', 'q1', 'q3', 'p10', 'p90',
                'iqr', 'mad', 'robust_cv', 'range_90pct',
                'robust_skew', 'robust_kurt', 'outlier_ratio',
                'data_range', 'max_abs', 'extreme_ratio'
            ])
        
        if 'autocorr' in feature_types:
            names.extend([f'autocorr_lag_{lag}' for lag in [1, 2, 5, 10, 20]])
        
        if 'spectral' in feature_types:
            names.extend([
                'spectral_median', 'spectral_iqr', 'spectral_peak',
                'spectral_peak_freq', 'spectral_slope', 'spectral_centroid',
                'spectral_rolloff', 'spectral_bandwidth'
            ])
        
        if 'dfa' in feature_types:
            names.extend([f'dfa_scale_{scale}' for scale in [4, 8, 16, 32]] + ['dfa_slope'])
        
        if 'wavelet' in feature_types:
            names.extend([
                'wavelet_diff1_median', 'wavelet_diff1_std', 'wavelet_diff1_outliers',
                'wavelet_diff2_median', 'wavelet_diff2_std', 'wavelet_diff2_outliers'
            ])
        
        return names
