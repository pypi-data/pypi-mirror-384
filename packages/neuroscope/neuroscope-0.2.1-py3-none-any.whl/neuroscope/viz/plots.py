"""
NeuroScope Visualization Module
High-quality plotting tools for neural network training analysis.
"""

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import PillowWriter


class Visualizer:
    """
    High quality visualization tool for neural network training analysis.

    Provides comprehensive plotting capabilities for analyzing training dynamics,
    network behavior, and diagnostic information. Creates professional-grade
    figures suitable for research publications and presentations.

    Args:
        hist (dict): Complete training history from model.fit() containing:
            - history: Training/validation metrics per epoch
            - weights/biases: Final network parameters
            - activations/gradients: Sample network internals
            - *_stats_over_epochs: Statistical evolution during training

    Attributes:
        hist (dict): Complete training history data.
        history (dict): Training metrics (loss, accuracy) evolution.
        weights/biases: Final network parameters.
        activations/gradients: Representative network internals.

    Example:
        >>> from neuroscope.viz import Visualizer
        >>> history = model.fit(X_train, y_train, epochs=100)
        >>> viz = Visualizer(history)
        >>> viz.plot_learning_curves()
        >>> viz.plot_activation_distribution()
        >>> viz.plot_gradient_flow()
    """

    def __init__(self, hist):
        """
        Initialize visualizer with comprehensive training history.

        Sets up visualization infrastructure and applies publication-quality
        styling to all plots. Automatically extracts relevant data components
        for different types of analysis.

        Args:
            hist (dict): Training history from model.fit() containing all
                training statistics, network states, and diagnostic information.
        """
        self.hist = hist
        self.method = self.hist.get("method")
        if self.method == "fit_fast":
            self.history = hist["history"]
            self.weights = hist.get("weights", None)
            self.biases = hist.get("biases", None)
            self.metric = hist.get("metric", "accuracy")
            self.metric_display_name = hist.get("metric_display_name", "Accuracy")
        else:
            self.history = hist["history"]
            self.weights = hist.get("weights", None)
            self.biases = hist.get("biases", None)
            self.activations = hist.get("activations", {})
            self.gradients = hist.get("gradients", {})
            self.weight_stats_over_epochs = hist.get("weight_stats_over_epochs", {})
            self.activation_stats_over_epochs = hist.get(
                "activation_stats_over_epochs", {}
            )
            self.gradient_stats_over_epochs = hist.get("gradient_stats_over_epochs", {})
            self.epoch_distributions = hist.get("epoch_distributions", {})
            self.gradient_norms = hist.get("gradient_norms_over_epochs", {})
            self.weight_update_ratios = hist.get("weight_update_ratios_over_epochs", {})
            self.metric = hist.get("metric", "accuracy")
            self.metric_display_name = hist.get("metric_display_name", "Accuracy")

        self.epochs_ = hist.get("epochs", None)
        self._setup_style()
        self._setup_colors()

    def _setup_colors(self):
        """Define consistent color palette for all plots."""
        self.colors = {
            "train": "#1f77b4",
            "validation": "#ff7f0e",
            "layers": [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
                "#17becf",
            ],
            "reference": {
                "good": "#2ca02c",
                "warning": "#ff7f0e",
                "critical": "#d62728",
            },
        }

        # Line styles
        self.line_style = {"width": 1.2, "alpha": 0.8, "markersize": 3, "markevery": 2}

    def _setup_style(self):
        """Configure publication-quality matplotlib styling."""
        plt.style.use("default")
        plt.rcParams.update(
            {
                "font.family": "serif",
                "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                "font.size": 10,
                "axes.linewidth": 0.8,
                "axes.spines.left": True,
                "axes.spines.bottom": True,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "xtick.direction": "in",
                "ytick.direction": "in",
                "xtick.major.size": 3,
                "ytick.major.size": 3,
                "xtick.minor.size": 1.5,
                "ytick.minor.size": 1.5,
                "legend.frameon": False,
                "figure.facecolor": "white",
            }
        )

    def _configure_plot(self, title=None, xlabel=None, ylabel=None, figsize=(8, 6)):
        """Create and configure a single plot."""
        fig, ax = plt.subplots(figsize=figsize)
        if title:
            ax.set_title(title, fontsize=11, fontweight="normal")
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.tick_params(labelsize=9)
        return fig, ax

    def plot_learning_curves(
        self, figsize=(9, 4), ci=False, markers=True, save_path=None, metric="accuracy"
    ):
        """
        Plot training and validation learning curves for regular fit() results.

        Creates highest quality subplot showing loss and metric evolution
        during training. Automatically detects available data and applies
        consistent styling with optional confidence intervals.

        Note: For fit_fast() results, use plot_curves_fast() instead.

        Args:
            figsize (tuple[int, int], optional): Figure dimensions (width, height). Defaults to (9, 4).
            ci (bool, optional): Whether to add confidence intervals using moving window statistics.
                Only available for regular fit() results. Defaults to False.
            markers (bool, optional): Whether to show markers on line plots. Defaults to True.
            save_path (str, optional): Path to save the figure. Defaults to None.
            metric (str, optional): Name of the metric for y-axis label. Defaults to 'accuracy'.

        Example:
            >>> viz.plot_learning_curves(figsize=(10, 5), ci=True, save_path='curves.png')
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        if self.epochs_:
            epochs = self.epochs_
        else:
            epochs = np.arange(len(self.history["train_loss"])) + 1
        marker_settings = {
            "train": (
                {"marker": "o", "markersize": 3, "markevery": 2}
                if markers
                else {"marker": None}
            ),
            "val": (
                {"marker": "s", "markersize": 3, "markevery": 2}
                if markers
                else {"marker": None}
            ),
        }
        ax1.plot(
            epochs,
            self.history["train_loss"],
            label="Training",
            linewidth=1.2,
            color="#1f77b4",
            **marker_settings["train"],
        )
        ax1.plot(
            epochs,
            self.history["val_loss"],
            label="Validation",
            linewidth=1.2,
            color="#ff7f0e",
            **marker_settings["val"],
        )
        if ci and len(epochs) > 3:
            self._add_confidence_intervals(
                ax1, epochs, self.history["train_loss"], "#1f77b4"
            )
            self._add_confidence_intervals(
                ax1, epochs, self.history["val_loss"], "#ff7f0e"
            )

        ax1.set_title("Loss", fontsize=11, fontweight="normal")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Loss")
        ax1.legend(fontsize=9, loc="upper right")
        ax1.grid(True, alpha=0.3, linewidth=0.5)
        ax1.tick_params(labelsize=9)
        ax2.plot(
            epochs,
            self.history["train_acc"],
            label="Training",
            linewidth=1.2,
            color="#1f77b4",
            **marker_settings["train"],
        )
        ax2.plot(
            epochs,
            self.history["val_acc"],
            label="Validation",
            linewidth=1.2,
            color="#ff7f0e",
            **marker_settings["val"],
        )
        if ci and len(epochs) > 3:
            self._add_confidence_intervals(
                ax2, epochs, self.history["train_acc"], "#1f77b4"
            )
            self._add_confidence_intervals(
                ax2, epochs, self.history["val_acc"], "#ff7f0e"
            )

        ax2.set_title(self.metric_display_name, fontsize=11, fontweight="normal")
        ax2.set_xlabel("Epoch")
        if metric is not None:
            ax2.set_ylabel(str(metric).title())
        else:
            ax2.set_ylabel(self.metric_display_name)

        ax2.legend(fontsize=9, loc="lower right")
        ax2.grid(True, alpha=0.3, linewidth=0.5)
        ax2.tick_params(labelsize=9)
        plt.tight_layout(pad=2.0)
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def _add_confidence_intervals(self, ax, x, y, color, alpha=0.2):
        """Add confidence intervals to plots using moving average smoothing."""
        if len(y) < 3:
            return
        y = np.array(y)
        window = min(5, len(y) // 3)
        if window < 2:
            return
        padded_y = np.pad(y, window // 2, mode="edge")
        ci_upper = []
        ci_lower = []
        for i in range(len(y)):
            window_data = padded_y[i : i + window]
            mean_val = np.mean(window_data)
            std_val = np.std(window_data)
            ci_upper.append(mean_val + 1.96 * std_val / np.sqrt(len(window_data)))
            ci_lower.append(mean_val - 1.96 * std_val / np.sqrt(len(window_data)))
        x_clean = [i for i, val in enumerate(x) if not np.isnan(val)]
        ax.fill_between(x_clean, ci_lower, ci_upper, color=color, alpha=alpha)

    def plot_curves_fast(self, figsize=(10, 4), markers=True, save_path=None):
        """
        Plot learning curves for fit_fast() results.

        Args:
            figsize (tuple, optional): Figure size. Defaults to (10, 4).
            markers (bool, optional): Show actual data points. Defaults to True.
            save_path (str, optional): Save path. Defaults to None.
        """
        if self.method != "fit_fast":
            print("Use plot_learning_curves() for regular fit() results.")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        # Get clean data from fit_fast (no None values)
        epochs = self.history["epochs"]
        train_loss = self.history["train_loss"]
        train_acc = self.history["train_acc"]
        val_loss = self.history.get("val_loss", [])
        val_acc = self.history.get("val_acc", [])

        # Plot settings
        line_kw = {"linewidth": 1.2}
        marker_kw = {"marker": "o", "markersize": 3} if markers else {"marker": None}

        # Plot Loss
        ax1.plot(
            epochs,
            train_loss,
            label="Training",
            color="#1f77b4",
            **line_kw,
            **marker_kw,
        )
        if val_loss:
            ax1.plot(
                epochs,
                val_loss,
                label="Validation",
                color="#ff7f0e",
                **line_kw,
                **marker_kw,
            )
        ax1.set_title("Loss", fontsize=11, fontweight="normal")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Loss")
        ax1.legend(fontsize=9, loc="upper right")
        ax1.grid(True, alpha=0.3, linewidth=0.5)
        ax1.tick_params(labelsize=9)

        # Plot Accuracy
        ax2.plot(
            epochs, train_acc, label="Training", color="#1f77b4", **line_kw, **marker_kw
        )
        if val_acc:
            ax2.plot(
                epochs,
                val_acc,
                label="Validation",
                color="#ff7f0e",
                **line_kw,
                **marker_kw,
            )
        ax2.set_title(self.metric_display_name, fontsize=11, fontweight="normal")
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel(self.metric_display_name)
        ax2.legend(fontsize=9, loc="lower right")
        ax2.grid(True, alpha=0.3, linewidth=0.5)
        ax2.tick_params(labelsize=9)

        plt.tight_layout(pad=2.0)
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_activation_hist(
        self, epoch=None, figsize=(9, 4), kde=False, last_layer=False, save_path=None
    ):
        """
        Plot activation value distributions across network layers.

        Visualizes the distribution of activation values for each layer at a specific
        epoch, aggregated from all mini-batches. Useful for detecting activation
        saturation, dead neurons, and distribution shifts during training.

        Args:
            epoch (int, optional): Specific epoch to plot. If None, uses last epoch. Defaults to None.
            figsize (tuple[int, int], optional): Figure dimensions. Defaults to (9, 4).
            kde (bool, optional): Whether to use KDE-style smoothing for smoother curves. Defaults to False.
            last_layer (bool, optional): Whether to include output layer. Defaults to False.
            save_path (str, optional): Path to save the figure. Defaults to None.

        Example:
            >>> viz.plot_activation_hist(epoch=50, kde=True, save_path='activations.png')
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        return self._plot_epoch_distribution(
            "activations",
            "Activation Distributions (Epoch-Agg)",
            "Activation Value",
            epoch,
            figsize,
            kde,
            last_layer,
            save_path,
        )

    def plot_gradient_hist(
        self, epoch=None, figsize=(9, 4), kde=False, last_layer=False, save_path=None
    ):
        """
        Plot gradient value distributions across network layers.

        Visualizes gradient distributions to detect vanishing/exploding gradient
        problems, gradient flow issues, and training stability. Shows zero-line
        reference for assessing gradient symmetry and magnitude.

        Args:
            epoch (int, optional): Specific epoch to plot. If None, uses last epoch. Defaults to None.
            figsize (tuple[int, int], optional): Figure dimensions. Defaults to (9, 4).
            kde (bool, optional): Whether to use KDE-style smoothing. Defaults to False.
            last_layer (bool, optional): Whether to include output layer gradients. Defaults to False.
            save_path (str, optional): Path to save the figure. Defaults to None.

        Note:
            Gradient distributions should be roughly symmetric around zero for healthy training.
            Very narrow distributions may indicate vanishing gradients, while very wide
            distributions may indicate exploding gradients.

        Example:
            >>> viz.plot_gradient_hist(epoch=25, kde=True, save_path='gradients.png')
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        return self._plot_epoch_distribution(
            "gradients",
            "Gradient Distributions (Epoch-Agg)",
            "Gradient Value",
            epoch,
            figsize,
            kde,
            last_layer,
            save_path,
        )

    def plot_weight_hist(
        self, epoch=None, figsize=(9, 4), kde=False, last_layer=False, save_path=None
    ):
        """Uses aggregated samples from all mini-batches within
        an epoch to create representative distributions. Shows weight evolution patterns.

        Args:
            epoch: Specific epoch to plot (default: last epoch)
            figsize: Figure size tuple
            kde: Whether to use KDE-style smoothing
            last_layer: Whether to include output layer (default: False, hidden layers only)
            save_path: Path to save figure
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return

        return self._plot_epoch_distribution(
            "weights",
            "Weight Distributions (Epoch-Agg)",
            "Weight Value",
            epoch,
            figsize,
            kde,
            last_layer,
            save_path,
        )

    def _plot_epoch_distribution(
        self, data_type, title, xlabel, epoch, figsize, kde, last_layer, save_path
    ):
        """
        Internal method to plot epoch-aggregated distributions.

        Uses research-validated approach:
        1. Aggregates all mini-batch samples from an epoch
        2. Creates smooth KDE-like distributions
        3. Layer-specific coloring and styling
        4. Zero line reference for gradient analysis
        """
        fig, ax = self._configure_plot(title, xlabel, "Density", figsize)
        if not self.epoch_distributions or data_type not in self.epoch_distributions:
            ax.text(
                0.5,
                0.5,
                f"No epoch {data_type} data available\n"
                "Requires training with MLP.fit() method",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
            )
            plt.show()
            return
        data_dict = self.epoch_distributions[data_type]
        num_epochs = len(list(data_dict.values())[0]) if data_dict else 0
        if num_epochs == 0:
            ax.text(
                0.5,
                0.5,
                f"No {data_type} data collected during training",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
            )
            plt.show()
            return
        target_epoch = epoch if epoch is not None else num_epochs - 1
        if target_epoch >= num_epochs or target_epoch < 0:
            target_epoch = num_epochs - 1
        layers_to_plot = list(data_dict.keys())
        if not last_layer:
            layers_to_plot = layers_to_plot[:-1]
        layer_colors = self.colors["layers"][: len(layers_to_plot)]
        for i, (layer_key, color) in enumerate(zip(layers_to_plot, layer_colors)):
            if target_epoch < len(data_dict[layer_key]):
                epoch_samples = data_dict[layer_key][target_epoch]

                if len(epoch_samples) > 0:
                    bins = min(50, max(15, int(np.sqrt(len(epoch_samples)))))
                    if kde:
                        counts, bin_edges = np.histogram(
                            epoch_samples, bins=bins, density=True
                        )
                        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                        x_smooth = np.linspace(
                            bin_centers.min(), bin_centers.max(), len(bin_centers) * 3
                        )
                        y_smooth = np.interp(x_smooth, bin_centers, counts)
                        ax.plot(
                            x_smooth,
                            y_smooth,
                            color=color,
                            linewidth=2.0,
                            alpha=0.9,
                            label=f"Layer {i + 1} (n={len(epoch_samples)})",
                        )
                        ax.fill_between(x_smooth, y_smooth, alpha=0.3, color=color)
                    else:
                        # Standard histogram
                        ax.hist(
                            epoch_samples,
                            bins=bins,
                            density=True,
                            alpha=0.7,
                            color=color,
                            label=f"Layer {i + 1} (n={len(epoch_samples)})",
                            edgecolor="black",
                            linewidth=0.5,
                        )
        if data_type in ["gradients", "weights"]:
            ax.axvline(
                0,
                color="red",
                linestyle="--",
                alpha=0.8,
                linewidth=1.5,
                label="Zero line",
            )
        ax.legend(fontsize=9, bbox_to_anchor=(1.02, 1), loc="upper left")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_activation_stats(
        self,
        activation_stats=None,
        figsize=(12, 4),
        save_path=None,
        reference_lines=False,
    ):
        """
        Plot activation statistics over time with both mean and std.

        Args:
            activation_stats: Dict of layer activation stats OR None to use class data
                             Format: {'layer_0': {'mean': [...], 'std': [...]}, ...}
            figsize: Figure size tuple
            save_path: Path to save figure
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        fig, ax = self._configure_plot(
            "Activation Statistics Over Epochs", "Epoch", "Mean Activation", figsize
        )
        data_source = (
            activation_stats
            if activation_stats is not None
            else self.activation_stats_over_epochs
        )
        if not data_source:
            ax.text(
                0.5,
                0.5,
                "No activation stats data available\nPlease run model.fit() to generate statistics",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
            )
            plt.show()
            return
        first_layer = list(data_source.values())[0]
        has_mean_std = isinstance(first_layer, dict) and "mean" in first_layer
        if has_mean_std:
            epochs = np.arange(len(first_layer["mean"])) + 1
        else:
            epochs = np.arange(len(first_layer)) + 1

        layer_colors = self.colors["layers"][: len(data_source)]

        for i, (layer_name, color) in enumerate(zip(data_source.keys(), layer_colors)):
            if has_mean_std:
                mean_values = data_source[layer_name]["mean"]
                ax.plot(
                    epochs,
                    mean_values,
                    label=f"Layer {i + 1} Mean",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"],
                    marker="o",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                    linestyle="-",
                )
                std_values = data_source[layer_name]["std"]
                ax.plot(
                    epochs,
                    std_values,
                    label=f"Layer {i + 1} Std",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"] * 0.7,
                    marker="s",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                    linestyle="--",
                )
            else:
                y_values = data_source[layer_name]
                ax.plot(
                    epochs,
                    y_values,
                    label=f"Layer {i + 1}",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"],
                    marker="o",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                )

        # Add healthy range reference lines for activation magnitudes during training
        # Xavier (2010), He (2015), Batch Norm papers: 0.01-5.0 is healthy range
        # (Applies to both mean and std of activations during training)
        if reference_lines:
            ax.axhline(
                y=0.01,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Min (0.01)",
            )
            ax.axhline(
                y=5.0,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Max (5.0)",
            )
        ax.legend(fontsize=9, bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_gradient_stats(
        self, figsize=(12, 4), save_path=None, reference_lines=False
    ):
        """Plot gradient statistics over time with both mean and std."""
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        fig, ax = self._configure_plot(
            "Gradient Statistics Over Epochs", "Epoch", "Mean |Gradient|", figsize
        )
        if not self.gradient_stats_over_epochs:
            ax.text(
                0.5,
                0.5,
                "No gradient stats data available\nPlease run model.fit() to generate statistics",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
            )
            plt.show()
            return
        first_layer = list(self.gradient_stats_over_epochs.values())[0]
        has_mean_std = isinstance(first_layer, dict) and "mean" in first_layer
        if has_mean_std:
            epochs = np.arange(len(first_layer["mean"])) + 1
        else:
            epochs = np.arange(len(first_layer)) + 1

        layer_colors = self.colors["layers"][: len(self.gradient_stats_over_epochs)]

        for i, (layer_name, color) in enumerate(
            zip(self.gradient_stats_over_epochs.keys(), layer_colors)
        ):
            if has_mean_std:
                mean_values = self.gradient_stats_over_epochs[layer_name]["mean"]
                ax.plot(
                    epochs,
                    mean_values,
                    label=f"Layer {i + 1} Mean",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"],
                    marker="s",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                    linestyle="-",
                )
                std_values = self.gradient_stats_over_epochs[layer_name]["std"]
                ax.plot(
                    epochs,
                    std_values,
                    label=f"Layer {i + 1} Std",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"] * 0.7,
                    marker="D",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                    linestyle="--",
                )
            else:
                y_values = self.gradient_stats_over_epochs[layer_name]
                ax.plot(
                    epochs,
                    y_values,
                    label=f"Layer {i + 1}",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"],
                    marker="s",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                )

        # Add healthy range reference lines for gradient magnitudes during training
        # Bengio (1994), Pascanu (2013), Goodfellow (2016): 1e-4 to 1e-1 is healthy range
        # (Applies to both mean and std of gradients during training)
        if reference_lines:
            ax.axhline(
                y=1e-4,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Min (1e-4)",
            )
            ax.axhline(
                y=1e-1,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Max (1e-1)",
            )
        ax.set_yscale("log")
        ax.legend(fontsize=9, bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_weight_stats(self, figsize=(12, 4), save_path=None, reference_lines=False):
        """Plot weight statistics over time with both mean and std."""
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        fig, ax = self._configure_plot(
            "Weight Statistics Over Epochs", "Epoch", "Mean |Weight|", figsize
        )
        if not self.weight_stats_over_epochs:
            ax.text(
                0.5,
                0.5,
                "No weight stats data available\nPlease run model.fit() to generate statistics",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
            )
            plt.show()
            return
        first_layer = list(self.weight_stats_over_epochs.values())[0]
        has_mean_std = isinstance(first_layer, dict) and "mean" in first_layer
        if has_mean_std:
            epochs = np.arange(len(first_layer["mean"])) + 1
        else:
            epochs = np.arange(len(first_layer)) + 1
        layer_colors = self.colors["layers"][: len(self.weight_stats_over_epochs)]

        for i, (layer_name, color) in enumerate(
            zip(self.weight_stats_over_epochs.keys(), layer_colors)
        ):
            if has_mean_std:
                mean_values = self.weight_stats_over_epochs[layer_name]["mean"]
                ax.plot(
                    epochs,
                    mean_values,
                    label=f"Layer {i + 1} Mean",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"],
                    marker="^",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                    linestyle="-",
                )
                std_values = self.weight_stats_over_epochs[layer_name]["std"]
                ax.plot(
                    epochs,
                    std_values,
                    label=f"Layer {i + 1} Std",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"] * 0.7,
                    marker="v",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                    linestyle="--",
                )
            else:
                y_values = self.weight_stats_over_epochs[layer_name]
                ax.plot(
                    epochs,
                    y_values,
                    label=f"Layer {i + 1}",
                    color=color,
                    linewidth=self.line_style["width"],
                    alpha=self.line_style["alpha"],
                    marker="^",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                )

        # Add healthy range reference lines for TRAINED neural network weights
        # ResNet, VGG, modern CNN literature: 0.05-0.8 is healthy range for trained weights
        # (NOT initialization ranges - these are post-training weight magnitudes)
        if reference_lines:
            ax.axhline(
                y=0.05,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Min (0.05)",
            )
            ax.axhline(
                y=0.8,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Max (0.8)",
            )
        ax.legend(fontsize=9, bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_update_ratios(
        self, update_ratios=None, figsize=(12, 4), save_path=None, reference_lines=False
    ):
        """
        Plot weight update ratios per layer across epochs.

        Args:
            update_ratios: Dict of layer update ratios (optional - uses collected data if None)
                          Format: {'layer_0': [ratio_epoch_0, ratio_epoch_1, ...], ...}
            figsize: Figure size tuple
            save_path: Path to save figure
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        fig, ax = self._configure_plot(
            "Weight Update Ratios Over Epochs", "Epoch", "Update Ratio", figsize
        )
        data_source = (
            update_ratios if update_ratios is not None else self.weight_update_ratios
        )
        if not data_source:
            ax.text(
                0.5,
                0.5,
                "No weight update ratio data available\nPlease run model.fit() to generate statistics",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
            )
            plt.show()
            return
        epochs = np.arange(len(list(data_source.values())[0])) + 1
        layer_colors = self.colors["layers"][: len(data_source)]
        for i, (layer_name, color) in enumerate(zip(data_source.keys(), layer_colors)):
            y_values = data_source[layer_name]
            ax.plot(
                epochs,
                y_values,
                label=f"Layer {i + 1}",
                color=color,
                linewidth=self.line_style["width"],
                marker="o",
                markersize=self.line_style["markersize"],
                markevery=self.line_style["markevery"],
            )
        if reference_lines:
            ax.axhline(
                y=1e-4,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Min (1e-4)",
            )
            ax.axhline(
                y=1e-2,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Healthy Max (1e-2)",
            )
        ax.set_yscale("log")
        ax.legend(fontsize=9, bbox_to_anchor=(1.02, 1), loc="upper left")
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_gradient_norms(
        self,
        gradient_norms=None,
        figsize=(12, 4),
        save_path=None,
        reference_lines=False,
    ):
        """Plot gradient norms per layer over epochs."""
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        fig, ax = self._configure_plot(
            "Gradient Norms Over Epochs", "Epoch", "Gradient Norm", figsize
        )
        data_source = (
            gradient_norms if gradient_norms is not None else self.gradient_norms
        )
        if not data_source:
            print("No gradient norm data available")
            return
        layer_colors = self.colors["layers"][: len(data_source)]
        epochs = np.arange(len(list(data_source.values())[0])) + 1
        for i, (layer_name, color) in enumerate(zip(data_source.keys(), layer_colors)):
            norms = data_source[layer_name]
            if norms:
                ax.plot(
                    epochs,
                    norms,
                    label=f"Layer {i + 1}",
                    color=color,
                    linewidth=self.line_style["width"],
                    marker="s",
                    markersize=self.line_style["markersize"],
                    markevery=self.line_style["markevery"],
                )

        # Add reference lines based on authentic gradient clipping literature
        # Pascanu et al. (2013), Sutskever et al. (2014): 1.0 is standard clipping threshold
        # Bengio et al. (1994): Below 0.01 indicates vanishing gradients
        if reference_lines:
            ax.axhline(
                y=1.0,
                color=self.colors["reference"]["good"],
                linestyle="--",
                alpha=0.7,
                label="Clipping Threshold (1.0)",
            )
            ax.axhline(
                y=0.01,
                color=self.colors["reference"]["warning"],
                linestyle="--",
                alpha=0.7,
                label="Vanishing Gradient Warning (0.01)",
            )
        ax.set_yscale("log")
        ax.legend(fontsize=9, bbox_to_anchor=(1.02, 1), loc="upper left")
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight", facecolor="white")
        plt.show()

    def plot_training_animation(self, bg="dark", save_path=None):
        """
        Creates a comprehensive 4-panel GIF animation showing:
        1. Loss curves over time
        2. Accuracy curves over time
        3. Current metrics bar chart
        4. Gradient flow analysis
        Speed automatically adjusts based on epoch count for smooth motion feel.
        Args:
            bg: Theme ('dark' or 'light')
            save_path: Path to save GIF (defaults to 'mlp_training_animation.gif')
        Returns:
            Path to saved GIF file
        """
        if self.method == "fit_fast":
            print("The function is only accessible to .fit() method.")
            return
        epochs = len(self.history.get("train_loss", []))
        if epochs == 0:
            print("No training data found - cannot create animation")
            return None
        fps = 3 if epochs < 50 else 5 if epochs <= 100 else 8
        colors = {
            "primary": "#2E86AB",
            "secondary": "#F18F01",
            "accent": "#28D631",
            "success": "#FF2727",
            "secondary_accent": "#FFC062",
            "primary_accent": "#63CBF8",
            "background": "#0A0E27" if bg == "dark" else "#FFFFFF",
            "text": "#FFFFFF" if bg == "dark" else "#000000",
            "grid": "#333333" if bg == "dark" else "#CCCCCC",
            "spine": "#555555" if bg == "dark" else "#999999",
        }
        fig = plt.figure(figsize=(18, 10))
        fig.patch.set_facecolor(colors["background"])

        axes = [
            plt.subplot(2, 3, 1),  # Loss curves
            plt.subplot(2, 3, 2),  # Accuracy curves
            plt.subplot(2, 3, 3),  # Metrics bar chart
            plt.subplot(2, 1, 2),  # Gradient flow
        ]
        plt.subplots_adjust(hspace=0.3, wspace=0.3)

        def style_axis(ax):
            """Apply consistent styling to axis"""
            ax.set_facecolor(colors["background"])
            ax.tick_params(colors=colors["text"])
            for spine in ax.spines.values():
                spine.set_color(colors["spine"])

        def style_legend(legend):
            """Apply consistent styling to legend"""
            legend.get_frame().set_facecolor(colors["background"])
            legend.get_frame().set_edgecolor(colors["spine"])
            for text in legend.get_texts():
                text.set_color(colors["text"])

        for ax in axes:
            style_axis(ax)
        train_loss, val_loss = self.history.get("train_loss", []), self.history.get(
            "val_loss", []
        )
        train_acc, val_acc = self.history.get("train_acc", []), self.history.get(
            "val_acc", []
        )

        def animate(frame):
            for ax in axes:
                ax.clear()
                style_axis(ax)

            current_epoch = frame + 1
            epochs_range = list(range(1, current_epoch + 1))
            # 1. Loss Evolution
            axes[0].set_title(
                "Loss Evolution", color=colors["text"], fontweight="bold", fontsize=15
            )
            if len(train_loss) >= current_epoch:
                train_losses_current = train_loss[:current_epoch]
                axes[0].plot(
                    epochs_range,
                    train_losses_current,
                    color=colors["primary"],
                    linewidth=2.5,
                    label="Train Loss",
                    alpha=0.9,
                )
            else:
                train_losses_current = []
            if len(val_loss) >= current_epoch:
                val_losses_current = val_loss[:current_epoch]
                axes[0].plot(
                    epochs_range,
                    val_losses_current,
                    color=colors["secondary"],
                    linewidth=2.5,
                    label="Val Loss",
                    alpha=0.9,
                )
            else:
                val_losses_current = []
            # Generalization gap visualization
            if train_losses_current and val_losses_current:
                min_length = min(len(train_losses_current), len(val_losses_current))
                epochs_common = epochs_range[:min_length]
                train_common = train_losses_current[:min_length]
                val_common = val_losses_current[:min_length]

                axes[0].fill_between(
                    epochs_common,
                    train_common,
                    val_common,
                    where=np.array(val_common) > np.array(train_common),
                    color=colors["secondary_accent"],
                    alpha=0.4,
                    interpolate=True,
                )

                axes[0].fill_between(
                    epochs_common,
                    train_common,
                    val_common,
                    where=np.array(val_common) <= np.array(train_common),
                    color=colors["primary_accent"],
                    alpha=0.3,
                    interpolate=True,
                )

            axes[0].set_xlabel("Epoch", color=colors["text"])
            axes[0].set_ylabel("Loss", color=colors["text"])
            axes[0].grid(True, alpha=0.3, color=colors["grid"])
            style_legend(axes[0].legend(loc="upper right"))
            # 2. Metric Evolution
            axes[1].set_title(
                f"{self.metric_display_name} Evolution",
                color=colors["text"],
                fontweight="bold",
                fontsize=16,
            )
            if len(train_acc) >= current_epoch:
                axes[1].plot(
                    epochs_range,
                    train_acc[:current_epoch],
                    color=colors["primary"],
                    linewidth=2,
                    label=f"Train {self.metric_display_name}",
                )
            if len(val_acc) >= current_epoch:
                axes[1].plot(
                    epochs_range,
                    val_acc[:current_epoch],
                    color=colors["secondary"],
                    linewidth=2,
                    label=f"Val {self.metric_display_name}",
                )
            axes[1].set_xlabel("Epoch", color=colors["text"])
            axes[1].set_ylabel(self.metric_display_name, color=colors["text"])
            axes[1].grid(True, alpha=0.3, color=colors["grid"])
            style_legend(axes[1].legend())
            # 3. Current Metrics Bar Chart
            axes[2].set_title(
                "Current Metrics", color=colors["text"], fontweight="bold", fontsize=16
            )
            metrics = [
                "Train Loss",
                "Val Loss",
                f"Train {self.metric_display_name}",
                f"Val {self.metric_display_name}",
            ]
            data_sources = [train_loss, val_loss, train_acc, val_acc]
            values = [
                data[current_epoch - 1] if len(data) >= current_epoch else 0
                for data in data_sources
            ]
            bar_colors = [colors["primary"], colors["secondary"]] * 2
            max_val = max(values) if any(values) else 1

            for i, (value, color) in enumerate(zip(values, bar_colors)):
                if value > 0:
                    axes[2].bar(
                        i, value, width=0.6, color=color, alpha=0.7, edgecolor="none"
                    )
                    axes[2].text(
                        i,
                        value + max_val * 0.02,
                        f"{value:.3f}",
                        ha="center",
                        va="bottom",
                        color=colors["text"],
                        fontweight="bold",
                        fontsize=8,
                    )

            axes[2].set_xlim(-0.5, len(metrics) - 0.5)
            axes[2].set_ylim(0, max_val * 1.15)
            axes[2].set_xticks(range(len(metrics)))
            axes[2].set_xticklabels(metrics, color=colors["text"])
            axes[2].set_ylabel("Value", color=colors["text"])
            # 4. Gradient Flow Analysis
            axes[3].set_title(
                "Gradient Flow Across Layers",
                color=colors["text"],
                fontweight="bold",
                fontsize=16,
            )
            if (
                hasattr(self, "gradient_stats_over_epochs")
                and self.gradient_stats_over_epochs
                and current_epoch > 0
            ):
                layer_colors = [
                    colors["primary"],
                    colors["secondary"],
                    colors["accent"],
                ]

                for i, (layer_key, layer_stats) in enumerate(
                    self.gradient_stats_over_epochs.items()
                ):
                    if isinstance(layer_stats, dict) and "mean" in layer_stats:
                        if current_epoch <= len(layer_stats["mean"]):
                            gradient_means = layer_stats["mean"][:current_epoch]
                            color = layer_colors[i % len(layer_colors)]

                            axes[3].plot(
                                epochs_range,
                                gradient_means,
                                color=color,
                                linewidth=2,
                                alpha=0.8,
                                label=f"Layer {i}",
                                marker="o",
                                markersize=3,
                            )

                axes[3].set_xlabel("Epoch", color=colors["text"])
                axes[3].set_ylabel("Mean Gradient Magnitude", color=colors["text"])
                axes[3].set_yscale("log")
                axes[3].set_ylim(1e-4, 1e0)
                axes[3].grid(True, alpha=0.2, color=colors["grid"])
                style_legend(axes[3].legend(loc="upper right"))
                # Reference lines for healthy gradient ranges
                axes[3].axhline(
                    y=1e-7,
                    color=colors["success"],
                    linestyle=":",
                    alpha=0.5,
                    linewidth=1,
                )
                axes[3].axhline(
                    y=1e-2,
                    color=colors["success"],
                    linestyle=":",
                    alpha=0.5,
                    linewidth=1,
                )
            else:
                axes[3].text(
                    0.5,
                    0.5,
                    "Gradient Flow Analysis\n(Gradient stats not available)",
                    ha="center",
                    va="center",
                    transform=axes[3].transAxes,
                    color=colors["text"],
                    fontsize=12,
                    alpha=0.7,
                )
            fig.suptitle(
                f"MLP Training Animation - Epoch {current_epoch}/{epochs}",
                fontsize=22,
                fontweight="bold",
                color=colors["text"],
            )

        # Create and save animation
        anim = animation.FuncAnimation(
            fig, animate, frames=epochs, interval=1000 // fps, repeat=True
        )
        output_path = save_path if save_path else "mlp_training_animation.gif"
        print("Building Animation - this may take a while...")
        try:
            anim.save(output_path, writer=PillowWriter(fps=fps))
            print(f"Saved animation to: {output_path}")
        except Exception as e:
            print(f"Error saving animation: {e}")
        plt.close(fig)
