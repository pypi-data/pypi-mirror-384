"""
Post-Training Evaluation for NeuroScope MLP Framework
Focused post-training evaluation tools for neural network assessment after training.
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np


class PostTrainingEvaluator:
    """
    Comprehensive post-training evaluation system for neural networks.

    Provides thorough analysis of trained model performance including robustness
    testing, performance metrics evaluation, and diagnostic assessments. Designed
    to validate model quality and identify potential deployment issues after
    training completion.

    Args:
        model: Trained and compiled MLP model instance with initialized weights.

    Attributes:
        model: Reference to the trained neural network model.
        results (dict): Cached evaluation results from various assessments.

    Example:
        >>> from neuroscope.diagnostics import PostTrainingEvaluator
        >>> model = MLP([784, 128, 10])
        >>> model.compile(lr=1e-3)
        >>> history = model.fit(X_train, y_train, epochs=100)
        >>> evaluator = PostTrainingEvaluator(model)
        >>> evaluator.evaluate(X_test, y_test)
        >>> # Access detailed results
        >>> robustness = evaluator.evaluate_robustness(X_test, y_test)
        >>> performance = evaluator.evaluate_performance(X_test, y_test)
    """

    def __init__(self, model):
        """Initialize evaluator with a trained model."""
        if not hasattr(model, "weights") or not hasattr(model, "biases"):
            raise ValueError("Model must be weight initialized.")
        if not getattr(model, "compiled", False):
            raise ValueError("Model must be compiled.")
        self.model = model
        self.results = {}

    def evaluate_robustness(
        self, X: np.ndarray, y: np.ndarray, noise_levels: List[float] = None
    ) -> Dict[str, Any]:
        """Evaluate model robustness against Gaussian noise."""
        if noise_levels is None:
            noise_levels = [0.01, 0.05, 0.1, 0.2]
        try:
            baseline_loss, baseline_accuracy = self.model.evaluate(X, y)
            baseline_predictions = self.model.predict(X)
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "note": "Failed to compute baseline performance",
            }
        robustness_scores = []
        for noise_level in noise_levels:
            try:
                X_noisy = X + np.random.normal(0, noise_level, X.shape)
                noisy_loss, noisy_accuracy = self.model.evaluate(X_noisy, y)
                noisy_predictions = self.model.predict(X_noisy)

                accuracy_drop = baseline_accuracy - noisy_accuracy
                if baseline_predictions.shape[1] > 1:
                    consistency = np.mean(
                        np.argmax(baseline_predictions, axis=1)
                        == np.argmax(noisy_predictions, axis=1)
                    )
                else:
                    consistency = max(
                        0,
                        np.corrcoef(
                            baseline_predictions.flatten(), noisy_predictions.flatten()
                        )[0, 1],
                    )

                accuracy_robustness = max(
                    0, 1 - (accuracy_drop / (baseline_accuracy + 1e-8))
                )
                robustness_scores.append((accuracy_robustness + consistency) / 2)
            except:
                pass
        overall_robustness = np.mean(robustness_scores) if robustness_scores else 0.0

        if overall_robustness >= 0.8:
            status, note = "EXCELLENT", "Highly robust to noise"
        elif overall_robustness >= 0.6:
            status, note = "PASS", "Good noise robustness"
        elif overall_robustness >= 0.4:
            status, note = "WARN", "Moderate robustness"
        else:
            status, note = "FAIL", "Poor noise robustness"

        return {
            "baseline_accuracy": baseline_accuracy,
            "baseline_loss": baseline_loss,
            "overall_robustness": overall_robustness,
            "status": status,
            "note": note,
        }

    def evaluate_performance(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Evaluate model performance metrics."""
        try:
            # Warm up the model with a small prediction to stabilize timing
            if X.shape[0] > 1:
                _ = self.model.predict(X[:1])

            # Take multiple timing measurements for more stable results
            times = []
            for _ in range(3):
                start_time = time.time()
                predictions = self.model.predict(X)
                times.append(time.time() - start_time)

            # Use median time for more robust measurement
            prediction_time = sorted(times)[1]  # median of 3 measurements

            loss, primary_accuracy = self.model.evaluate(X, y)
            # Ensure minimum time to avoid division by zero and unrealistic values
            min_time = 1e-6  # 1 microsecond minimum
            prediction_time = max(prediction_time, min_time)
            samples_per_second = X.shape[0] / prediction_time
            total_params = sum(
                w.size + b.size for w, b in zip(self.model.weights, self.model.biases)
            )

            all_metrics = self._evaluate_all_metrics(X, y, predictions)

            # Status assessment
            if primary_accuracy >= 0.9 and samples_per_second >= 1000:
                status, note = "EXCELLENT", "High accuracy and fast inference"
            elif primary_accuracy >= 0.8:
                status, note = "PASS", "Good overall performance"
            elif primary_accuracy >= 0.6:
                status, note = "WARN", "Moderate performance"
            else:
                status, note = "FAIL", "Poor performance"

            return {
                "accuracy": primary_accuracy,
                "loss": loss,
                "samples_per_second": samples_per_second,
                "total_params": total_params,
                "all_metrics": all_metrics,
                "status": status,
                "note": note,
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "note": "Failed to evaluate performance",
            }

    def _evaluate_all_metrics(
        self, X: np.ndarray, y: np.ndarray, predictions: np.ndarray
    ) -> Dict[str, float]:
        """Evaluate all available metrics from the metrics module."""
        try:
            from neuroscope.mlp.metrics import Metrics
        except ImportError:
            try:
                from ..mlp.metrics import Metrics
            except ImportError as e:
                return {"error": f"Failed to import metrics: {str(e)}"}

        # Determine task type
        is_multiclass = predictions.shape[1] > 1
        is_binary = predictions.shape[1] == 1 and len(np.unique(y)) <= 10
        is_regression = not (is_multiclass or is_binary)

        metrics_results = {}
        try:
            # Regression metrics (for regression and binary classification only)
            if is_regression or is_binary:
                metrics_results.update(
                    {
                        "mse": Metrics.mse(y, predictions),
                        "rmse": Metrics.rmse(y, predictions),
                        "mae": Metrics.mae(y, predictions),
                    }
                )

            # Classification metrics
            if is_binary:
                metrics_results.update(
                    {
                        "accuracy_binary": Metrics.accuracy_binary(y, predictions),
                        "precision": Metrics.precision(y, predictions),
                        "recall": Metrics.recall(y, predictions),
                        "f1_score": Metrics.f1_score(y, predictions),
                    }
                )
            elif is_multiclass:
                metrics_results.update(
                    {
                        "accuracy_multiclass": Metrics.accuracy_multiclass(
                            y, predictions
                        ),
                        "precision": Metrics.precision(y, predictions, average="macro"),
                        "recall": Metrics.recall(y, predictions, average="macro"),
                        "f1_score": Metrics.f1_score(y, predictions, average="macro"),
                    }
                )

            # Regression-specific metrics
            if is_regression:
                metrics_results["r2_score"] = Metrics.r2_score(y, predictions)

        except Exception as e:
            metrics_results["error"] = str(e)

        return metrics_results

    def evaluate_stability(
        self, X: np.ndarray, y: np.ndarray, n_samples: int = 100
    ) -> Dict[str, Any]:
        """Evaluate prediction stability across similar inputs. (K Neighbor Approach)"""
        try:
            if X.shape[0] < 2:
                return {
                    "status": "ERROR",
                    "error": "Insufficient data",
                    "note": "Need at least 2 samples",
                }

            n_test = min(n_samples, X.shape[0])
            test_indices = np.random.choice(X.shape[0], n_test, replace=False)
            stability_scores = []

            for idx in test_indices:
                x_ref = X[idx : idx + 1]
                pred_ref = self.model.predict(x_ref)

                distances = np.linalg.norm(X - x_ref, axis=1)
                distances[idx] = np.inf
                neighbor_idx = np.argmin(distances)

                if distances[neighbor_idx] == np.inf:
                    continue
                pred_neighbor = self.model.predict(X[neighbor_idx : neighbor_idx + 1])

                if pred_ref.shape[1] > 1:
                    stability = (
                        1.0 if np.argmax(pred_ref) == np.argmax(pred_neighbor) else 0.0
                    )
                else:
                    pred_distance = np.abs(
                        pred_ref.flatten()[0] - pred_neighbor.flatten()[0]
                    )
                    output_scale = np.std(y) + 1e-8
                    stability = np.exp(-pred_distance / output_scale)

                stability_scores.append(stability)

            overall_stability = np.mean(stability_scores) if stability_scores else 0.0

            if overall_stability >= 0.8:
                status, note = "EXCELLENT", "Highly stable predictions"
            elif overall_stability >= 0.6:
                status, note = "PASS", "Good prediction stability"
            elif overall_stability >= 0.4:
                status, note = "WARN", "Moderate stability issues"
            else:
                status, note = "FAIL", "Poor prediction stability"

            return {
                "overall_stability": overall_stability,
                "status": status,
                "note": note,
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "note": "Failed to evaluate stability",
            }

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        X_train: Optional[np.ndarray] = None,
        y_train: Optional[np.ndarray] = None,
    ):
        """Run comprehensive model evaluation and generate summary report."""
        print("=" * 80)
        print("                  NEUROSCOPE POST-TRAINING EVALUATION")
        print("=" * 80)

        evaluations = [
            ("Robustness", lambda: self.evaluate_robustness(X_test, y_test)),
            ("Performance", lambda: self.evaluate_performance(X_test, y_test)),
            ("Stability", lambda: self.evaluate_stability(X_test, y_test)),
        ]

        if X_train is not None and y_train is not None:
            evaluations.append(
                (
                    "Generalization",
                    lambda: self.evaluate_generalization(
                        X_train, y_train, X_test, y_test
                    ),
                )
            )

        all_results = {}
        print(f"{'EVALUATION':<15} {'STATUS':<12} {'SCORE':<12} {'NOTE':<45}")
        print("-" * 80)

        for eval_name, eval_func in evaluations:
            try:
                result = eval_func()
                all_results[eval_name] = result
                status = result.get("status", "UNKNOWN")
                note = result.get("note", "-")
                score_keys = [
                    "overall_robustness",
                    "accuracy",
                    "generalization_score",
                    "overall_stability",
                ]
                score = next(
                    (f"{result[key]:.3f}" for key in score_keys if key in result), "N/A"
                )

                print(f"{eval_name:<15} {status:<12} {score:<12} {note:<45}")

            except Exception as e:
                all_results[eval_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "note": "Evaluation failed",
                }
                print(
                    f"{eval_name:<15} {'ERROR':<12} {'N/A':<12} {'Evaluation failed':<45}"
                )

        print("-" * 80)
        status_counts = {}
        for result in all_results.values():
            status = result.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts.get("ERROR", 0) > 0:
            overall_status = "EVALUATION ERRORS"
        elif status_counts.get("FAIL", 0) > 0:
            overall_status = "ISSUES DETECTED"
        elif status_counts.get("WARN", 0) > 0:
            overall_status = "WARNINGS PRESENT"
        else:
            overall_status = "EVALUATION COMPLETE"

        pass_count = status_counts.get("PASS", 0) + status_counts.get("EXCELLENT", 0)
        print(f"OVERALL STATUS: {overall_status}")
        print(f"EVALUATIONS PASSED: {pass_count}/{len(evaluations)}")
        if (
            "Performance" in all_results
            and all_results["Performance"].get("status") != "ERROR"
        ):
            self._display_metrics_evaluation(all_results["Performance"])
        print("=" * 80)
        self.results = all_results

    def _display_metrics_evaluation(self, performance_result: Dict[str, Any]):
        """Display metrics evaluation in a structured table format."""
        all_metrics = performance_result.get("all_metrics", {})
        if not all_metrics or "error" in all_metrics:
            return

        is_classification = any(
            metric in all_metrics
            for metric in [
                "accuracy_binary",
                "accuracy_multiclass",
                "precision",
                "recall",
                "f1_score",
            ]
        )
        task_type = "CLASSIFICATION" if is_classification else "REGRESSION"

        print("=" * 80)
        print(f"                     {task_type} METRICS")
        print("=" * 80)

        if is_classification:
            metric_order = [
                ("accuracy_binary", "Accuracy"),
                ("accuracy_multiclass", "Accuracy"),
                ("precision", "Precision"),
                ("recall", "Recall"),
                ("f1_score", "F1-Score"),
            ]

            def get_status(key, value):
                return (
                    ("EXCELLENT", "Outstanding performance")
                    if value >= 0.95
                    else (
                        ("PASS", "Good performance")
                        if value >= 0.85
                        else (
                            ("WARN", "Moderate performance")
                            if value >= 0.70
                            else ("FAIL", "Poor performance")
                        )
                    )
                )

        else:
            metric_order = [
                ("r2_score", "R² Score"),
                ("mae", "Mean Absolute Error"),
                ("mse", "Mean Squared Error"),
                ("rmse", "Root Mean Squared Error"),
            ]

            def get_status(key, value):
                if key == "r2_score":
                    return (
                        ("EXCELLENT", "Outstanding fit")
                        if value >= 0.9
                        else (
                            ("PASS", "Good fit")
                            if value >= 0.7
                            else (
                                ("WARN", "Moderate fit")
                                if value >= 0.5
                                else ("FAIL", "Poor fit")
                            )
                        )
                    )
                else:
                    return (
                        ("EXCELLENT", "Very low error")
                        if value <= 0.1
                        else (
                            ("PASS", "Low error")
                            if value <= 0.3
                            else (
                                ("WARN", "Moderate error")
                                if value <= 0.5
                                else ("FAIL", "High error")
                            )
                        )
                    )

        metrics_to_display = []
        for metric_key, display_name in metric_order:
            if metric_key in all_metrics and isinstance(
                all_metrics[metric_key], (int, float)
            ):
                value = all_metrics[metric_key]
                status, note = get_status(metric_key, value)
                metrics_to_display.append((display_name, status, value, note))

        print(f"{'METRIC':<20} {'STATUS':<12} {'SCORE':<12} {'NOTE':<40}")
        print("-" * 80)

        for metric_name, status, value, note in metrics_to_display:
            score_str = f"{value:.4f}"
            print(f"{metric_name:<20} {status:<12} {score_str:<12} {note:<40}")

        print("-" * 80)
        status_counts = {}
        for _, status, _, _ in metrics_to_display:
            status_counts[status] = status_counts.get(status, 0) + 1

        metrics_pass_count = status_counts.get("PASS", 0) + status_counts.get(
            "EXCELLENT", 0
        )
        total_metrics = len(metrics_to_display)

        metrics_overall = (
            "METRICS ISSUES DETECTED"
            if status_counts.get("FAIL", 0) > 0
            else (
                "SOME METRICS WARNINGS"
                if status_counts.get("WARN", 0) > 0
                else "METRICS EVALUATION COMPLETE"
            )
        )

        print(f"METRICS STATUS: {metrics_overall}")
        print(f"METRICS PASSED: {metrics_pass_count}/{total_metrics}")
