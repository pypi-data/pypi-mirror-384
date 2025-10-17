"""
NeuroScope Visualization Module

Publication-quality plotting tools for neural network analysis:
- Training dynamics visualization (loss curves, metrics evolution)
- Network internals analysis (activations, gradients, weights)
- Diagnostic plots for training health assessment
- Professional styling suitable for research publications

Convenient function access:
    >>> from neuroscope.viz import (
    ...     Visualizer, plot_learning_curves, plot_activation_hist,
    ...     plot_gradient_hist, plot_weight_hist, plot_activation_stats
    ... )
    >>> # Use functions directly with training history
    >>> plot_learning_curves(history)
    >>> plot_activation_hist(history, epoch=50)
"""

# Main class
from .plots import Visualizer


# Direct function access
def plot_learning_curves(
    history, figsize=(9, 4), ci=False, markers=True, save_path=None, metric="accuracy"
):
    """Plot training and validation learning curves."""
    viz = Visualizer(history)
    return viz.plot_learning_curves(figsize, ci, markers, save_path, metric)


def plot_activation_hist(
    history, epoch=None, figsize=(9, 4), kde=False, last_layer=False, save_path=None
):
    """Plot activation value distributions across network layers."""
    viz = Visualizer(history)
    return viz.plot_activation_hist(epoch, figsize, kde, last_layer, save_path)


def plot_gradient_hist(
    history, epoch=None, figsize=(9, 4), kde=False, last_layer=False, save_path=None
):
    """Plot gradient value distributions across network layers."""
    viz = Visualizer(history)
    return viz.plot_gradient_hist(epoch, figsize, kde, last_layer, save_path)


def plot_weight_hist(
    history, epoch=None, figsize=(9, 4), kde=False, last_layer=False, save_path=None
):
    """Plot weight value distributions across network layers."""
    viz = Visualizer(history)
    return viz.plot_weight_hist(epoch, figsize, kde, last_layer, save_path)


def plot_activation_stats(
    history,
    activation_stats=None,
    figsize=(12, 4),
    save_path=None,
    reference_lines=False,
):
    """Plot activation statistics evolution over training epochs."""
    viz = Visualizer(history)
    return viz.plot_activation_stats(
        activation_stats, figsize, save_path, reference_lines
    )


def plot_gradient_stats(
    history, figsize=(12, 4), save_path=None, reference_lines=False
):
    """Plot gradient statistics evolution over training epochs."""
    viz = Visualizer(history)
    return viz.plot_gradient_stats(figsize, save_path, reference_lines)


def plot_weight_stats(history, figsize=(12, 4), save_path=None, reference_lines=False):
    """Plot weight statistics evolution over training epochs."""
    viz = Visualizer(history)
    return viz.plot_weight_stats(figsize, save_path, reference_lines)


def plot_update_ratios(
    history, update_ratios=None, figsize=(12, 4), save_path=None, reference_lines=False
):
    """Plot weight update ratios over training epochs."""
    viz = Visualizer(history)
    return viz.plot_update_ratios(update_ratios, figsize, save_path, reference_lines)


def plot_gradient_norms(
    history, gradient_norms=None, figsize=(12, 4), save_path=None, reference_lines=False
):
    """Plot gradient norms evolution over training epochs."""
    viz = Visualizer(history)
    return viz.plot_gradient_norms(gradient_norms, figsize, save_path, reference_lines)


def plot_training_animation(history, bg="dark", save_path=None):
    """Create animated visualization of training progress."""
    viz = Visualizer(history)
    return viz.plot_training_animation(bg, save_path)


__all__ = [
    # Main class
    "Visualizer",
    # Direct plotting functions
    "plot_learning_curves",
    "plot_activation_hist",
    "plot_gradient_hist",
    "plot_weight_hist",
    "plot_activation_stats",
    "plot_gradient_stats",
    "plot_weight_stats",
    "plot_update_ratios",
    "plot_gradient_norms",
    "plot_training_animation",
]
