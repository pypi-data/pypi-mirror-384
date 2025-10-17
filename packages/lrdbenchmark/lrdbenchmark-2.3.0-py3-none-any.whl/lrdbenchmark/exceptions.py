"""
Custom exception hierarchy for LRDBenchmark.

This module defines all custom exceptions used throughout the LRDBenchmark
package, providing clear error categorization and helpful error messages.
"""


class LRDBenchmarkError(Exception):
    """Base exception class for all LRDBenchmark errors."""
    pass


class EstimatorError(LRDBenchmarkError):
    """Raised when estimator-specific errors occur."""
    
    def __init__(self, message: str, estimator_name: str = None, suggestions: list = None):
        super().__init__(message)
        self.estimator_name = estimator_name
        self.suggestions = suggestions or []
        
        if suggestions:
            self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
        else:
            self.full_message = message
    
    def __str__(self):
        return self.full_message


class DataGenerationError(LRDBenchmarkError):
    """Raised when data generation fails."""
    
    def __init__(self, message: str, model_name: str = None, suggestions: list = None):
        super().__init__(message)
        self.model_name = model_name
        self.suggestions = suggestions or [
            "Try reducing the data length or using a different generation method",
            "Check if the model parameters are within valid ranges",
            "Consider using CPU-only mode if GPU issues occur",
            "See: https://lrdbenchmark.readthedocs.io/data-generation-troubleshooting"
        ]
        
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in self.suggestions)
    
    def __str__(self):
        return self.full_message


class OptimizationError(LRDBenchmarkError):
    """Raised when optimization backend errors occur."""
    
    def __init__(self, message: str, framework: str = None, suggestions: list = None):
        super().__init__(message)
        self.framework = framework
        self.suggestions = suggestions or [
            "Try using a different optimization framework (numpy, numba, jax)",
            "Check if the required dependencies are installed",
            "Consider using CPU-only mode if GPU issues occur",
            "See: https://lrdbenchmark.readthedocs.io/optimization-troubleshooting"
        ]
        
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in self.suggestions)
    
    def __str__(self):
        return self.full_message


class GPUMemoryError(LRDBenchmarkError):
    """Raised when GPU memory issues occur."""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error
        
        # Add helpful suggestions to the error message
        suggestions = [
            "Try setting use_gpu=False to use CPU-only mode",
            "Reduce batch_size or sequence length",
            "Clear GPU cache with torch.cuda.empty_cache()",
            "See: https://lrdbenchmark.readthedocs.io/gpu-troubleshooting"
        ]
        
        self.suggestions = suggestions
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    
    def __str__(self):
        return self.full_message


class ValidationError(LRDBenchmarkError):
    """Raised when parameter validation fails."""
    
    def __init__(self, message: str, parameter_name: str = None, valid_range: str = None):
        super().__init__(message)
        self.parameter_name = parameter_name
        self.valid_range = valid_range
        
        suggestions = []
        if parameter_name:
            suggestions.append(f"Check the {parameter_name} parameter")
        if valid_range:
            suggestions.append(f"Valid range: {valid_range}")
        suggestions.extend([
            "See the parameter documentation for valid values",
            "Check: https://lrdbenchmark.readthedocs.io/parameter-reference"
        ])
        
        self.suggestions = suggestions
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    
    def __str__(self):
        return self.full_message


class BackendError(LRDBenchmarkError):
    """Raised when optimization backend selection fails."""
    
    def __init__(self, message: str, available_backends: list = None):
        super().__init__(message)
        self.available_backends = available_backends or []
        
        suggestions = [
            "Try explicitly setting the optimization framework",
            "Check if required dependencies are installed",
            "Use 'auto' mode to let the system choose the best backend"
        ]
        
        if available_backends:
            suggestions.append(f"Available backends: {', '.join(available_backends)}")
        
        suggestions.append("See: https://lrdbenchmark.readthedocs.io/backend-selection")
        
        self.suggestions = suggestions
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    
    def __str__(self):
        return self.full_message


class BenchmarkError(LRDBenchmarkError):
    """Raised when benchmark execution fails."""
    
    def __init__(self, message: str, benchmark_name: str = None, suggestions: list = None):
        super().__init__(message)
        self.benchmark_name = benchmark_name
        self.suggestions = suggestions or [
            "Check if all required estimators are available",
            "Verify that the data is in the correct format",
            "Try running individual estimators first to isolate the issue",
            "See: https://lrdbenchmark.readthedocs.io/benchmark-troubleshooting"
        ]
        
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in self.suggestions)
    
    def __str__(self):
        return self.full_message


class ModelError(LRDBenchmarkError):
    """Raised when model loading or inference fails."""
    
    def __init__(self, message: str, model_name: str = None, suggestions: list = None):
        super().__init__(message)
        self.model_name = model_name
        self.suggestions = suggestions or [
            "Check if the model file exists and is accessible",
            "Verify that the model is compatible with the current version",
            "Try re-downloading the model if it's corrupted",
            "See: https://lrdbenchmark.readthedocs.io/model-troubleshooting"
        ]
        
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in self.suggestions)
    
    def __str__(self):
        return self.full_message


class ConfigurationError(LRDBenchmarkError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None, valid_values: list = None):
        super().__init__(message)
        self.config_key = config_key
        self.valid_values = valid_values or []
        
        suggestions = []
        if config_key:
            suggestions.append(f"Check the {config_key} configuration")
        if valid_values:
            suggestions.append(f"Valid values: {', '.join(map(str, valid_values))}")
        suggestions.extend([
            "See the configuration documentation for valid options",
            "Check: https://lrdbenchmark.readthedocs.io/configuration-guide"
        ])
        
        self.suggestions = suggestions
        self.full_message = f"{message}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    
    def __str__(self):
        return self.full_message


class DependencyError(LRDBenchmarkError):
    """Raised when required dependencies are missing."""
    
    def __init__(self, missing_dependency: str, install_command: str = None):
        message = f"Missing dependency: {missing_dependency}"
        if install_command:
            message += f"\nInstall with: {install_command}"
        super().__init__(message)
        self.missing_dependency = missing_dependency
        self.install_command = install_command
