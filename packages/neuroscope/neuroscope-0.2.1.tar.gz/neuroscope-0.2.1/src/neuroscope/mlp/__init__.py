"""
NeuroScope MLP Module

Core neural network implementation with modern features:
- Multi-layer perceptron with flexible architecture
- Advanced activation functions and weight initialization
- Comprehensive loss functions and evaluation metrics
- Efficient forward/backward propagation with numerical stability

Convenient function access:
    >>> from neuroscope.mlp import MLP, mse, bce, accuracy_binary, relu, he_init
    >>> # Use functions directly without class prefixes
    >>> loss = mse(y_true, y_pred)
    >>> acc = accuracy_binary(y_true, y_pred)
    >>> activated = relu(z)
    >>> weights, biases = he_init([784, 128, 10])
"""

from .activations import ActivationFunctions
from .initializers import WeightInits
from .losses import LossFunctions
from .metrics import Metrics

# Main classes
from .mlp import MLP
from .optimizers import SGD, Adam, RMSprop, SGDMomentum
from .utils import Utils

# Direct function access - Loss Functions
mse = LossFunctions.mse
bce = LossFunctions.bce
cce = LossFunctions.cce
mse_with_reg = LossFunctions.mse_with_reg
bce_with_reg = LossFunctions.bce_with_reg
cce_with_reg = LossFunctions.cce_with_reg

# Direct function access - Metrics
accuracy_binary = Metrics.accuracy_binary
accuracy_multiclass = Metrics.accuracy_multiclass
rmse = Metrics.rmse
mae = Metrics.mae
r2_score = Metrics.r2_score
f1_score = Metrics.f1_score
precision = Metrics.precision
recall = Metrics.recall

# Direct function access - Activation Functions
relu = ActivationFunctions.relu
leaky_relu = ActivationFunctions.leaky_relu
sigmoid = ActivationFunctions.sigmoid
tanh = ActivationFunctions.tanh
selu = ActivationFunctions.selu
softmax = ActivationFunctions.softmax
relu_derivative = ActivationFunctions.relu_derivative
leaky_relu_derivative = ActivationFunctions.leaky_relu_derivative
sigmoid_derivative = ActivationFunctions.sigmoid_derivative
tanh_derivative = ActivationFunctions.tanh_derivative
selu_derivative = ActivationFunctions.selu_derivative

# Direct function access - Weight Initializers
he_init = WeightInits.he_init
xavier_init = WeightInits.xavier_init
random_init = WeightInits.random_init
selu_init = WeightInits.selu_init
smart_init = WeightInits.smart_init

# Direct function access - Utilities
get_batches = Utils.get_batches
gradient_clipping = Utils.gradient_clipping
validate_array_input = Utils.validate_array_input

__all__ = [
    # Main classes
    "MLP",
    "LossFunctions",
    "Metrics",
    "ActivationFunctions",
    "WeightInits",
    "Utils",
    # Optimizers
    "SGD",
    "SGDMomentum",
    "Adam",
    "RMSprop",
    # Loss functions
    "mse",
    "bce",
    "cce",
    "mse_with_reg",
    "bce_with_reg",
    "cce_with_reg",
    # Metrics
    "accuracy_binary",
    "accuracy_multiclass",
    "rmse",
    "mae",
    "r2_score",
    "f1_score",
    "precision",
    "recall",
    # Activations
    "relu",
    "leaky_relu",
    "sigmoid",
    "tanh",
    "selu",
    "softmax",
    "relu_derivative",
    "leaky_relu_derivative",
    "sigmoid_derivative",
    "tanh_derivative",
    "selu_derivative",
    # Initializers
    "he_init",
    "xavier_init",
    "random_init",
    "selu_init",
    "smart_init",
    # Utilities
    "get_batches",
    "gradient_clipping",
    "validate_array_input",
]
