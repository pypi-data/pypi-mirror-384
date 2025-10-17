"""
NeuroScope: A comprehensive neural network framework for learning and prototyping.

NeuroScope provides a clean, education-oriented interface for building and analyzing
multi-layer perceptrons with advanced diagnostic capabilities. Designed for rapid
experimentation with comprehensive monitoring and visualization tools.

Core Components:
    - MLP: Modern multi-layer perceptron implementation
    - Diagnostics: Pre-training, training, and post-training analysis tools
    - Visualization: Publication-quality plotting and analysis

Example:
    >>> from neuroscope.mlp import MLP, mse, accuracy_binary, relu
    >>> from neuroscope.diagnostics import PreTrainingAnalyzer, TrainingMonitor
    >>> from neuroscope.viz import Visualizer
    >>>
    >>> # Create and train model
    >>> model = MLP([784, 128, 10], activation="relu", out_activation="softmax")
    >>> model.compile(optimizer="adam", lr=1e-3)
    >>>
    >>> # Analyze before training
    >>> analyzer = PreTrainingAnalyzer(model)
    >>> analyzer.analyze(X_train, y_train)
    >>>
    >>> # Ultra-fast training for production
    >>> history = model.fit_fast(X_train, y_train, X_val, y_val, epochs=100, batch_size=256)
    >>>
    >>> # Or train with full diagnostics for research
    >>> monitor = TrainingMonitor()
    >>> history = model.fit(X_train, y_train, monitor=monitor, epochs=100)
    >>>
    >>> # Use functions directly
    >>> loss = mse(y_true, y_pred)
    >>> acc = accuracy_binary(y_true, y_pred)
    >>>
    >>> # Visualize results
    >>> viz = Visualizer(history)
    >>> viz.plot_learning_curves()
"""

from neuroscope.__version__ import __version__
from neuroscope.diagnostics.posttraining import PostTrainingEvaluator
from neuroscope.diagnostics.pretraining import PreTrainingAnalyzer
from neuroscope.diagnostics.training_monitors import TrainingMonitor
from neuroscope.mlp.activations import ActivationFunctions
from neuroscope.mlp.initializers import WeightInits

# Direct function access for convenience
from neuroscope.mlp.losses import LossFunctions
from neuroscope.mlp.metrics import Metrics

# Main classes
from neuroscope.mlp.mlp import MLP
from neuroscope.viz.plots import Visualizer

# Export loss functions directly
mse = LossFunctions.mse
bce = LossFunctions.bce
cce = LossFunctions.cce
mse_with_reg = LossFunctions.mse_with_reg
bce_with_reg = LossFunctions.bce_with_reg
cce_with_reg = LossFunctions.cce_with_reg

# Export metrics directly
accuracy_binary = Metrics.accuracy_binary
accuracy_multiclass = Metrics.accuracy_multiclass
rmse = Metrics.rmse
mae = Metrics.mae
r2_score = Metrics.r2_score
f1_score = Metrics.f1_score
precision = Metrics.precision
recall = Metrics.recall

# Export activation functions directly
relu = ActivationFunctions.relu
leaky_relu = ActivationFunctions.leaky_relu
sigmoid = ActivationFunctions.sigmoid
tanh = ActivationFunctions.tanh
selu = ActivationFunctions.selu
softmax = ActivationFunctions.softmax

# Export initializers directly
he_init = WeightInits.he_init
xavier_init = WeightInits.xavier_init
random_init = WeightInits.random_init
selu_init = WeightInits.selu_init

# Aliases for convenient imports
PTA = PreTrainingAnalyzer  # Pre-Training Analyzer
TM = TrainingMonitor  # Training Monitor
PTE = PostTrainingEvaluator  # Post-Training Evaluator
VIZ = Visualizer  # Visualizer


__all__ = [
    # Main classes
    "MLP",
    "PreTrainingAnalyzer",
    "TrainingMonitor",
    "PostTrainingEvaluator",
    "Visualizer",
    # Convenient aliases
    "PTA",
    "TM",
    "PTE",
    "VIZ",
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
    # Initializers
    "he_init",
    "xavier_init",
    "random_init",
    "selu_init",
    # Version
    "__version__",
]
