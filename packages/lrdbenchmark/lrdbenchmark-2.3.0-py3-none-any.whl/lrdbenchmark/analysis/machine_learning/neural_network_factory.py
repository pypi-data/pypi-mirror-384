"""
Neural Network Factory for Hurst Parameter Estimation

This module provides a factory for creating various neural network architectures
suitable for benchmarking Hurst parameter estimation in time series data.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import logging
import pickle
import os
import json

# Import utility function for package data paths
try:
    from ...utils import get_neural_network_model_path
except ImportError:
    # Fallback for development
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from utils import get_neural_network_model_path

logger = logging.getLogger(__name__)

class NNArchitecture(Enum):
    """Available neural network architectures."""
    FFN = "feedforward"
    CNN = "convolutional"
    LSTM = "lstm"
    BILSTM = "bidirectional_lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    HYBRID_CNN_LSTM = "hybrid_cnn_lstm"
    RESNET = "resnet"

@dataclass
class NNConfig:
    """Configuration for neural network architecture."""
    architecture: NNArchitecture
    input_length: int
    hidden_dims: List[int] = None
    dropout_rate: float = 0.2
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    activation: str = "relu"
    optimizer: str = "adam"
    weight_decay: float = 1e-4
    
    # Architecture-specific parameters
    conv_filters: int = 64
    conv_kernel_size: int = 3
    lstm_units: int = 64
    transformer_heads: int = 8
    transformer_layers: int = 2
    resnet_blocks: int = 2
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [64, 32]

class BaseNeuralNetwork(nn.Module):
    """Base class for all neural network architectures with train-once, apply-many workflow."""
    
    def __init__(self, config: NNConfig, model_name: str = None):
        super().__init__()
        self.config = config
        self.device = self._get_optimal_device()
        self.is_trained = False
        self.training_history = None
        self.model_name = model_name or self.__class__.__name__.lower()
        self.model_dir = "models"
        os.makedirs(self.model_dir, exist_ok=True)
        # Don't move to device here, let subclasses handle it
    
    def _get_optimal_device(self):
        """Select optimal device with CUDA compatibility check."""
        if torch.cuda.is_available():
            try:
                # Test CUDA with small operation
                device = torch.device('cuda')
                test_tensor = torch.zeros(1).to(device)
                result = test_tensor + 1  # Test operation
                _ = result.cpu()  # Move result back to CPU to test full pipeline
                logger.info(f"CUDA device selected: {torch.cuda.get_device_name()}")
                return device
            except RuntimeError as e:
                if "CUDA" in str(e) or "kernel image" in str(e):
                    logger.warning(f"CUDA available but incompatible: {e}. Falling back to CPU.")
                    return torch.device('cpu')
                else:
                    logger.warning(f"CUDA test failed with unexpected error: {e}. Falling back to CPU.")
                    return torch.device('cpu')
            except Exception as e:
                logger.warning(f"CUDA test failed with exception: {e}. Falling back to CPU.")
                return torch.device('cpu')
        logger.info("CUDA not available, using CPU device")
        return torch.device('cpu')
        
    def forward(self, x):
        raise NotImplementedError("Subclasses must implement forward method")
    
    def predict(self, x: np.ndarray, batch_size: int = 32) -> np.ndarray:
        """Make predictions on new data with automatic device handling."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        self.eval()
        
        # Convert to PyTorch tensor and ensure correct device
        if isinstance(x, np.ndarray):
            x = torch.FloatTensor(x)
        if x.dim() == 1:
            x = x.unsqueeze(0)
        
        n_samples = x.shape[0]
        predictions = []
        
        # Process in batches to avoid GPU memory issues
        for i in range(0, n_samples, batch_size):
            batch_end = min(i + batch_size, n_samples)
            batch_x = x[i:batch_end]
            
            with torch.no_grad():
                # Ensure data is on correct device
                batch_x = batch_x.to(self.device)
                
                # Ensure correct input shape
                if len(batch_x.shape) == 1:
                    batch_x = batch_x.unsqueeze(0)  # Add batch dimension
                elif len(batch_x.shape) == 2:
                    # For 2D input (batch, sequence_length), we need to add feature dimension
                    # This will be handled by the individual network's forward method
                    pass
                
                batch_predictions = self.forward(batch_x)
                predictions.extend(batch_predictions.cpu().numpy().flatten())
                
                # Clear GPU memory
                del batch_predictions
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        
        return np.array(predictions)
    
    def train_model(self, X: np.ndarray, y: np.ndarray, 
                   validation_split: float = 0.2) -> Dict[str, List[float]]:
        """Train the neural network model."""
        # Convert to PyTorch tensors
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.FloatTensor(y).to(self.device)
        
        # Create data loaders
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        train_size = int((1 - validation_split) * len(dataset))
        val_size = len(dataset) - train_size
        train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
        
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=self.config.batch_size, shuffle=False)
        
        # Setup optimizer and loss
        optimizer = self._get_optimizer()
        criterion = nn.MSELoss()
        
        # Training history
        history = {"train_loss": [], "val_loss": []}
        
        # Training loop
        for epoch in range(self.config.epochs):
            # Training
            self.train()
            train_loss = 0.0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.forward(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Validation
            self.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    outputs = self.forward(batch_X)
                    loss = criterion(outputs.squeeze(), batch_y)
                    val_loss += loss.item()
            
            # Record history
            avg_train_loss = train_loss / len(train_loader)
            avg_val_loss = val_loss / len(val_loader)
            history["train_loss"].append(avg_train_loss)
            history["val_loss"].append(avg_val_loss)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}")
        
        # Mark as trained and save model
        self.is_trained = True
        self.training_history = history
        self.save_model()
        
        logger.info(f"Training completed: Final Train Loss = {avg_train_loss:.4f}, Val Loss = {avg_val_loss:.4f}")
        return history
    
    def _get_optimizer(self):
        """Get optimizer based on configuration."""
        if self.config.optimizer.lower() == "adam":
            return torch.optim.Adam(self.parameters(), lr=self.config.learning_rate, weight_decay=self.config.weight_decay)
        elif self.config.optimizer.lower() == "sgd":
            return torch.optim.SGD(self.parameters(), lr=self.config.learning_rate, weight_decay=self.config.weight_decay)
        else:
            return torch.optim.Adam(self.parameters(), lr=self.config.learning_rate, weight_decay=self.config.weight_decay)
    
    def save_model(self):
        """Save the trained model and configuration."""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
            
        model_path = os.path.join(self.model_dir, f"{self.model_name}_neural_network.pth")
        config_path = os.path.join(self.model_dir, f"{self.model_name}_neural_network_config.json")
        
        # Save model state
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': self.config.__dict__,
            'training_history': self.training_history,
            'is_trained': self.is_trained
        }, model_path)
        
        # Save config separately for easy loading
        config_dict = {
            'architecture': self.config.architecture.value,
            'input_length': self.config.input_length,
            'hidden_dims': self.config.hidden_dims,
            'dropout_rate': self.config.dropout_rate,
            'learning_rate': self.config.learning_rate,
            'batch_size': self.config.batch_size,
            'epochs': self.config.epochs,
            'activation': self.config.activation,
            'optimizer': self.config.optimizer,
            'weight_decay': self.config.weight_decay,
            'conv_filters': self.config.conv_filters,
            'conv_kernel_size': self.config.conv_kernel_size,
            'lstm_units': self.config.lstm_units,
            'transformer_heads': self.config.transformer_heads,
            'transformer_layers': self.config.transformer_layers,
            'resnet_blocks': self.config.resnet_blocks
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Model saved to {model_path}")
    
    def load_model(self, model_path: str = None):
        """Load a trained model with automatic device handling."""
        if model_path is None:
            # Try to get pretrained model from package first
            pretrained_model_path, pretrained_config_path = get_neural_network_model_path(self.model_name)
            if pretrained_model_path:
                model_path = pretrained_model_path
                logger.info(f"Using pretrained {self.model_name} model from package: {model_path}")
            else:
                # Fallback to local model directory
                model_path = os.path.join(self.model_dir, f"{self.model_name}_neural_network.pth")
                logger.info(f"Using local {self.model_name} model path: {model_path}")
        
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found: {model_path}")
            return False
            
        try:
            # Load with automatic device mapping
            checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
            self.load_state_dict(checkpoint['model_state_dict'])
            self.to(self.device)
            self.training_history = checkpoint['training_history']
            self.is_trained = checkpoint['is_trained']
            
            logger.info(f"Model loaded from {model_path} on device {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def is_model_trained(self) -> bool:
        """Check if model is trained."""
        return self.is_trained

class FeedforwardNetwork(BaseNeuralNetwork):
    """Basic feedforward neural network."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        layers = []
        input_dim = config.input_length
        
        for i, hidden_dim in enumerate(config.hidden_dims):
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU() if config.activation == "relu" else nn.Tanh())
            layers.append(nn.Dropout(config.dropout_rate))
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, 1))
        self.network = nn.Sequential(*layers)
        self.to(self.device)
    
    def forward(self, x):
        return self.network(x)

class ConvolutionalNetwork(BaseNeuralNetwork):
    """Convolutional neural network for time series."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.conv1 = nn.Conv1d(1, config.conv_filters, config.conv_kernel_size, padding=1)
        self.pool1 = nn.MaxPool1d(2)
        self.conv2 = nn.Conv1d(config.conv_filters, config.conv_filters * 2, config.conv_kernel_size, padding=1)
        self.pool2 = nn.MaxPool1d(2)
        
        # Calculate the size after convolutions
        conv_output_size = self._get_conv_output_size(config.input_length)
        
        self.fc1 = nn.Linear(conv_output_size, config.hidden_dims[0])
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc2 = nn.Linear(config.hidden_dims[0], 1)
        self.to(self.device)
    
    def _get_conv_output_size(self, input_length):
        """Calculate the output size after convolutions."""
        # Simulate forward pass to get output size
        x = torch.zeros(1, 1, input_length)
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        return x.view(1, -1).size(1)
    
    def forward(self, x):
        # Ensure input has correct shape: (batch, channels, length)
        if len(x.shape) == 2:
            x = x.unsqueeze(1)  # Add channel dimension
        
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        
        x = x.view(x.size(0), -1)  # Flatten
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        
        return x

class LSTMNetwork(BaseNeuralNetwork):
    """LSTM neural network for time series."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.lstm = nn.LSTM(input_size=1, hidden_size=config.lstm_units, 
                           batch_first=True, dropout=config.dropout_rate)
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc = nn.Linear(config.lstm_units, 1)
        self.to(self.device)
    
    def forward(self, x):
        # Ensure input has correct shape: (batch, length, features)
        if len(x.shape) == 2:
            x = x.unsqueeze(-1)  # Add feature dimension
        
        lstm_out, _ = self.lstm(x)
        # Take the last output
        last_output = lstm_out[:, -1, :]
        x = self.dropout(last_output)
        x = self.fc(x)
        
        return x

class BidirectionalLSTMNetwork(BaseNeuralNetwork):
    """Bidirectional LSTM neural network."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.lstm = nn.LSTM(input_size=1, hidden_size=config.lstm_units, 
                           batch_first=True, dropout=config.dropout_rate, bidirectional=True)
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc = nn.Linear(config.lstm_units * 2, 1)  # *2 for bidirectional
        self.to(self.device)
    
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(-1)
        
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        x = self.dropout(last_output)
        x = self.fc(x)
        
        return x

class GRUNetwork(BaseNeuralNetwork):
    """GRU neural network for time series."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.gru = nn.GRU(input_size=1, hidden_size=config.lstm_units, 
                         batch_first=True, dropout=config.dropout_rate)
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc = nn.Linear(config.lstm_units, 1)
        self.to(self.device)
    
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(-1)
        
        gru_out, _ = self.gru(x)
        last_output = gru_out[:, -1, :]
        x = self.dropout(last_output)
        x = self.fc(x)
        
        return x

class TransformerNetwork(BaseNeuralNetwork):
    """Transformer encoder network for time series."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.embedding = nn.Linear(1, config.lstm_units)
        self.pos_encoding = nn.Parameter(torch.zeros(1, config.input_length, config.lstm_units))
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.lstm_units,
            nhead=config.transformer_heads,
            dim_feedforward=config.lstm_units * 4,
            dropout=config.dropout_rate,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=config.transformer_layers)
        
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc = nn.Linear(config.lstm_units, 1)
        self.to(self.device)
    
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(-1)
        
        x = self.embedding(x)
        x = x + self.pos_encoding[:, :x.size(1), :]
        
        x = self.transformer(x)
        # Global average pooling
        x = x.mean(dim=1)
        x = self.dropout(x)
        x = self.fc(x)
        
        return x

