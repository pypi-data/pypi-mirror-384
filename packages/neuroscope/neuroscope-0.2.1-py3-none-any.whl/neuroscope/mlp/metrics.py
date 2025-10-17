"""
Metrics Module
Comprehensive evaluation metrics for regression and classification tasks.
"""

import numpy as np


class Metrics:
    """
    Comprehensive collection of evaluation metrics for neural networks.

    Provides implementations of standard metrics for both regression and
    classification tasks. All metrics handle edge cases and provide
    meaningful results for model evaluation.
    """

    @staticmethod
    def accuracy_multiclass(y_true, y_pred):
        """
        Compute multi-class classification accuracy.

        Calculates the fraction of correctly predicted samples for multi-class
        classification problems. Handles both sparse labels and one-hot encoded inputs.

        Args:
            y_true (NDArray[np.float64]): True class labels of shape (N,) for sparse labels
                or (N, C) for one-hot encoded.
            y_pred (NDArray[np.float64]): Predicted class probabilities of shape (N, C).

        Returns:
            float: Classification accuracy as a fraction (0.0 to 1.0).

        Example:
            >>> accuracy = Metrics.accuracy_multiclass(y_true, y_pred)
            >>> print(f"Accuracy: {accuracy:.2%}")
        """
        # y_pred: (N, C), y_true: (N,) or (N, C)
        pred_classes = np.argmax(y_pred, axis=1)
        if y_true.ndim == 1:
            true_classes = y_true
        else:
            true_classes = np.argmax(y_true, axis=1)
        return float(np.mean(pred_classes == true_classes))

    @staticmethod
    def accuracy_binary(y_true, y_pred, thresh=0.5):
        """
        Compute binary classification accuracy.

        Calculates the fraction of correctly predicted samples for binary
        classification by applying a threshold to predicted probabilities.

        Args:
            y_true (NDArray[np.float64]): Binary labels (0/1) of shape (N,) or (N, 1).
            y_pred (NDArray[np.float64]): Predicted probabilities of shape (N,) or (N, 1).
            thresh (float, optional): Classification threshold. Defaults to 0.5.

        Returns:
            float: Binary classification accuracy as a fraction (0.0 to 1.0).

        Example:
            >>> accuracy = Metrics.accuracy_binary(y_true, y_pred, thresh=0.5)
            >>> print(f"Binary Accuracy: {accuracy:.2%}")
        """
        # y_pred: (N, C), y_true: (N,) or (N, C)
        preds = (y_pred >= thresh).astype(int)
        y_true = y_true.reshape(preds.shape)
        return float(np.mean(preds == y_true))

    @staticmethod
    def mse(y_true, y_pred):
        """
        Compute mean squared error metric.

        Calculates the average squared differences between predicted and true values.
        Commonly used metric for regression problems.

        Args:
            y_true (NDArray[np.float64]): Ground truth values of shape (N,) or (N, 1).
            y_pred (NDArray[np.float64]): Predicted values of shape (N,) or (N, 1).

        Returns:
            float: Mean squared error (scalar).

        Example:
            >>> mse_score = Metrics.mse(y_true, y_pred)
            >>> print(f"MSE: {mse_score:.4f}")
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        return float(np.mean((y_true - y_pred) ** 2))

    @staticmethod
    def rmse(y_true, y_pred):
        return float(np.sqrt(Metrics.mse(y_true, y_pred)))

    @staticmethod
    def mae(y_true, y_pred):
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        return float(np.mean(np.abs(y_true - y_pred)))

    @staticmethod
    def r2_score(y_true, y_pred):
        """
        Compute coefficient of determination (R² score).

        Measures the proportion of variance in the dependent variable that is
        predictable from the independent variables. R² = 1 indicates perfect fit,
        R² = 0 indicates the model performs as well as predicting the mean.

        Args:
            y_true (NDArray[np.float64]): Ground truth values of shape (N,) or (N, 1).
            y_pred (NDArray[np.float64]): Predicted values of shape (N,) or (N, 1).

        Returns:
            float: R² score (can be negative for very poor fits).

        Example:
            >>> r2 = Metrics.r2_score(y_true, y_pred)
            >>> print(f"R² Score: {r2:.3f}")
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        return float(1.0 - (ss_res / ss_tot))

    @staticmethod
    def _get_classification_data(y_true, y_pred, threshold=0.5):
        """
        Convert predictions to class arrays and compute confusion matrix elements.

        Returns:
            tuple: (y_true_classes, y_pred_classes, num_classes, tp, fp, fn)
        """
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)

        if y_pred.ndim == 1 or (y_pred.ndim == 2 and y_pred.shape[1] == 1):
            # Binary classification
            y_pred_classes = (y_pred.flatten() >= threshold).astype(int)
            y_true_classes = y_true.flatten().astype(int)
            num_classes = 2
        else:
            # Multi-class classification
            y_pred_classes = np.argmax(y_pred, axis=1)
            if y_true.ndim == 1:
                y_true_classes = y_true.astype(int)
            else:
                y_true_classes = np.argmax(y_true, axis=1)
            num_classes = max(np.max(y_true_classes), np.max(y_pred_classes)) + 1

        # Compute confusion matrix elements for all classes at once
        tp = np.zeros(num_classes)
        fp = np.zeros(num_classes)
        fn = np.zeros(num_classes)

        for i in range(num_classes):
            tp[i] = np.sum((y_true_classes == i) & (y_pred_classes == i))
            fp[i] = np.sum((y_true_classes != i) & (y_pred_classes == i))
            fn[i] = np.sum((y_true_classes == i) & (y_pred_classes != i))

        return y_true_classes, y_pred_classes, num_classes, tp, fp, fn

    @staticmethod
    def _apply_averaging(scores, y_true_classes, num_classes, average):
        """Apply averaging strategy to per-class scores."""
        if average == "macro":
            return float(np.mean(scores))
        elif average == "weighted":
            support = np.array(
                [np.sum(y_true_classes == i) for i in range(num_classes)]
            )
            total_support = np.sum(support)
            if total_support == 0:
                return 0.0
            weights = support / total_support
            return float(np.sum(scores * weights))
        else:
            return scores

    @staticmethod
    def precision(y_true, y_pred, average="weighted", threshold=0.5):
        """
        Compute precision score: TP / (TP + FP)

        Args:
            y_true: True labels
            y_pred: Predicted probabilities or labels
            average: 'macro', 'weighted', or None for per-class scores
            threshold: Decision threshold for binary classification
        """
        y_true_classes, y_pred_classes, num_classes, tp, fp, fn = (
            Metrics._get_classification_data(y_true, y_pred, threshold)
        )

        precision_scores = np.zeros(num_classes)
        for i in range(num_classes):
            precision_scores[i] = (
                tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) > 0 else 0.0
            )

        return Metrics._apply_averaging(
            precision_scores, y_true_classes, num_classes, average
        )

    @staticmethod
    def recall(y_true, y_pred, average="weighted", threshold=0.5):
        """
        Compute recall score: TP / (TP + FN)

        Args:
            y_true: True labels
            y_pred: Predicted probabilities or labels
            average: 'macro', 'weighted', or None for per-class scores
            threshold: Decision threshold for binary classification
        """
        y_true_classes, y_pred_classes, num_classes, tp, fp, fn = (
            Metrics._get_classification_data(y_true, y_pred, threshold)
        )

        recall_scores = np.zeros(num_classes)
        for i in range(num_classes):
            recall_scores[i] = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) > 0 else 0.0

        return Metrics._apply_averaging(
            recall_scores, y_true_classes, num_classes, average
        )

    @staticmethod
    def f1_score(y_true, y_pred, average="weighted", threshold=0.5):
        """
        Compute F1 score: 2 * (Precision * Recall) / (Precision + Recall)

        Args:
            y_true: True labels
            y_pred: Predicted probabilities or labels
            average: 'macro', 'weighted', or None for per-class scores
            threshold: Decision threshold for binary classification
        """
        y_true_classes, y_pred_classes, num_classes, tp, fp, fn = (
            Metrics._get_classification_data(y_true, y_pred, threshold)
        )

        f1_scores = np.zeros(num_classes)
        for i in range(num_classes):
            precision_i = tp[i] / (tp[i] + fp[i]) if (tp[i] + fp[i]) > 0 else 0.0
            recall_i = tp[i] / (tp[i] + fn[i]) if (tp[i] + fn[i]) > 0 else 0.0
            f1_scores[i] = (
                2 * precision_i * recall_i / (precision_i + recall_i)
                if (precision_i + recall_i) > 0
                else 0.0
            )

        return Metrics._apply_averaging(f1_scores, y_true_classes, num_classes, average)
