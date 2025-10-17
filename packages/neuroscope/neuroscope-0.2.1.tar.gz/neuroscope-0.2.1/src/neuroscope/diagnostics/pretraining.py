"""
Pre-Training Analysis for NeuroScope MLP Framework
Focused pre-training analysis tools for neural network assessment before training.
"""

from typing import Any, Dict, List

import numpy as np


class PreTrainingAnalyzer:
    """
    Comprehensive pre-training diagnostic tool for neural networks.

    Analyzes model architecture, weight initialization, and data compatibility
    before training begins. Implements research-validated checks to identify
    potential training issues early, based on established deep learning principles
    from Glorot & Bengio (2010), He et al. (2015), and others.

    Args:
        model: Compiled MLP model instance with initialized weights.

    Attributes:
        model: Reference to the neural network model.
        results (dict): Cached analysis results.

    Example:
        >>> from neuroscope.diagnostics import PreTrainingAnalyzer
        >>> model = MLP([784, 128, 10])
        >>> model.compile(lr=1e-3)
        >>> analyzer = PreTrainingAnalyzer(model)
        >>> results = analyzer.analyze(X_train, y_train)
    """

    def __init__(self, model):
        """Initialize analyzer with a compiled model."""
        if not hasattr(model, "weights") or not hasattr(model, "biases"):
            raise ValueError("Model must be weight initialized.")
        if not getattr(model, "compiled", False):
            raise ValueError("Model must be compiled.")

        self.model = model
        self.results = {}

    def analyze_initial_loss(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Validate initial loss against theoretical expectations.

        Compares the model's initial loss (before training) with theoretical
        baselines for different task types. For classification, expects loss
        near -log(1/num_classes). For regression, compares against variance-based
        baseline as described in Goodfellow et al. (2016).

        Args:
            X (NDArray[np.float64]): Input data of shape (N, input_dim).
            y (NDArray[np.float64]): Target values of shape (N,) or (N, output_dim).

        Returns:
            dict: Analysis results containing:
                - initial_loss: Computed initial loss value
                - expected_loss: Theoretical expected loss
                - ratio: initial_loss / expected_loss
                - task_type: Detected task type (regression/classification)
                - status: "PASS", "WARN", or "FAIL"
                - note: Diagnostic message

        Example:
            >>> results = analyzer.analyze_initial_loss(X_train, y_train)
            >>> print(f"Initial loss check: {results['status']}")
        """
        try:
            initial_loss, _ = self.model.evaluate(X, y)

            # Determine task type and expected loss
            unique_targets = np.unique(y)
            is_binary = len(unique_targets) == 2 and set(unique_targets).issubset(
                {0, 1}
            )
            is_multiclass = len(unique_targets) > 2 and all(
                isinstance(x, (int, np.integer)) for x in unique_targets
            )

            if is_binary:
                expected_loss = -np.log(0.5)  # Binary cross-entropy
                task_type = "Binary Classification"
            elif is_multiclass:
                num_classes = len(unique_targets)
                expected_loss = -np.log(1.0 / num_classes)
                task_type = f"{num_classes}-Class Classification"
            else:
                """For regression, the theoretically optimal constant predictor is the mean.
                With common zero-mean random init (He/Xavier) and zero biases, initial predictions tend to be near 0.
                Use baseline MSE of predicting 0 vs mean(y): E[(y-0)^2] = Var(y) + (E[y])^2. This is a more faithful baseline than Var(y).
                """
                y_mean = float(np.mean(y))
                expected_loss = float(np.var(y) + y_mean**2)
                task_type = "Regression"

            ratio = initial_loss / expected_loss if expected_loss > 0 else float("inf")

            if is_binary or is_multiclass:
                status = (
                    "PASS"
                    if 0.8 <= ratio <= 1.5
                    else "WARN" if 0.5 <= ratio <= 2.0 else "FAIL"
                )
            else:
                status = "PASS" if ratio <= 2.0 else "WARN" if ratio <= 5.0 else "FAIL"

            return {
                "initial_loss": initial_loss,
                "expected_loss": expected_loss,
                "ratio": ratio,
                "task_type": task_type,
                "status": status,
                "note": self._get_loss_note(ratio, task_type),
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "note": "Check model compilation & data format.",
            }

    def analyze_weight_init(self) -> Dict[str, Any]:
        """
        Validate weight initialization against theoretical optima.

        Analyzes weight initialization quality by comparing actual weight standard
        deviations against theoretically optimal values for different activation
        functions. Based on He initialization (He et al. 2015) for ReLU variants
        and Xavier initialization (Glorot & Bengio 2010) for sigmoid/tanh.

        Returns:
            dict: Analysis results containing:
                - layers: List of per-layer initialization analysis
                - status: Overall initialization quality ("PASS", "WARN", "FAIL")
                - note: Summary diagnostic message

        Example:
            >>> results = analyzer.analyze_weight_init()
            >>> for layer in results['layers']:
            ...     print(f"Layer {layer['layer']}: {layer['status']}")
        """
        results = []
        overall_status = "PASS"
        actual_init_method = getattr(self.model, "init_method", "unknown")

        for i, (W, b) in enumerate(zip(self.model.weights, self.model.biases)):
            fan_in = W.shape[0]
            fan_out = W.shape[1]
            activation = self.model.hidden_activation
            actual_std = float(np.std(W))
            if actual_init_method == "random":
                expected_std = 0.01
                init_type = "Random"
                if 0.005 <= actual_std <= 0.05:
                    layer_status = "PASS"
                elif 0.001 <= actual_std <= 0.1:
                    layer_status = "WARN"
                else:
                    layer_status = "FAIL"
            else:
                if activation in ["relu", "leaky_relu"]:
                    expected_std = np.sqrt(
                        2.0 / fan_in
                    )  # He initialization (He et al. 2015)
                    init_type = "He"
                elif activation in ["tanh", "sigmoid"]:
                    expected_std = np.sqrt(
                        2.0 / (fan_in + fan_out)
                    )  # Xavier initialization (Glorot & Bengio 2010)
                    init_type = "Xavier"
                elif activation == "selu":
                    expected_std = np.sqrt(
                        1.0 / fan_in
                    )  # Lecun normal (Lecun et al. 1998)
                    init_type = "Lecun"
                else:
                    expected_std = np.sqrt(
                        2.0 / (fan_in + fan_out)
                    )  # Xavier uniform (Glorot & Bengio 2010)
                    init_type = "Xavier-Uniform"

                std_ratio = actual_std / expected_std

                if 0.7 <= std_ratio <= 1.4:
                    layer_status = "PASS"
                elif 0.5 <= std_ratio <= 2.0:
                    layer_status = "WARN"
                    overall_status = (
                        "WARN" if overall_status == "PASS" else overall_status
                    )
                else:
                    layer_status = "FAIL"
                    overall_status = "FAIL"

            if overall_status != "FAIL":
                if layer_status == "WARN":
                    overall_status = "WARN"
                elif layer_status == "FAIL":
                    overall_status = "FAIL"

            result_entry = {
                "layer": i + 1,
                "actual_std": actual_std,
                "init_type": init_type,
                "status": layer_status,
            }
            if actual_init_method != "random":
                result_entry["expected_std"] = expected_std
                result_entry["ratio"] = std_ratio

            results.append(result_entry)

        return {
            "layers": results,
            "status": overall_status,
            "note": self._get_init_note(overall_status),
        }

    def analyze_layer_capacity(self) -> Dict[str, Any]:
        """Analyze information bottlenecks and layer capacity issues."""
        layer_dims = self.model.layer_dims
        bottlenecks = []
        for i in range(len(layer_dims) - 2):
            current_dim = layer_dims[i]
            next_dim = layer_dims[i + 1]
            # More tolerant thresholds based on modern architecture patterns
            if next_dim < current_dim * 0.1:  # Extreme bottleneck (90%+ reduction)
                bottlenecks.append(
                    {
                        "layer": i + 1,
                        "from_dim": current_dim,
                        "to_dim": next_dim,
                        "reduction": (current_dim - next_dim) / current_dim,
                        "severity": "SEVERE",
                    }
                )
            elif (
                next_dim < current_dim * 0.2
            ):  # Significant bottleneck (80%+ reduction)
                bottlenecks.append(
                    {
                        "layer": i + 1,
                        "from_dim": current_dim,
                        "to_dim": next_dim,
                        "reduction": (current_dim - next_dim) / current_dim,
                        "severity": "MODERATE",
                    }
                )

        total_params = sum(
            W.size + b.size for W, b in zip(self.model.weights, self.model.biases)
        )

        if len(bottlenecks) == 0:
            status = "PASS"
        elif any(b["severity"] == "SEVERE" for b in bottlenecks):
            status = "FAIL"
        else:
            status = "WARN"

        return {
            "bottlenecks": bottlenecks,
            "total_params": total_params,
            "status": status,
            "note": self._get_capacity_note(bottlenecks),
        }

    def analyze_architecture_sanity(self) -> Dict[str, Any]:
        """
        Perform comprehensive architecture validation.

        Validates network architecture against established deep learning principles
        and best practices. Checks for common architectural pitfalls such as
        incompatible activation functions, inappropriate depth, and problematic
        layer configurations based on research findings.

        Returns:
            dict: Analysis results containing:
                - issues: List of critical architectural problems
                - warnings: List of potential concerns
                - status: Overall architecture quality ("PASS", "WARN", "FAIL")
                - note: Summary diagnostic message

        Note:
            Based on research from Bengio et al. (2009) on vanishing gradients,
            modern best practices for deep architectures, and activation function
            compatibility studies.

        Example:
            >>> results = analyzer.analyze_architecture_sanity()
            >>> if results['issues']:
            ...     print("Critical issues found:", results['issues'])
        """
        issues = []
        warnings = []
        layer_dims = self.model.layer_dims
        input_dim = layer_dims[0]
        if input_dim > 5000:
            warnings.append(
                "Very high input dimensionality - consider dimensionality reduction"
            )
        elif input_dim < 2:
            issues.append("Input dimension too small")
        output_dim = layer_dims[-1]
        if hasattr(self.model, "out_activation"):
            if self.model.out_activation == "sigmoid" and output_dim != 1:
                issues.append("Sigmoid should have 1 output neuron")
            elif self.model.out_activation == "softmax" and output_dim < 2:
                issues.append("Softmax needs at least 2 output neurons")
        depth = len(layer_dims) - 1
        if depth > 10:
            warnings.append("Deep network - consider residual connections")

        # Activation compatibility (research-validated)
        if hasattr(self.model, "hidden_activation"):
            if self.model.hidden_activation == "sigmoid" and depth > 3:
                issues.append(
                    "Sigmoid in deep networks causes vanishing gradients (Bengio et al. 2009)"
                )
            elif self.model.hidden_activation == "tanh" and depth > 5:
                warnings.append("Tanh in very deep networks may cause gradient issues")

        if issues:
            status = "FAIL"
        elif warnings:
            status = "WARN"
        else:
            status = "PASS"

        return {
            "issues": issues,
            "warnings": warnings,
            "status": status,
            "note": self._get_architecture_note(issues, warnings),
        }

    def analyze_capacity_data_ratio(
        self, X: np.ndarray, y: np.ndarray
    ) -> Dict[str, Any]:
        """Analyze parameter count relative to training data size."""
        n_samples = X.shape[0]
        total_params = sum(
            W.size + b.size for W, b in zip(self.model.weights, self.model.biases)
        )
        params_per_sample = total_params / n_samples
        if params_per_sample < 3.0:
            overfitting_risk = "LOW"
            status = "PASS"
        elif params_per_sample < 10.0:
            overfitting_risk = "MODERATE"
            status = "PASS"
        elif params_per_sample < 50.0:
            overfitting_risk = "HIGH"
            status = "WARN"
        else:
            overfitting_risk = "CRITICAL"
            status = "WARN"

        return {
            "n_samples": n_samples,
            "total_params": total_params,
            "params_per_sample": params_per_sample,
            "overfitting_risk": overfitting_risk,
            "status": status,
            "note": self._get_data_ratio_note(
                params_per_sample, n_samples, total_params
            ),
        }

    def analyze_convergence_feasibility(
        self, X: np.ndarray, y: np.ndarray
    ) -> Dict[str, Any]:
        """Assess whether the current setup can theoretically converge."""
        feasibility_score = 0
        max_score = 6
        issues = []
        try:
            from mlp.core import _BackwardPass, _ForwardPass

            activations, z_values = _ForwardPass.forward_mlp(
                X[: min(32, len(X))],
                self.model.weights,
                self.model.biases,
                self.model.hidden_activation,
                self.model.out_activation,
                training=True,
            )

            dW, _ = _BackwardPass.backward_mlp(
                (
                    y[: min(32, len(y))].reshape(-1, 1)
                    if y.ndim == 1
                    else y[: min(32, len(y))]
                ),
                activations,
                z_values,
                self.model.weights,
                self.model.biases,
                X[: min(32, len(X))],
                self.model.hidden_activation,
                self.model.out_activation,
            )

            grad_norms = [np.linalg.norm(dw) for dw in dW]
            if all(norm > 1e-8 for norm in grad_norms):
                feasibility_score += 1
            else:
                issues.append("Vanishing gradients")
            if all(norm < 1e2 for norm in grad_norms):
                feasibility_score += 1
            else:
                issues.append("Exploding gradients")
        except Exception as e:
            issues.append("Gradient computation failed")
        if hasattr(self.model, "lr"):
            lr = self.model.lr
            if 1e-5 <= lr <= 1e-1:
                feasibility_score += 1
            else:
                issues.append("Inappropriate learning rate")
        try:
            initial_loss, _ = self.model.evaluate(
                X[: min(100, len(X))], y[: min(100, len(y))]
            )
            if np.isfinite(initial_loss) and initial_loss > 0:
                feasibility_score += 1
            else:
                issues.append("Invalid loss values")
        except:
            issues.append("Loss computation failed")

        try:
            predictions = self.model.predict(X[: min(10, len(X))])
            if np.all(np.isfinite(predictions)):
                feasibility_score += 1
            else:
                issues.append("Non-finite predictions")
        except:
            issues.append("Forward pass failed")

        capacity_result = self.analyze_capacity_data_ratio(X, y)
        if capacity_result["overfitting_risk"] in ["LOW", "MODERATE"]:
            feasibility_score += 1
        else:
            issues.append("High overfitting risk")

        feasibility_percentage = (feasibility_score / max_score) * 100
        if feasibility_percentage >= 80:
            status = "EXCELLENT"
        elif feasibility_percentage >= 60:
            status = "PASS"
        elif feasibility_percentage >= 40:
            status = "WARN"
        else:
            status = "FAIL"

        return {
            "feasibility_score": feasibility_score,
            "max_score": max_score,
            "feasibility_percentage": feasibility_percentage,
            "issues": issues,
            "status": status,
            "note": self._get_convergence_note(feasibility_percentage, issues),
        }

    def analyze(self, X: np.ndarray, y: np.ndarray) -> None:
        """Comprehensive pre-training analysis with clean tabular output."""
        print("=" * 90)
        print("                         NEUROSCOPE PRE-TRAINING ANALYSIS")
        print("=" * 90)
        tests = [
            ("Initial Loss Check", self.analyze_initial_loss, True),
            ("Initialization Validation", self.analyze_weight_init, False),
            ("Layer Capacity Analysis", self.analyze_layer_capacity, False),
            ("Architecture Sanity Check", self.analyze_architecture_sanity, False),
            ("Capacity vs Data Ratio", self.analyze_capacity_data_ratio, True),
            ("Convergence Feasibility", self.analyze_convergence_feasibility, True),
        ]

        all_results = {}

        # Header
        print(f"{'DIAGNOSTIC TOOL':<27} {'STATUS':<12} {'RESULT':<14} {'NOTE':<42}")
        print("-" * 90)

        for test_name, test_func, needs_data in tests:
            if needs_data:
                result = test_func(X, y)
            else:
                result = test_func()

            all_results[test_name] = result
            status = result.get("status", "UNKNOWN")
            if "initial_loss" in result:
                result_info = f"{result['initial_loss']:.4f}"
            elif "feasibility_percentage" in result:
                result_info = f"{result['feasibility_percentage']:.1f}%"
            elif "total_params" in result:
                result_info = f"{result['total_params']:,} params"
            elif "layers" in result:
                result_info = f"{len(result['layers'])} layers"
            elif "issues" in result and "warnings" in result:
                result_info = f"{len(result['issues'])}I/{len(result['warnings'])}W"
            else:
                result_info = "-"

            note = result.get("note", "-")

            print(f"{test_name:<27} {status:<12} {result_info:<14} {note:<42}")

        print("-" * 90)
        status_counts = {}
        for test_name, result in all_results.items():
            status = result.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        if status_counts.get("FAIL", 0) > 0 or status_counts.get("ERROR", 0) > 0:
            final_status = "CRITICAL ISSUES DETECTED"
        elif status_counts.get("WARN", 0) > 0:
            final_status = "WARNINGS PRESENT"
        else:
            final_status = "ALL SYSTEMS READY"

        pass_count = status_counts.get("PASS", 0) + status_counts.get("EXCELLENT", 0)
        total_tests = len(tests)
        print(f"OVERALL STATUS: {final_status}")
        print(f"TESTS PASSED: {pass_count}/{total_tests}")
        if status_counts.get("WARN", 0) > 0:
            print(f"WARNINGS: {status_counts['WARN']}")
        if status_counts.get("FAIL", 0) > 0:
            print(f"FAILURES: {status_counts['FAIL']}")
        print("=" * 90)
        self.results = all_results
        self.results["overall_status"] = final_status

    # Helper methods
    def _get_loss_note(self, ratio: float, task_type: str) -> str:
        if 0.8 <= ratio <= 1.2:
            return "Perfect loss init"
        elif ratio > 2.0:
            return "Loss too high -check data/arch"
        elif ratio < 0.5:
            return "Loss too low -verify labels"
        else:
            return "Acceptable loss range"

    def _get_init_note(self, status: str) -> str:
        actual_init_method = getattr(self.model, "init_method", "unknown")
        if actual_init_method == "random":
            if "PASS" in status:
                return "Random init detected - consider He/Xavier"
            elif "WARN" in status:
                return "Random init suboptimal"
            else:
                return "Random init inappropriate"
        else:
            if "PASS" in status:
                return "Good weight init"
            elif "WARN" in status:
                return "Consider He/Xavier init"
            else:
                return "Poor init"

    def _get_capacity_note(self, bottlenecks: List) -> str:
        if not bottlenecks:
            return "No bottlenecks"
        severe = sum(1 for b in bottlenecks if b["severity"] == "SEVERE")
        if severe > 0:
            return f"{severe} severe bottlenecks"
        else:
            return "Moderate bottlenecks"

    def _get_architecture_note(self, issues: List, warnings: List) -> str:
        if issues:
            return f"{len(issues)} critical issues"
        elif warnings:
            return f"{len(warnings)} warnings found"
        else:
            return "Architecture is fine"

    def _get_data_ratio_note(
        self, params_per_sample: float, n_samples: int, total_params: int
    ) -> str:
        if params_per_sample < 2.0:
            return "Excellent model size"
        elif params_per_sample < 5.0:
            return "Good model capacity"
        elif params_per_sample < 20.0:
            if n_samples < 500:
                return "Consider more data"
            else:
                return "Use regularization"
        else:
            return "Model too complex"

    def _get_convergence_note(self, percentage: float, issues: List) -> str:
        if percentage >= 80:
            return "Excellent convergence setup"
        elif percentage >= 60:
            return "Good convergence potential"
        elif issues:
            return f"{len(issues)} convergence issues"
        else:
            return "Uncertain convergence"
