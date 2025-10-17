"""
Tests for Unified Feature Extractor

This module provides comprehensive tests for the unified feature extraction pipeline.
"""

import numpy as np
import pytest
from scipy import stats
from lrdbenchmark.analysis.machine_learning.unified_feature_extractor import UnifiedFeatureExtractor

class TestUnifiedFeatureExtractor:
    """Test cases for UnifiedFeatureExtractor."""
    
    def test_extract_features_76_exact_count(self):
        """Test that exactly 76 features are extracted."""
        # Generate test data
        data = np.random.randn(1000)
        
        features = UnifiedFeatureExtractor.extract_features_76(data)
        
        assert len(features) == 76, f"Expected 76 features, got {len(features)}"
    
    def test_extract_features_76_no_nan_inf(self):
        """Test that no NaN or Inf values are in extracted features."""
        # Generate test data
        data = np.random.randn(1000)
        
        features = UnifiedFeatureExtractor.extract_features_76(data)
        
        assert not np.any(np.isnan(features)), "Features contain NaN values"
        assert not np.any(np.isinf(features)), "Features contain Inf values"
    
    def test_extract_features_76_deterministic(self):
        """Test that feature extraction is deterministic."""
        # Generate test data
        np.random.seed(42)
        data = np.random.randn(1000)
        
        features1 = UnifiedFeatureExtractor.extract_features_76(data)
        features2 = UnifiedFeatureExtractor.extract_features_76(data)
        
        np.testing.assert_array_almost_equal(features1, features2, decimal=10)
    
    def test_extract_features_76_different_lengths(self):
        """Test feature extraction with different data lengths."""
        lengths = [100, 500, 1000, 2000]
        
        for length in lengths:
            data = np.random.randn(length)
            features = UnifiedFeatureExtractor.extract_features_76(data)
            
            assert len(features) == 76, f"Expected 76 features for length {length}"
            assert not np.any(np.isnan(features)), f"NaN values for length {length}"
            assert not np.any(np.isinf(features)), f"Inf values for length {length}"
    
    def test_extract_features_29_subset(self):
        """Test that 29-feature extraction returns first 29 features."""
        data = np.random.randn(1000)
        
        features_76 = UnifiedFeatureExtractor.extract_features_76(data)
        features_29 = UnifiedFeatureExtractor.extract_features_29(data)
        
        assert len(features_29) == 29, f"Expected 29 features, got {len(features_29)}"
        np.testing.assert_array_almost_equal(features_29, features_76[:29], decimal=10)
    
    def test_extract_features_54_subset(self):
        """Test that 54-feature extraction returns first 54 features."""
        data = np.random.randn(1000)
        
        features_76 = UnifiedFeatureExtractor.extract_features_76(data)
        features_54 = UnifiedFeatureExtractor.extract_features_54(data)
        
        assert len(features_54) == 54, f"Expected 54 features, got {len(features_54)}"
        np.testing.assert_array_almost_equal(features_54, features_76[:54], decimal=10)
    
    def test_feature_names_76(self):
        """Test that feature names are correctly generated."""
        names = UnifiedFeatureExtractor.get_feature_names()
        
        assert len(names) == 76, f"Expected 76 feature names, got {len(names)}"
        assert all(isinstance(name, str) for name in names), "All names should be strings"
        assert len(set(names)) == len(names), "Feature names should be unique"
    
    def test_feature_names_29(self):
        """Test that 29-feature names are correctly generated."""
        names_76 = UnifiedFeatureExtractor.get_feature_names()
        names_29 = UnifiedFeatureExtractor.get_feature_names_29()
        
        assert len(names_29) == 29, f"Expected 29 feature names, got {len(names_29)}"
        assert names_29 == names_76[:29], "29-feature names should be first 29 of 76"
    
    def test_feature_names_54(self):
        """Test that 54-feature names are correctly generated."""
        names_76 = UnifiedFeatureExtractor.get_feature_names()
        names_54 = UnifiedFeatureExtractor.get_feature_names_54()
        
        assert len(names_54) == 54, f"Expected 54 feature names, got {len(names_54)}"
        assert names_54 == names_76[:54], "54-feature names should be first 54 of 76"
    
    def test_basic_statistical_features(self):
        """Test that basic statistical features are correctly computed."""
        data = np.array([1, 2, 3, 4, 5])
        
        features = UnifiedFeatureExtractor.extract_features_76(data)
        
        # Check first 10 features (basic statistics)
        assert abs(features[0] - np.mean(data)) < 1e-10, "Mean feature incorrect"
        assert abs(features[1] - np.std(data)) < 1e-10, "Std feature incorrect"
        assert abs(features[2] - np.var(data)) < 1e-10, "Var feature incorrect"
        assert abs(features[3] - np.min(data)) < 1e-10, "Min feature incorrect"
        assert abs(features[4] - np.max(data)) < 1e-10, "Max feature incorrect"
        assert abs(features[5] - np.median(data)) < 1e-10, "Median feature incorrect"
        assert abs(features[6] - np.percentile(data, 25)) < 1e-10, "Q25 feature incorrect"
        assert abs(features[7] - np.percentile(data, 75)) < 1e-10, "Q75 feature incorrect"
        assert abs(features[8] - stats.skew(data)) < 1e-10, "Skew feature incorrect"
        assert abs(features[9] - stats.kurtosis(data)) < 1e-10, "Kurtosis feature incorrect"
    
    def test_autocorrelation_features(self):
        """Test that autocorrelation features are correctly computed."""
        # Create data with known autocorrelation
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        features = UnifiedFeatureExtractor.extract_features_76(data)
        
        # Check autocorrelation features (indices 10-16)
        for i, lag in enumerate([1, 2, 5, 10, 20, 50, 100]):
            if len(data) > lag:
                expected = np.corrcoef(data[:-lag], data[lag:])[0, 1]
                if not np.isnan(expected):
                    assert abs(features[10 + i] - expected) < 1e-10, f"ACF lag {lag} incorrect"
    
    def test_spectral_features(self):
        """Test that spectral features are correctly computed."""
        # Create sinusoidal data
        t = np.linspace(0, 1, 1000)
        data = np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(1000)
        
        features = UnifiedFeatureExtractor.extract_features_76(data)
        
        # Check that spectral features are computed (indices 37-46)
        spectral_features = features[37:47]
        assert not np.any(np.isnan(spectral_features)), "Spectral features contain NaN"
        assert not np.any(np.isinf(spectral_features)), "Spectral features contain Inf"
    
    def test_edge_cases(self):
        """Test edge cases for feature extraction."""
        # Very short data
        data_short = np.array([1, 2, 3])
        features_short = UnifiedFeatureExtractor.extract_features_76(data_short)
        assert len(features_short) == 76, "Short data should still return 76 features"
        assert not np.any(np.isnan(features_short)), "Short data should not produce NaN"
        
        # Constant data
        data_constant = np.ones(100)
        features_constant = UnifiedFeatureExtractor.extract_features_76(data_constant)
        assert len(features_constant) == 76, "Constant data should return 76 features"
        assert not np.any(np.isnan(features_constant)), "Constant data should not produce NaN"
        
        # Data with zeros
        data_zeros = np.zeros(100)
        features_zeros = UnifiedFeatureExtractor.extract_features_76(data_zeros)
        assert len(features_zeros) == 76, "Zero data should return 76 features"
        assert not np.any(np.isnan(features_zeros)), "Zero data should not produce NaN"
    
    def test_feature_consistency(self):
        """Test that features are consistent across different data types."""
        # Normal data
        data_normal = np.random.randn(1000)
        features_normal = UnifiedFeatureExtractor.extract_features_76(data_normal)
        
        # Uniform data
        data_uniform = np.random.uniform(-1, 1, 1000)
        features_uniform = UnifiedFeatureExtractor.extract_features_76(data_uniform)
        
        # Both should have same length and no NaN/Inf
        assert len(features_normal) == len(features_uniform) == 76
        assert not np.any(np.isnan(features_normal)) and not np.any(np.isinf(features_normal))
        assert not np.any(np.isnan(features_uniform)) and not np.any(np.isinf(features_uniform))
    
    def test_performance(self):
        """Test that feature extraction is reasonably fast."""
        import time
        
        data = np.random.randn(10000)
        
        start_time = time.time()
        features = UnifiedFeatureExtractor.extract_features_76(data)
        end_time = time.time()
        
        extraction_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second for 10k points)
        assert extraction_time < 1.0, f"Feature extraction too slow: {extraction_time:.3f}s"
        assert len(features) == 76, "Performance test should still return 76 features"

if __name__ == "__main__":
    pytest.main([__file__])
