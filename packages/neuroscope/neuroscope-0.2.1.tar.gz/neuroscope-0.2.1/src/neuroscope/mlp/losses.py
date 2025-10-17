"""
Loss Functions Module
Collection of loss functions for different machine learning tasks.
"""

import numpy as np


class LossFunctions:
    """
    Collection of loss functions for neural network training.

    Provides implementations of common loss functions used in regression and
    classification tasks, with support for L2 regularization. All functions
    handle numerical stability and edge cases appropriately.
    """

    @staticmethod
    def mse(y_true, y_pred):
        """
        Compute mean squared error loss.

        Standard regression loss function that penalizes squared differences
        between predictions and targets. Suitable for continuous target values.

        Args:
            y_true (NDArray[np.float64]): Ground truth values of shape (N,) or (N, 1).
            y_pred (NDArray[np.float64]): Predicted values of shape (N,) or (N, 1).

        Returns:
            float: Mean squared error loss (scalar).

        Example:
            >>> loss = LossFunctions.mse(y_true, y_pred)
            >>> print(f"MSE Loss: {loss:.4f}")
        """
        y_true = np.asarray(y_true).flatten()
        y_pred = np.asarray(y_pred).flatten()
        return float(np.mean((y_true - y_pred) ** 2))

    @staticmethod
    def bce(y_true, y_pred, eps=1e-12):
        """
        Compute binary cross-entropy loss.

        Standard loss function for binary classification problems. Applies
        numerical clipping to prevent log(0) errors and ensure stability.

        Args:
            y_true (NDArray[np.float64]): Binary labels (0/1) of shape (N,).
            y_pred (NDArray[np.float64]): Predicted probabilities of shape (N,).
            eps (float, optional): Small value for numerical stability. Defaults to 1e-12.

        Returns:
            float: Binary cross-entropy loss (scalar).

        Example:
            >>> loss = LossFunctions.bce(y_true, y_pred)
            >>> print(f"BCE Loss: {loss:.4f}")
        """
        y_pred = np.clip(np.asarray(y_pred).reshape(-1), eps, 1 - eps)  # shape (N,)
        y_true = np.asarray(y_true).reshape(-1)  # shape (N,)
        loss = -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        return loss

    @staticmethod
    def bce_with_reg(y_true, y_pred, weights, lamda=0.01, eps=1e-12):
        y_pred = np.clip(np.asarray(y_pred).reshape(-1), eps, 1 - eps)
        y_true = np.asarray(y_true).reshape(-1)
        N = y_true.shape[0]
        bce_loss = LossFunctions.bce(y_true, y_pred, eps)
        l2_penalty = 0
        for W in weights:
            l2_penalty += np.sum(W**2)
        l2_penalty = (lamda / (2.0 * N)) * l2_penalty
        loss = bce_loss + l2_penalty
        return loss

    @staticmethod
    def cce(y_true, y_pred, eps=1e-12):
        """
        Compute categorical cross-entropy loss.

        Standard loss function for multi-class classification. Handles both
        sparse labels (class indices) and one-hot encoded targets.

        Args:
            y_true (NDArray[np.float64]): Class labels of shape (N,) for sparse labels
                or (N, C) for one-hot encoded targets.
            y_pred (NDArray[np.float64]): Predicted class probabilities of shape (N, C).
            eps (float, optional): Small value for numerical stability. Defaults to 1e-12.

        Returns:
            float: Categorical cross-entropy loss (scalar).

        Example:
            >>> loss = LossFunctions.cce(y_true, y_pred)
            >>> print(f"CCE Loss: {loss:.4f}")
        """
        # y_pred: (N, C), y_true: (N,) or (N, C)
        y_pred = np.clip(y_pred, eps, 1 - eps)
        if y_true.ndim == 1:
            num_classes = y_pred.shape[1]
            y_true_onehot = np.eye(num_classes)[y_true]
        else:
            y_true_onehot = y_true
        return -np.sum(y_true_onehot * np.log(y_pred)) / y_pred.shape[0]

    @staticmethod
    def cce_with_reg(y_true, y_pred, weights, lamda=0.01, eps=1e-12):
        # y_pred: (N, C), y_true: (N,) or (N, C)
        N = y_pred.shape[0]
        ce_loss = LossFunctions.cce(y_true, y_pred, eps)
        l2_penalty = 0
        for W in weights:
            l2_penalty += np.sum(W**2)
        l2_penalty = (lamda / (2.0 * N)) * l2_penalty
        return ce_loss + l2_penalty

    @staticmethod
    def mse_with_reg(y_true, y_pred, weights, lamda=0.01):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        N = y_true.shape[0]
        loss = LossFunctions.mse(y_true, y_pred)
        l2_penalty = 0
        for W in weights:
            l2_penalty += np.sum(W**2)
        l2_penalty = (lamda / (2.0 * N)) * l2_penalty
        return loss + l2_penalty
