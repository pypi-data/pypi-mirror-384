"""
ManniGrad: A tiny autograd engine and neural network library.
"""

# Import core components to the top-level namespace
from .engine import Value
from .nn import Neuron, Layer, MLP, SGD, Adam
from .utils import mse_loss

# Define the public API of the package
__all__ = [
    # from engine
    'Value',
    # from nn
    'Neuron',
    'Layer',
    'MLP',
    'SGD',
    'Adam',
    # from utils
    'mse_loss',
]

__version__ = "0.1.2"  
