"""
Unified Gradient Boosting Estimator for Hurst Parameter Estimation

This module provides a Gradient Boosting estimator that uses the unified feature extraction
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

class GradientBoostingEstimator(BaseEstimator):
    """
    Gradient Boosting estimator using unified feature extraction.
    Works with pre-trained models expecting 54 features.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the Gradient Boosting estimator.
        
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
        """Get the default path for the pre-trained Gradient Boosting model."""
        return "models/gradient_boosting_estimator.joblib"
    
    def _load_model(self):
        """Load the pre-trained Gradient Boosting model."""
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
            self.feature_names = model_data.get('feature_names', UnifiedFeatureExtractor.get_feature_names_54())
            self.is_loaded = True
            logger.info(f"Gradient Boosting model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load Gradient Boosting model: {e}")
            self.is_loaded = False
    
    def estimate(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Estimate Hurst parameter using Gradient Boosting with unified features.
        
        Args:
            data: Time series data
            
        Returns:
            Dictionary containing estimation results
        """
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded:
            logger.error("Gradient Boosting model not loaded")
            return {
                'hurst_parameter': np.nan,
                'method': 'gradient_boosting',
                'error': 'Model not loaded',
                'features_used': 0
            }
        
        try:
            # Extract first 54 features using unified extractor
            features = UnifiedFeatureExtractor.extract_features_54(data)
            
            # Ensure we have exactly 54 features
            if len(features) != 54:
                logger.warning(f"Expected 54 features, got {len(features)}")
                # Pad or truncate as needed
                if len(features) < 54:
                    features = np.pad(features, (0, 54 - len(features)), 'constant')
                else:
                    features = features[:54]
            
            # Scale features
            features_scaled = self.scaler.transform(features.reshape(1, -1))
            
            # Make prediction
            H_estimate = self.model.predict(features_scaled)[0]
            
            return {
                'hurst_parameter': float(H_estimate),
                'method': 'gradient_boosting',
                'features_used': 54,
                'feature_names': self.feature_names[:54]
            }
            
        except Exception as e:
            logger.error(f"Gradient Boosting estimation failed: {e}")
            return {
                'hurst_parameter': np.nan,
                'method': 'gradient_boosting',
                'error': str(e),
                'features_used': 54
            }
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """
        Get feature importance from the Gradient Boosting model.
        
        Returns:
            Array of feature importances or None if model not loaded
        """
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded or self.model is None:
            return None
            
        try:
            return self.model.feature_importances_
        except Exception as e:
            logger.error(f"Failed to get feature importance: {e}")
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