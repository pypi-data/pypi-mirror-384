"""
Unified SVR Estimator for Hurst Parameter Estimation

This module provides an SVR estimator that uses the unified feature extraction
pipeline to work with pre-trained models.
"""

import numpy as np
import joblib
import os
from typing import Dict, Any, Optional, List
import logging

from lrdbenchmark.models.estimators.base_estimator import BaseEstimator
from .unified_feature_extractor import UnifiedFeatureExtractor

logger = logging.getLogger(__name__)

class SVREstimator(BaseEstimator):
    """
    SVR estimator using unified feature extraction.
    Works with pre-trained models expecting 29 features.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the SVR estimator.
        
        Args:
            model_path: Path to the pre-trained model. If None, uses default path.
        """
        super().__init__()
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.is_loaded = False
    
    def _validate_parameters(self) -> None:
        """Validate estimator parameters."""
        # For unified estimators, parameters are handled by the pre-trained models
        pass
        
    def _get_default_model_path(self) -> str:
        """Get the default path for the pre-trained SVR model."""
        return "models/svr_estimator.joblib"
    
    def _load_model(self):
        """Load the pre-trained SVR model."""
        if self.is_loaded:
            return
            
        if not os.path.exists(self.model_path):
            logger.warning(f"Pre-trained model not found at {self.model_path}")
            self.is_loaded = False
            return
            
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data.get('feature_names', UnifiedFeatureExtractor.get_feature_names_29())
            self.is_loaded = True
            logger.info(f"SVR model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load SVR model: {e}")
            self.is_loaded = False
    
    def estimate(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using SVR with unified features.
        
        Args:
            data: Time series data
            
        Returns:
            Dictionary containing estimation results
        """
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded:
            logger.error("SVR model not loaded")
            return {
                'hurst_parameter': np.nan,
                'method': 'svr',
                'error': 'Model not loaded',
                'features_used': 0
            }
        
        try:
            # Extract first 29 features using unified extractor
            features = UnifiedFeatureExtractor.extract_features_29(data)
            
            # Ensure we have exactly 29 features
            if len(features) != 29:
                logger.warning(f"Expected 29 features, got {len(features)}")
                # Pad or truncate as needed
                if len(features) < 29:
                    features = np.pad(features, (0, 29 - len(features)), 'constant')
                else:
                    features = features[:29]
            
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Make prediction
            H_estimate = self.model.predict(features_scaled)[0]
            
            return {
                'hurst_parameter': float(H_estimate),
                'method': 'svr',
                'features_used': 29,
                'feature_names': self.feature_names[:29]
            }
            
        except Exception as e:
            logger.error(f"SVR estimation failed: {e}")
            return {
                'hurst_parameter': np.nan,
                'method': 'svr',
                'error': str(e),
                'features_used': 29
            }
    
    def get_support_vectors(self) -> Optional[np.ndarray]:
        """
        Get support vectors from the SVR model.
        
        Returns:
            Array of support vectors or None if model not loaded
        """
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded or self.model is None:
            return None
            
        try:
            return self.model.support_vectors_
        except Exception as e:
            logger.error(f"Failed to get support vectors: {e}")
            return None
    
    def get_feature_names(self) -> Optional[List[str]]:
        """
        Get feature names used by the model.
        
        Returns:
            List of feature names or None if not available
        """
        if not self.is_loaded:
            self._load_model()
            
        return self.feature_names
    
    def is_model_available(self) -> bool:
        """
        Check if the pre-trained model is available.
        
        Returns:
            True if model is available and loaded
        """
        if not self.is_loaded:
            self._load_model()
        return self.is_loaded