class HybridCNNLSTMNetwork(BaseNeuralNetwork):
    """Hybrid CNN-LSTM network."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.conv1 = nn.Conv1d(1, config.conv_filters, config.conv_kernel_size, padding=1)
        self.pool1 = nn.MaxPool1d(2)
        self.conv2 = nn.Conv1d(config.conv_filters, config.conv_filters * 2, config.conv_kernel_size, padding=1)
        self.pool2 = nn.MaxPool1d(2)
        
        # Calculate LSTM input size
        lstm_input_size = self._get_lstm_input_size(config.input_length)
        
        self.lstm = nn.LSTM(input_size=lstm_input_size, hidden_size=config.lstm_units, 
                           batch_first=True, dropout=config.dropout_rate)
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc = nn.Linear(config.lstm_units, 1)
        self.to(self.device)
    
    def _get_lstm_input_size(self, input_length):
        """Calculate LSTM input size after convolutions."""
        x = torch.zeros(1, 1, input_length)
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        return x.size(1) * x.size(2)  # channels * length
    
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        # CNN layers
        x = self.pool1(F.relu(self.conv1(x)))
        x = self.pool2(F.relu(self.conv2(x)))
        
        # Reshape for LSTM: (batch, length, features)
        x = x.permute(0, 2, 1)
        x = x.contiguous().view(x.size(0), x.size(1), -1)
        
        # LSTM layers
        lstm_out, _ = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        x = self.dropout(last_output)
        x = self.fc(x)
        
        return x

class ResNetBlock(nn.Module):
    """Residual block for ResNet architecture."""
    
    def __init__(self, in_channels, out_channels, kernel_size=3):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size, padding=1)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.bn2 = nn.BatchNorm1d(out_channels)
        
        # Skip connection
        self.skip = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else nn.Identity()
    
    def forward(self, x):
        residual = self.skip(x)
        
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        
        out += residual
        out = F.relu(out)
        
        return out

class ResNetNetwork(BaseNeuralNetwork):
    """ResNet architecture for time series."""
    
    def __init__(self, config: NNConfig):
        super().__init__(config)
        
        self.conv1 = nn.Conv1d(1, 64, 7, padding=3)
        self.bn1 = nn.BatchNorm1d(64)
        self.pool1 = nn.MaxPool1d(2)
        
        # Residual blocks
        self.blocks = nn.ModuleList()
        in_channels = 64
        for i in range(config.resnet_blocks):
            out_channels = 64 * (2 ** i)
            self.blocks.append(ResNetBlock(in_channels, out_channels))
            in_channels = out_channels
        
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.dropout = nn.Dropout(config.dropout_rate)
        self.fc = nn.Linear(in_channels, 1)
        self.to(self.device)
    
    def forward(self, x):
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
        
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)
        
        for block in self.blocks:
            x = block(x)
        
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.fc(x)
        
        return x

class NeuralNetworkFactory:
    """Factory for creating neural network architectures."""
    
    _architectures = {
        NNArchitecture.FFN: FeedforwardNetwork,
        NNArchitecture.CNN: ConvolutionalNetwork,
        NNArchitecture.LSTM: LSTMNetwork,
        NNArchitecture.BILSTM: BidirectionalLSTMNetwork,
        NNArchitecture.GRU: GRUNetwork,
        NNArchitecture.TRANSFORMER: TransformerNetwork,
        NNArchitecture.HYBRID_CNN_LSTM: HybridCNNLSTMNetwork,
        NNArchitecture.RESNET: ResNetNetwork,
    }
    
    @classmethod
    def create_network(cls, config: NNConfig) -> BaseNeuralNetwork:
        """Create a neural network with the specified architecture."""
        if config.architecture not in cls._architectures:
            raise ValueError(f"Unknown architecture: {config.architecture}")
        
        network_class = cls._architectures[config.architecture]
        return network_class(config)
    
    @classmethod
    def get_available_architectures(cls) -> List[NNArchitecture]:
        """Get list of available architectures."""
        return list(cls._architectures.keys())
    
    @classmethod
    def create_benchmark_networks(cls, input_length: int, 
                                 architectures: Optional[List[NNArchitecture]] = None) -> Dict[str, BaseNeuralNetwork]:
        """Create a set of networks for benchmarking."""
        if architectures is None:
            architectures = list(NNArchitecture)
        
        networks = {}
        for arch in architectures:
            config = NNConfig(
                architecture=arch,
                input_length=input_length,
                hidden_dims=[64, 32],
                dropout_rate=0.2,
                learning_rate=0.001,
                epochs=50
            )
            # Pass model name to the network
            network = cls.create_network(config)
            network.model_name = arch.value
            networks[arch.value] = network
        
        return networks

# Convenience functions
def create_feedforward_network(input_length: int, hidden_dims: List[int] = [64, 32]) -> BaseNeuralNetwork:
    """Create a feedforward neural network."""
    config = NNConfig(
        architecture=NNArchitecture.FFN,
        input_length=input_length,
        hidden_dims=hidden_dims
    )
    return NeuralNetworkFactory.create_network(config)

def create_cnn_network(input_length: int, conv_filters: int = 64) -> BaseNeuralNetwork:
    """Create a convolutional neural network."""
    config = NNConfig(
        architecture=NNArchitecture.CNN,
        input_length=input_length,
        conv_filters=conv_filters
    )
    return NeuralNetworkFactory.create_network(config)

def create_lstm_network(input_length: int, lstm_units: int = 64) -> BaseNeuralNetwork:
    """Create an LSTM neural network."""
    config = NNConfig(
        architecture=NNArchitecture.LSTM,
        input_length=input_length,
        lstm_units=lstm_units
    )
    return NeuralNetworkFactory.create_network(config)

def create_all_benchmark_networks(input_length: int) -> Dict[str, BaseNeuralNetwork]:
    """Create all available neural network architectures for benchmarking."""
    return NeuralNetworkFactory.create_benchmark_networks(input_length)
