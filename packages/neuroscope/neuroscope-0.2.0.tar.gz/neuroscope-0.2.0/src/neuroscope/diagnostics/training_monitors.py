"""
Training Monitors for NeuroScope MLP Framework
Real-time monitoring tools for neural network training based on modern deep learning research.
Implements comprehensive training diagnostics with emoji-based status indicators.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from wcwidth import wcswidth
except ImportError:

    def wcswidth(s):
        return len(s) if s else 0


class TrainingMonitor:
    """
    Comprehensive real-time training monitoring system for neural networks.

    Monitors 10 key training health indicators:
    - Dead ReLU neurons detection
    - Vanishing Gradient Problem (VGP) detection
    - Exploding Gradient Problem (EGP) detection
    - Weight health analysis
    - Learning progress
    - Overfitting detection
    - Gradient signal-to-noise ratio
    - Activation saturation detection (tanh/sigmoid)
    - Training plateau detection
    - Weight update vs magnitude ratios
    """

    def __init__(self, model=None, history_size=50):
        """
        Initialize comprehensive training monitor.

        Sets up monitoring infrastructure for tracking 10 key training health
        indicators during neural network training. Uses research-validated
        thresholds and emoji-based status visualization.

        Args:
            model: Optional MLP model instance (can be set later).
            history_size (int, optional): Number of epochs to keep in rolling
                history for trend analysis. Defaults to 50.

        Example:
            >>> monitor = TrainingMonitor(history_size=100)
            >>> results = model.fit(X, y, monitor=monitor)
        """
        self.model = model
        self.history_size = history_size
        self.reset_history()
        self.epoch_count = 0
        self.baseline_activations = {}
        self.baseline_set = False

    def reset_history(self):
        """Reset all monitoring history."""
        self.history = {
            "loss": deque(maxlen=self.history_size),
            "val_loss": deque(maxlen=self.history_size),
            "dead_neurons": deque(maxlen=self.history_size),
            "vgp": deque(maxlen=self.history_size),
            "egp": deque(maxlen=self.history_size),
            "weight_health": deque(maxlen=self.history_size),
            "gradient_snr": deque(maxlen=self.history_size),
            "saturation": deque(maxlen=self.history_size),
            "weight_update_ratio": deque(maxlen=self.history_size),
            "learning_progress": deque(maxlen=self.history_size),
        }
        self.baseline_set = False

    def monitor_relu_dead_neurons(
        self,
        activations: List[np.ndarray],
        activation_functions: Optional[List[str]] = None,
    ) -> Tuple[float, str]:
        """
        Monitor for dead ReLU neurons during training.

        Detects neurons that have become inactive (always output zero) which
        indicates the "dying ReLU" problem. Uses activation-function-aware
        thresholds based on research by Glorot et al. (2011) and He et al. (2015).

        Natural sparsity in ReLU networks is expected (~50%), but excessive
        sparsity (>90%) indicates dead neurons that cannot learn.

        Args:
            activations (list[NDArray[np.float64]]): Layer activation outputs.
            activation_functions (list[str], optional): Activation function names per layer.

        Returns:
            tuple[float, str]: (dead_percentage, status_emoji) where status is:
                - 🟢: Healthy sparsity (<10% dead)
                - 🟡: Moderate concern (10-30% dead)
                - 🔴: Critical issue (>30% dead)

        Note:
            Based on "Deep Sparse Rectifier Neural Networks" (Glorot et al. 2011)
            and "Delving Deep into Rectifiers" (He et al. 2015).
        """
        if not activations or len(activations) == 0:
            return 0.0, "🟡"
        activation_thresholds = {
            # Standard ReLU: Glorot et al. found ~50% natural sparsity in random init
            # Dead threshold: >90% (well above natural sparsity)
            "relu": {
                "dead_threshold": 0.90,
                "warning_threshold": 0.75,
                "zero_tolerance": 1e-8,
            },
            # Leaky ReLU: Allows small negative values, lower natural sparsity
            # Dead threshold: >85% (Maas et al. 2013 recommendations)
            "leaky_relu": {
                "dead_threshold": 0.85,
                "warning_threshold": 0.70,
                "zero_tolerance": 1e-6,
            },
            "default": {
                "dead_threshold": 0.85,
                "warning_threshold": 0.70,
                "zero_tolerance": 1e-7,
            },
        }

        def get_activation_type(act_name):
            if not act_name:
                return "default"
            act_lower = str(act_name).lower()
            if act_lower in activation_thresholds:
                return act_lower
            if "relu" in act_lower:
                if "leaky" in act_lower or "lrelu" in act_lower:
                    return "leaky_relu"
                else:
                    return "relu"
            else:
                return "default"

        total_neurons = 0
        dead_neurons = 0
        # Analyze all hidden layers
        for i, activation in enumerate(activations[:-1]):
            if activation.size == 0:
                continue
            if activation_functions and i < len(activation_functions):
                act_type = get_activation_type(activation_functions[i])
            else:
                act_type = "default"
            thresholds = activation_thresholds[act_type]
            if activation.ndim > 1:
                layer_neurons = activation.shape[1]
                # Calculate zero activation ratio per neuron using appropriate tolerance
                zero_ratios = np.mean(
                    np.abs(activation) <= thresholds["zero_tolerance"], axis=0
                )
            else:
                layer_neurons = 1
                zero_ratios = np.array(
                    [np.mean(np.abs(activation) <= thresholds["zero_tolerance"])]
                )
            layer_dead = np.sum(zero_ratios > thresholds["dead_threshold"])
            total_neurons += layer_neurons
            dead_neurons += layer_dead
        dead_percentage = (
            (dead_neurons / total_neurons * 100) if total_neurons > 0 else 0.0
        )
        if dead_percentage > 30.0:
            status = "🔴"
        elif dead_percentage > 10.0:
            status = "🟡"
        else:
            status = "🟢"

        return dead_percentage, status

    def monitor_vanishing_gradients(
        self, gradients: List[np.ndarray]
    ) -> Tuple[float, str]:
        """
        Detect vanishing gradient problem using research-validated metrics.

        Monitors gradient flow through the network to detect vanishing gradients
        based on variance analysis from Glorot & Bengio (2010). Healthy networks
        maintain similar gradient variance across layers.

        Args:
            gradients (list[NDArray[np.float64]]): Gradient arrays for each layer.

        Returns:
            tuple[float, str]: (vgp_severity, status_emoji) where:
                - vgp_severity: Float in [0,1] indicating severity
                - status: 🟢 (healthy), 🟡 (warning), 🔴 (critical)

        Note:
            Implementation based on "Understanding the difficulty of training
            deep feedforward neural networks" (Glorot & Bengio 2010).
        """
        if not gradients or len(gradients) < 2:
            return 0.0, "🟡"
        # Calculate layer-wise gradient statistics (Glorot & Bengio 2010)
        layer_variances = []
        layer_rms = []
        for grad in gradients:
            if grad.size > 0:
                grad_flat = grad.flatten()
                variance = np.var(grad_flat)
                rms = np.sqrt(np.mean(grad_flat**2))
                layer_variances.append(variance)
                layer_rms.append(rms)
        if len(layer_variances) < 2:
            return 0.0, "🟡"

        # Method 1: Variance ratio analysis (PRIMARY - Glorot & Bengio 2010)
        # Healthy networks: variance ratio ≈ 1.0, Vanishing: early/late >> 1.0
        variance_ratios = []
        for i in range(len(layer_variances) - 1):
            if layer_variances[i + 1] > 1e-12:
                ratio = layer_variances[i] / layer_variances[i + 1]
                variance_ratios.append(ratio)
        vgp_severity = 0.0
        if variance_ratios:
            mean_variance_ratio = np.mean(variance_ratios)
            if mean_variance_ratio > 2.0:
                vgp_severity = min(0.8, (mean_variance_ratio - 2.0) / 8.0)

        # Method 2: RMS gradient magnitude decay (SECONDARY)
        min_rms = min(layer_rms) if layer_rms else 0.0
        if min_rms < 1e-7:  # Severely vanished gradients
            vgp_severity = max(vgp_severity, 0.7)
        elif min_rms < 1e-5:  # Moderately vanished
            vgp_severity = max(vgp_severity, 0.4)

        if vgp_severity < 0.15:
            status = "🟢"
        elif vgp_severity < 0.4:
            status = "🟡"
        else:
            status = "🔴"

        return vgp_severity, status

    def monitor_exploding_gradients(
        self, gradients: List[np.ndarray]
    ) -> Tuple[float, str]:
        """
        Detect exploding gradient problem using gradient norm analysis.

        Monitors gradient magnitudes to detect exploding gradients based on
        research by Pascanu et al. (2013). Uses both global norm and per-layer
        analysis to identify unstable training dynamics.

        Args:
            gradients (list[NDArray[np.float64]]): Gradient arrays for each layer.

        Returns:
            tuple[float, str]: (egp_severity, status_emoji) where:
                - egp_severity: Float in [0,1] indicating severity
                - status: 🟢 (stable), 🟡 (elevated), 🔴 (exploding)

        Note:
            Based on "On the difficulty of training recurrent neural networks"
            (Pascanu et al. 2013) gradient clipping and norm analysis.
        """
        if not gradients or len(gradients) < 1:
            return 0.0, "🟡"

        # Calculate gradient norms (Pascanu et al. 2013 method)
        layer_norms = []
        total_norm_squared = 0.0

        for grad in gradients:
            if grad.size > 0:
                grad_flat = grad.flatten()
                layer_norm = np.linalg.norm(grad_flat)
                layer_norms.append(layer_norm)
                total_norm_squared += layer_norm**2

        if not layer_norms:
            return 0.0, "🟡"

        total_norm = np.sqrt(total_norm_squared)
        max_layer_norm = max(layer_norms)
        egp_severity = 0.0

        # Method 1: Global gradient norm (PRIMARY - Pascanu et al. 2013)
        # Literature suggests clipping thresholds typically 1.0-5.0
        if total_norm > 10.0:
            norm_severity = min(1.0, (total_norm - 10.0) / 10.0)
            egp_severity = max(egp_severity, norm_severity)
        elif total_norm > 5.0:
            norm_severity = (total_norm - 5.0) / 5.0
            egp_severity = max(egp_severity, norm_severity * 0.6)

        # Method 2: Individual layer explosion (SECONDARY)
        # Any single layer with extreme gradients
        if max_layer_norm > 5.0:
            layer_severity = min(0.5, (max_layer_norm - 5.0) / 5.0)
            egp_severity = min(1.0, egp_severity + layer_severity)

        if egp_severity < 0.1:
            status = "🟢"
        elif egp_severity < 0.4:
            status = "🟡"
        else:
            status = "🔴"

        return egp_severity, status

    def monitor_weight_health(self, weights: List[np.ndarray]) -> Tuple[float, str]:
        """
        Simple, research-backed weight health monitor.
        Based on Glorot & Bengio (2010) and He et al. (2015) initialization theory.
        Args:
            weights: List of weight matrices
        Returns:
            Tuple of (health_score, status)
        """
        if not weights or len(weights) == 0:
            return 0.0, "WARN"
        health_scores = []
        for w in weights:
            if w.size == 0:
                continue
            w_flat = w.flatten()
            # Initialization theory: He for ReLU, Glorot for others
            fan_in = w.shape[1] if len(w.shape) == 2 else w.shape[0]
            he_std = np.sqrt(2.0 / (fan_in + 1e-8))
            actual_std = np.std(w_flat)
            std_ratio = actual_std / (he_std + 1e-8)
            # Healthy if std within 0.5x to 2x theoretical
            init_health = 1.0 if 0.5 <= std_ratio <= 2.0 else 0.0
            # Dead weights: too many near zero
            dead_ratio = np.mean(np.abs(w_flat) < 1e-8)
            dead_health = 1.0 if dead_ratio < 0.1 else 0.0
            # Numerical stability
            finite_health = 1.0 if np.all(np.isfinite(w_flat)) else 0.0
            health = (init_health + dead_health + finite_health) / 3.0
            health_scores.append(health)
        if not health_scores:
            return 0.0, "🟡"
        avg_health = np.mean(health_scores)
        if avg_health >= 0.8:
            status = "🟢"
        elif avg_health >= 0.5:
            status = "🟡"
        else:
            status = "🔴"
        return avg_health, status

    def monitor_learning_progress(
        self, current_loss: float, val_loss: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Research-accurate learning progress monitor.
        Based on optimization literature: Bottou (2010), Goodfellow et al. (2016), Smith (2017).
        Key insights:
        - Progress = consistent loss reduction + convergence stability + generalization health
        - Uses exponential moving averages and plateau detection from literature
        Args:
            current_loss: Current training loss
            val_loss: Optional validation loss

        Returns:
            Tuple of (progress_score, emoji_status)
        """
        self.history["loss"].append(current_loss)
        if val_loss is not None:
            self.history["val_loss"].append(val_loss)

        if len(self.history["loss"]) < 5:
            return 0.7, "🟢"

        losses = np.array(list(self.history["loss"]))
        recent_window = min(20, len(losses))
        recent_losses = losses[-recent_window:]
        progress_score = 0.0

        # Method 1: Exponential decay trend (Bottou 2010 optimization theory)
        # Healthy SGD shows exponential loss decay in early stages
        if len(recent_losses) >= 10:
            # Fit exponential decay: loss = a * exp(-b * epoch) + c
            epochs = np.arange(len(recent_losses))
            try:
                # Log-linear fit to detect exponential decay
                log_losses = np.log(recent_losses + 1e-8)
                slope = np.polyfit(epochs, log_losses, 1)[0]

                # Negative slope = decreasing loss = good progress
                if slope < -0.01:  # Strong decay
                    decay_score = 0.4
                elif slope < -0.001:  # Moderate decay
                    decay_score = 0.25
                elif slope < 0.001:  # Slow but steady
                    decay_score = 0.1
                else:  # Increasing or flat
                    decay_score = 0.0

                progress_score += decay_score
            except:
                progress_score += 0.1

        # Method 2: Plateau detection (Research standard)
        # Check if stuck in plateau vs making progress
        if len(recent_losses) >= 5:
            recent_5 = recent_losses[-5:]
            loss_range = np.max(recent_5) - np.min(recent_5)
            relative_range = loss_range / (np.mean(recent_5) + 1e-8)

            # Small relative range = plateau, large = instability
            if relative_range < 0.01:  # Plateau detected
                plateau_score = 0.0
            elif relative_range < 0.05:  # Slow progress
                plateau_score = 0.1
            elif relative_range < 0.2:  # Good progress
                plateau_score = 0.3
            else:  # Too unstable
                plateau_score = 0.1

            progress_score += plateau_score

        # Method 3: Generalization gap (Goodfellow et al. 2016)
        if val_loss is not None and len(self.history["val_loss"]) >= 3:
            gap = val_loss - current_loss
            relative_gap = gap / (current_loss + 1e-8)

            # Healthy gap: 0.1-0.3, concerning >0.5
            if relative_gap < 0.3:
                gap_score = 0.3
            elif relative_gap < 0.5:
                gap_score = 0.1
            else:
                gap_score = 0.0

            progress_score += gap_score
        else:
            if len(self.history["loss"]) < 10:
                progress_score += 0.3
            else:
                progress_score += 0.15

        if progress_score > 0.5:
            status = "🟢"
        elif progress_score > 0.25:
            status = "🟡"
        else:
            status = "🔴"

        return progress_score, status

    def monitor_overfitting(
        self, train_loss: float, val_loss: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Research-accurate overfitting detection.
        Based on Prechelt (1998), Goodfellow et al. (2016), and Caruana et al. (2001).
        Key insights:
        - Overfitting = increasing generalization gap + validation curve deterioration
        Args:
            train_loss: Training loss
            val_loss: Validation loss

        Returns:
            Tuple of (overfitting_score, emoji_status)
        """
        self.history["loss"].append(train_loss)
        if val_loss is not None:
            self.history["val_loss"].append(val_loss)

        if val_loss is None or len(self.history["val_loss"]) < 5:
            return 0.0, "🟡"

        val_losses = np.array(list(self.history["val_loss"]))
        train_losses = np.array(list(self.history["loss"]))
        min_len = min(len(val_losses), len(train_losses))
        val_losses = val_losses[-min_len:]
        train_losses = train_losses[-min_len:]
        overfitting_score = 0.0

        # Method 1: Generalization Gap Analysis (Goodfellow et al. 2016)
        current_gap = val_loss - train_loss
        relative_gap = current_gap / (train_loss + 1e-8)
        if relative_gap > 0.5:  # Severe overfitting
            gap_score = 0.4
        elif relative_gap > 0.2:  # Moderate overfitting
            gap_score = 0.25
        elif relative_gap > 0.1:  # Mild overfitting
            gap_score = 0.1
        else:  # Healthy generalization
            gap_score = 0.0
        overfitting_score += gap_score

        # Method 2: Validation Curve Analysis (Prechelt 1998)
        # Classic early stopping: validation loss starts increasing
        if len(val_losses) >= 10:
            recent_window = min(10, len(val_losses))
            recent_val = val_losses[-recent_window:]
            # Check for validation loss increase trend
            epochs = np.arange(len(recent_val))
            try:
                slope = np.polyfit(epochs, recent_val, 1)[0]
                # Positive slope = validation loss increasing = overfitting
                if slope > 0.01:  # Strong validation increase
                    curve_score = 0.35
                elif slope > 0.005:  # Moderate increase
                    curve_score = 0.2
                elif slope > 0.001:  # Mild increase
                    curve_score = 0.1
                else:  # Stable or decreasing
                    curve_score = 0.0

                overfitting_score += curve_score
            except:
                overfitting_score += 0.05

        # Method 3: Training-Validation Divergence (Caruana et al. 2001)
        # Healthy training: both losses decrease together
        if len(train_losses) >= 5 and len(val_losses) >= 5:
            recent_train = train_losses[-5:]
            recent_val = val_losses[-5:]
            # Calculate trends
            train_trend = (recent_train[-1] - recent_train[0]) / (
                recent_train[0] + 1e-8
            )
            val_trend = (recent_val[-1] - recent_val[0]) / (recent_val[0] + 1e-8)

            # Divergence: train decreasing, validation increasing
            if train_trend < -0.01 and val_trend > 0.01:  # Strong divergence
                divergence_score = 0.25
            elif train_trend < 0 and val_trend > 0:  # Moderate divergence
                divergence_score = 0.15
            else:  # No concerning divergence
                divergence_score = 0.0

            overfitting_score += divergence_score

        if overfitting_score < 0.15:
            status = "🟢"
        elif overfitting_score < 0.4:
            status = "🟡"
        else:
            status = "🔴"

        return min(1.0, overfitting_score), status

    def monitor_gradient_snr(self, gradients: List[np.ndarray]) -> Tuple[float, str]:
        """
        Calculate Gradient Signal-to-Noise Ratio (GSNR) for optimization health.
        - Signal: RMS gradient magnitude (update strength)
        - Noise: Coefficient of variation (relative inconsistency)
        - GSNR = RMS_magnitude / (std_magnitude + ε)
        This measures gradient update consistency.
        Args:
            gradients: List of gradient arrays from each layer

        Returns:
            Tuple of (gsnr_score, emoji_status)
        """
        if not gradients or len(gradients) == 0:
            return 0.0, "🟡"
        grad_magnitudes = []
        for grad in gradients:
            if grad.size > 0:
                grad_flat = grad.flatten()
                magnitudes = np.abs(grad_flat)
                grad_magnitudes.extend(magnitudes)
        if len(grad_magnitudes) == 0:
            return 0.0, "🟡"
        grad_magnitudes = np.array(grad_magnitudes)
        if np.all(grad_magnitudes < 1e-10):
            return 0.0, "🟡"

        # RESEARCH-VALIDATED GSNR: Two approaches with literature analysis
        # CLASSICAL SNR (μ²/σ²) - from ICCV 2023 papers (Michalkiewicz et al., Sun et al.)
        # Problem: Always ≈0 in healthy SGD where mean≈0 is normal
        # mean_grad = np.mean(grad_magnitudes)
        # variance_grad = np.var(grad_magnitudes)
        # classical_gsnr = (mean_grad**2) / (variance_grad + 1e-10)
        # PRACTICAL SNR (mean|g|/std|g|) - Gradient magnitude consistency
        # Advantage: Non-zero values for meaningful training monitoring
        mean_magnitude = np.mean(grad_magnitudes)
        std_magnitude = np.std(grad_magnitudes)
        if mean_magnitude < 1e-10:
            return 0.0, "🟡"
        gsnr = mean_magnitude / (std_magnitude + 1e-10)
        # Based on actual SGD training data (your values: 0.6-0.9 are healthy!)
        # - GSNR > 1.5: Very consistent gradient magnitudes
        # - GSNR 0.4-1.5: Normal SGD consistency
        # - GSNR < 0.4: High variance/problematic gradients
        if gsnr > 1.5:
            status = "🟢"
        elif gsnr > 0.4:
            status = "🟡"
        else:
            status = "🔴"

        return gsnr, status

    def monitor_activation_saturation(
        self, activations: List[np.ndarray], activation_functions: List[str] = None
    ) -> Tuple[float, str]:
        """
        Research-accurate activation saturation detection.
        Based on Glorot & Bengio (2010), Hochreiter (1991), and He et al. (2015).
        Key insights:
        - Saturation = extreme activation values + poor gradient flow + skewed distributions
        - Uses function-specific thresholds and statistical distribution analysis
        - Tracks saturation propagation through network layers
        Args:
            activations: List of activation arrays from each layer
            activation_functions: List of activation function names for each layer
        Returns:
            Tuple of (saturation_score, emoji_status)
        """
        if not activations or len(activations) == 0:
            return 0.0, "🟡"
        layer_saturations = []
        # Analyze each hidden layer for saturation
        for i, activation in enumerate(activations[:-1]):
            if activation.size == 0:
                continue
            activation_flat = activation.flatten()
            activation_func = (
                activation_functions[i]
                if activation_functions and i < len(activation_functions)
                else "unknown"
            )
            layer_saturation = 0.0
            # Method 1: Function-specific extreme value analysis (Glorot & Bengio 2010)
            if activation_func.lower() == "tanh":
                # Tanh: saturated at ±1, research threshold: ±0.9
                extreme_high = np.mean(activation_flat > 0.9)
                extreme_low = np.mean(activation_flat < -0.9)
                extreme_saturation = extreme_high + extreme_low

            elif activation_func.lower() == "sigmoid":
                # Sigmoid: saturated at 0/1, research threshold: <0.1 or >0.9
                extreme_high = np.mean(activation_flat > 0.9)
                extreme_low = np.mean(activation_flat < 0.1)
                extreme_saturation = extreme_high + extreme_low

            elif activation_func.lower() in ["relu", "leakyrelu"]:
                # High activation values indicate potential saturation
                extreme_saturation = np.mean(activation_flat > 10.0)
            else:
                q01, q99 = np.percentile(activation_flat, [1, 99])
                if q99 - q01 < 0.1:  # Very narrow range = likely saturated
                    extreme_saturation = 0.8
                else:
                    extreme_saturation = 0.0
            # Method 2: Statistical distribution analysis (Hochreiter 1991)
            # Healthy activations should be well-distributed
            try:
                activation_var = np.var(activation_flat)
                # Low variance indicates saturation
                if activation_func.lower() == "tanh":
                    # Tanh should have variance around 0.1-0.3 when healthy
                    if activation_var < 0.05:  # Very low variance
                        distribution_score = 0.4
                    elif activation_var < 0.1:  # Low variance
                        distribution_score = 0.2
                    else:
                        distribution_score = 0.0
                elif activation_func.lower() == "sigmoid":
                    # Sigmoid should have variance around 0.05-0.25 when healthy
                    if activation_var < 0.02:  # Very low variance
                        distribution_score = 0.4
                    elif activation_var < 0.05:  # Low variance
                        distribution_score = 0.2
                    else:
                        distribution_score = 0.0
                else:
                    # General case: very low variance indicates problems
                    if activation_var < 0.01:
                        distribution_score = 0.3
                    else:
                        distribution_score = 0.0
            except:
                distribution_score = 0.0

            # Method 3: Gradient flow estimation (inferred from activation patterns)
            # If activations are at extremes, gradients will be near zero
            if activation_func.lower() in ["tanh", "sigmoid"]:
                # Count neurons in "gradient-dead zones"
                if activation_func.lower() == "tanh":
                    # Tanh derivative ≈ 0 when |x| > 2.5, very small when |x| > 1.5
                    gradient_dead = np.mean(np.abs(activation_flat) > 1.5)
                else:  # sigmoid
                    # Sigmoid derivative ≈ 0 when x < -3 or x > 3 (pre-activation)
                    # Post-activation: very small when close to 0 or 1
                    gradient_dead = np.mean(
                        (activation_flat < 0.05) | (activation_flat > 0.95)
                    )

                gradient_score = gradient_dead
            else:
                gradient_score = 0.0
            layer_saturation = (
                extreme_saturation * 0.5
                + distribution_score * 0.3
                + gradient_score * 0.2
            )

            layer_saturations.append(layer_saturation)
        if not layer_saturations:
            return 0.0, "🟡"

        # Method 4: Layer propagation analysis (He et al. 2015)
        # Early layer saturation is more problematic than late layer saturation
        weighted_saturations = []
        for i, sat in enumerate(layer_saturations):
            # Earlier layers get higher weight (more impact on gradient flow)
            weight = 1.0 + (len(layer_saturations) - i) * 0.1
            weighted_saturations.append(sat * weight)
        avg_saturation = np.mean(weighted_saturations) / 1.5  # Normalize for weighting
        self.history["saturation"].append(avg_saturation)
        if avg_saturation < 0.1:  # <10% saturation
            status = "🟢"  # Healthy activation distribution
        elif avg_saturation < 0.25:  # 10-25% saturation
            status = "🟡"  # Moderate saturation
        else:  # >25% saturation
            status = "🔴"  # Severe saturation

        return min(1.0, avg_saturation), status

    def monitor_plateau(
        self,
        current_loss: float,
        val_loss: Optional[float] = None,
        current_gradients: Optional[List[np.ndarray]] = None,
    ) -> Tuple[float, str]:
        """
        Research-accurate training plateau detection.
        Based on Prechelt (1998), Bengio (2012), and Smith (2017).
        Key insights:
        - Plateau = statistical stagnation + loss of learning momentum + gradient analysis
        - Uses multi-scale analysis and statistical significance testing
        - Integrates validation correlation and gradient magnitude trends
        Args:
            current_loss: Current training loss
            val_loss: Optional validation loss for correlation analysis
            current_gradients: Optional gradient arrays for gradient-based detection

        Returns:
            Tuple of (plateau_score, emoji_status)
        """
        self.history["loss"].append(current_loss)
        if val_loss is not None:
            self.history["val_loss"].append(val_loss)

        if len(self.history["loss"]) < 15:
            return 0.0, "🟢"

        losses = np.array(list(self.history["loss"]))
        plateau_score = 0.0

        # Method 1: Multi-scale stagnation analysis (Prechelt 1998)
        # Check different time horizons for plateau patterns
        short_window = losses[-5:]  # Short-term (5 epochs)
        medium_window = losses[-10:]  # Medium-term (10 epochs)
        long_window = losses[-15:]  # Long-term (15 epochs)
        stagnation_scores = []
        for window, name in [
            (short_window, "short"),
            (medium_window, "medium"),
            (long_window, "long"),
        ]:
            if len(window) < 3:
                continue
            # Statistical stagnation test
            window_var = np.var(window)
            window_mean = np.mean(window)
            relative_var = window_var / (window_mean**2 + 1e-8)
            # Trend analysis using linear regression
            epochs = np.arange(len(window))
            try:
                slope, intercept = np.polyfit(epochs, window, 1)
                # Normalize slope by initial loss value
                normalized_slope = slope / (window[0] + 1e-8)
                # Stagnation indicators
                var_stagnant = relative_var < 1e-4  # Very low relative variance
                trend_stagnant = abs(normalized_slope) < 1e-4  # Near-zero trend
                if name == "short":
                    weight = 0.2  # Short-term stagnation less concerning
                elif name == "medium":
                    weight = 0.4  # Medium-term more important
                else:  # long
                    weight = 0.4  # Long-term most concerning
                stagnation = (var_stagnant + trend_stagnant) / 2.0
                stagnation_scores.append(stagnation * weight)
            except:
                stagnation_scores.append(0.0)
        plateau_score += sum(stagnation_scores)
        # Method 2: Statistical significance testing (Prechelt 1998)
        # Test if recent performance is significantly different from earlier
        if len(losses) >= 20:
            early_window = losses[-20:-10]  # Earlier period
            recent_window = losses[-10:]  # Recent period
            # Perform statistical test (simplified t-test concept)
            early_mean = np.mean(early_window)
            recent_mean = np.mean(recent_window)
            # Combined variance estimate
            early_var = np.var(early_window)
            recent_var = np.var(recent_window)
            pooled_var = (early_var + recent_var) / 2.0
            if pooled_var > 1e-10:
                # Effect size calculation
                effect_size = abs(early_mean - recent_mean) / np.sqrt(pooled_var)
                # Small effect size indicates no significant change (plateau)
                if effect_size < 0.2:  # Small effect (Cohen's d)
                    significance_score = 0.3
                elif effect_size < 0.5:  # Medium effect
                    significance_score = 0.1
                else:  # Large effect - no plateau
                    significance_score = 0.0
                plateau_score += significance_score

        # Method 3: Gradient-based plateau detection (Smith 2017)
        if current_gradients is not None and len(current_gradients) > 0:
            # Calculate current gradient magnitude
            current_grad_norm = 0.0
            for grad in current_gradients:
                if grad.size > 0:
                    current_grad_norm += np.sum(grad**2)
            current_grad_norm = np.sqrt(current_grad_norm)
            # Store gradient history
            if not hasattr(self, "_gradient_history"):
                self._gradient_history = []
            self._gradient_history.append(current_grad_norm)
            # Keep last 10 gradient norms
            if len(self._gradient_history) > 10:
                self._gradient_history = self._gradient_history[-10:]
            # Analyze gradient plateau
            if len(self._gradient_history) >= 5:
                grad_norms = np.array(self._gradient_history)
                grad_var = np.var(grad_norms)
                grad_mean = np.mean(grad_norms)
                # Low gradient variance + low absolute gradients = plateau
                relative_grad_var = grad_var / (grad_mean**2 + 1e-8)
                if relative_grad_var < 1e-3 and grad_mean < 1e-3:
                    gradient_score = 0.25
                elif relative_grad_var < 1e-2:
                    gradient_score = 0.15
                else:
                    gradient_score = 0.0

                plateau_score += gradient_score
        # Method 4: Validation-training correlation (Huang et al. 2017)
        if val_loss is not None and len(self.history["val_loss"]) >= 10:
            val_losses = np.array(list(self.history["val_loss"])[-10:])
            train_losses = losses[-10:]
            # Both should plateau together for true learning plateau
            val_var = np.var(val_losses)
            train_var = np.var(train_losses[-10:])
            val_mean = np.mean(val_losses)
            train_mean = np.mean(train_losses[-10:])

            val_rel_var = val_var / (val_mean**2 + 1e-8)
            train_rel_var = train_var / (train_mean**2 + 1e-8)

            # Both metrics stagnant = true plateau
            if val_rel_var < 1e-3 and train_rel_var < 1e-3:
                correlation_score = 0.2
            elif val_rel_var < 1e-2 and train_rel_var < 1e-2:
                correlation_score = 0.1
            else:
                correlation_score = 0.0

            plateau_score += correlation_score
        plateau_score = min(1.0, plateau_score)
        if plateau_score < 0.2:
            status = "🟢"  # Healthy learning progress
        elif plateau_score < 0.5:
            status = "🟡"  # Possible platea
        else:
            status = "🔴"  # Plateau detected
        return plateau_score, status

    def monitor_weight_update_ratio(
        self, weights: List[np.ndarray], weight_updates: List[np.ndarray]
    ) -> Tuple[float, str]:
        """
        Monitor Weight Update to Weight magnitude Ratios (WUR) for learning rate validation.
        Research-based implementation using:
        - Smith (2015): Learning rate should produce WUR ~10^-3 to 10^-2 for stable training
        - Zeiler (2012): Update magnitude should be proportional to weight magnitude
        Formula: WUR = ||weight_update|| / ||weight|| per layer
        Args:
            weights: Current weight matrices
            weight_updates: Weight update matrices (gradients * learning_rate)

        Returns:
            Tuple of (median_wur, status)
        """
        if not weights or not weight_updates or len(weights) != len(weight_updates):
            return 0.0, "WARN"

        wurs = []
        for w, dw in zip(weights, weight_updates):
            if w.size == 0 or dw.size == 0:
                continue
            weight_norm = np.linalg.norm(w.flatten())
            update_norm = np.linalg.norm(dw.flatten())
            if weight_norm > 1e-10:
                wur = update_norm / weight_norm
                wurs.append(wur)
        if not wurs:
            return 0.0, "🟡"
        # Use median for robustness (research standard)
        median_wur = np.median(wurs)
        # Research-based thresholds from Smith (2015)
        if 1e-3 <= median_wur <= 1e-2:
            status = "🟢"
        elif 1e-4 <= median_wur <= 5e-2:
            status = "🟡"
        else:
            status = "🔴"

        return median_wur, status

    def monitor_step(
        self,
        epoch: int,
        train_loss: float,
        val_loss: Optional[float] = None,
        activations: Optional[List[np.ndarray]] = None,
        gradients: Optional[List[np.ndarray]] = None,
        weights: Optional[List[np.ndarray]] = None,
        weight_updates: Optional[List[np.ndarray]] = None,
        activation_functions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform one monitoring step and return all metrics.
        Args:
            epoch: Current epoch number
            train_loss: Training loss
            val_loss: Validation loss (optional)
            activations: Layer activations (optional)
            gradients: Layer gradients (optional)
            weights: Layer weights (optional)
            weight_updates: Weight updates (optional)
            activation_functions: List of activation function names (optional)

        Returns:
            Dictionary containing all monitoring results
        """
        self.epoch_count = epoch
        results = {}
        if activations:
            dead_pct, dead_status = self.monitor_relu_dead_neurons(
                activations, activation_functions
            )
            saturation_score, saturation_status = self.monitor_activation_saturation(
                activations, activation_functions
            )
            results["dead_neurons"] = {"value": dead_pct, "status": dead_status}
            results["saturation"] = {
                "value": saturation_score,
                "status": saturation_status,
            }
        else:
            results["dead_neurons"] = {"value": 0.0, "status": "🟡"}
            results["saturation"] = {"value": 0.0, "status": "🟡"}

        if gradients:
            vgp, vgp_status = self.monitor_vanishing_gradients(gradients)
            egp, egp_status = self.monitor_exploding_gradients(gradients)
            snr, snr_status = self.monitor_gradient_snr(gradients)
            results["vgp"] = {"value": vgp, "status": vgp_status}
            results["egp"] = {"value": egp, "status": egp_status}
            results["snr"] = {"value": snr, "status": snr_status}
        else:
            results["vgp"] = {"value": 0.0, "status": "🟡"}
            results["egp"] = {"value": 0.0, "status": "🟡"}
            results["snr"] = {"value": 0.0, "status": "🟡"}

        if weights:
            weight_health, health_status = self.monitor_weight_health(weights)
            results["weight_health"] = {"value": weight_health, "status": health_status}
        else:
            results["weight_health"] = {"value": 0.0, "status": "🟡"}

        if weights and weight_updates:
            wur, wur_status = self.monitor_weight_update_ratio(weights, weight_updates)
            results["wur"] = {"value": wur, "status": wur_status}
        else:
            results["wur"] = {"value": 0.0, "status": "🟡"}

        progress, progress_status = self.monitor_learning_progress(train_loss, val_loss)
        overfitting, overfit_status = self.monitor_overfitting(train_loss, val_loss)
        plateau, plateau_status = self.monitor_plateau(train_loss, val_loss, gradients)
        results["progress"] = {"value": progress, "status": progress_status}
        results["overfitting"] = {"value": overfitting, "status": overfit_status}
        results["plateau"] = {"value": plateau, "status": plateau_status}
        return results

    def _align_banner(self, lines: List[str], sep="|", padding=1) -> str:
        rows = [[cell.strip() for cell in line.split(sep)] for line in lines]
        max_cols = max(len(r) for r in rows)
        for r in rows:
            while len(r) < max_cols:
                r.append("")
        col_widths = []
        for c in range(max_cols):
            maxw = max(wcswidth(rows[r][c]) or 0 for r in range(len(rows)))
            col_widths.append(maxw)
        out_lines = []
        for r in rows:
            parts = []
            for i, cell in enumerate(r):
                cur = wcswidth(cell) or 0
                pad = col_widths[i] - cur
                parts.append(cell + " " * (pad + padding))
            out_lines.append((" " + sep + " ").join(parts).rstrip())
        return "\n".join(out_lines)

    def format_monitoring_output(self, results: Dict[str, Any]) -> str:
        line1 = f"SNR: {results['snr']['status']} ({results['snr']['value']:.2f}),    | Dead Neurons: {results['dead_neurons']['status']} ({results['dead_neurons']['value']:.2f}%) | VGP:      {results['vgp']['status']} | EGP:     {results['egp']['status']} |  Weight Health: {results['weight_health']['status']}"

        line2 = f"WUR: {results['wur']['status']} ({results['wur']['value']:.2e}) | Saturation:   {results['saturation']['status']} ({results['saturation']['value']:.2f})  | Progress: {results['progress']['status']} | Plateau: {results['plateau']['status']} |  Overfitting:   {results['overfitting']['status']}"

        # Use the exact same alignment function that works perfectly
        lines = [line1, line2]
        aligned_output = self._align_banner(lines, sep="|", padding=1)

        # Add separator lines above and below
        separator_line = "-" * 100
        return f"{separator_line}\n{aligned_output}\n{separator_line}"
