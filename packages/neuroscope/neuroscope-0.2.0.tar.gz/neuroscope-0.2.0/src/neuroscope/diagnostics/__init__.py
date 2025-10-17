"""
NeuroScope Diagnostics Module

Research-validated diagnostic tools for neural network training:
- Pre-training analysis for architecture and initialization validation
- Real-time training monitoring with comprehensive health indicators
- Post-training evaluation and performance analysis
Convenient function access:
    >>> from neuroscope.diagnostics import (
    ...     PreTrainingAnalyzer, TrainingMonitor, PostTrainingEvaluator,
    ...     monitor_dead_neurons, monitor_vanishing_gradients, monitor_exploding_gradients,
    ...     analyze_initial_loss, analyze_weight_init, analyze_architecture_sanity
    ... )
Based on established deep learning research and best practices.
"""

from .posttraining import PostTrainingEvaluator

# Main classes
from .pretraining import PreTrainingAnalyzer
from .training_monitors import TrainingMonitor

# Create instances for direct function access
_temp_analyzer = None
_temp_monitor = None
_temp_evaluator = None


# Pre-training analysis functions (require model parameter)
def analyze_initial_loss(model, X, y):
    """Analyze initial loss against theoretical expectations."""
    analyzer = PreTrainingAnalyzer(model)
    return analyzer.analyze_initial_loss(X, y)


def analyze_weight_init(model):
    """Validate weight initialization quality."""
    analyzer = PreTrainingAnalyzer(model)
    return analyzer.analyze_weight_init()


def analyze_architecture_sanity(model):
    """Perform comprehensive architecture validation."""
    analyzer = PreTrainingAnalyzer(model)
    return analyzer.analyze_architecture_sanity()


# Training monitoring functions (standalone)
def monitor_dead_neurons(activations, activation_functions=None):
    """Monitor dead ReLU neurons during training."""
    monitor = TrainingMonitor()
    return monitor.monitor_relu_dead_neurons(activations, activation_functions)


def monitor_vanishing_gradients(gradients):
    """Detect vanishing gradient problem."""
    monitor = TrainingMonitor()
    return monitor.monitor_vanishing_gradients(gradients)


def monitor_exploding_gradients(gradients):
    """Detect exploding gradient problem."""
    monitor = TrainingMonitor()
    return monitor.monitor_exploding_gradients(gradients)


# Post-training evaluation functions (require model parameter)
def evaluate_robustness(model, X, y, noise_levels=None):
    """Evaluate model robustness against noise."""
    evaluator = PostTrainingEvaluator(model)
    return evaluator.evaluate_robustness(X, y, noise_levels)


def evaluate_performance(model, X, y):
    """Evaluate comprehensive model performance."""
    evaluator = PostTrainingEvaluator(model)
    return evaluator.evaluate_performance(X, y)


__all__ = [
    # Main classes
    "PreTrainingAnalyzer",
    "TrainingMonitor",
    "PostTrainingEvaluator",
    # Pre-training functions
    "analyze_initial_loss",
    "analyze_weight_init",
    "analyze_architecture_sanity",
    # Training monitoring functions
    "monitor_dead_neurons",
    "monitor_vanishing_gradients",
    "monitor_exploding_gradients",
    # Post-training functions
    "evaluate_robustness",
    "evaluate_performance",
]
