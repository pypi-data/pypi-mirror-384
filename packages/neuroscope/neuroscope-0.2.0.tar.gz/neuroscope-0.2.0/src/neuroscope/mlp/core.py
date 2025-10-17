"""
Core Neural Network Operations
Internal forward and backward propagation implementations.
"""

import time
from collections import Counter, defaultdict

import numpy as np

from .activations import ActivationFunctions
from .utils import Utils


class _ForwardPass:
    """
    Internal class for forward propagation operations.

    Implements efficient forward pass through multi-layer perceptrons with
    support for various activation functions, dropout, and numerical stability.
    This class is part of the internal API and should not be used directly.
    """

    @staticmethod
    def forward_mlp(
        X,
        weights: list,
        biases: list,
        hidden_activation=None,
        out_activation=None,
        dropout_rate=0.0,
        dropout_type="normal",
        training=True,
    ):
        """
        Perform forward propagation through the entire network.

        Executes the forward pass by computing linear transformations followed by
        activation functions for each layer. Supports dropout during training
        and handles different activation functions for hidden and output layers.

        Args:
            X (NDArray[np.float64]): Input data of shape (N, input_dim).
            weights (list[NDArray[np.float64]]): Weight matrices for each layer.
            biases (list[NDArray[np.float64]]): Bias vectors for each layer.
            hidden_activation (str, optional): Activation function for hidden layers.
            out_activation (str, optional): Activation function for output layer.
            dropout_rate (float, optional): Dropout probability. Defaults to 0.0.
            dropout_type (str, optional): Dropout variant. Defaults to 'normal'.
            training (bool, optional): Whether in training mode. Defaults to True.

        Returns:
            tuple: (activations, z_values) where activations contains the output
                   of each layer and z_values contains pre-activation values.
        """
        # X = input(X_train/X_test) --> (N, input_dim)
        # weights = [(inputxhidden), (hiddenxhidden), (hiddenxhidden),...,(hidden, out)] for N layers
        # biases = [(1, hidden), (1, hidden),...,(1, out)] for N layers
        z_values = (
            []
        )  # [(N, hidden_dim), (N, hidden_dim),...,(N, hidden_dim)] for all Layers
        activations = (
            []
        )  # [(N, hidden_dim), (N, hidden_dim),...,(N, hidden_dim)] for all Layers
        # First layer: input to first hidden
        A = X
        L = len(weights)

        for i in range(L):
            # Linear transformation: Z = X @ W + b
            Z = A @ weights[i] + biases[i]  # (N, fan_out)
            z_values.append(Z)

            # Apply activation function
            if i == L - 1:  # Output layer
                if out_activation is None:
                    A = Z
                elif out_activation == "sigmoid":
                    A = ActivationFunctions.sigmoid(Z)
                elif out_activation == "softmax":
                    A = ActivationFunctions.softmax(Z)
                else:
                    raise ValueError(
                        f"Unknown output activation function: {out_activation}"
                    )

            else:  # Hidden layers
                if hidden_activation is None:
                    A = Z
                elif hidden_activation == "leaky_relu":
                    A = ActivationFunctions.leaky_relu(Z)
                elif hidden_activation == "relu":
                    A = ActivationFunctions.relu(Z)
                elif hidden_activation == "sigmoid":
                    A = ActivationFunctions.sigmoid(Z)
                elif hidden_activation == "tanh":
                    A = ActivationFunctions.tanh(Z)
                elif hidden_activation == "selu":
                    A = ActivationFunctions.selu(Z)
                else:
                    raise ValueError(
                        f"Unknown activation function: {hidden_activation}"
                    )

                # Apply dropout to hidden layers (not output layer)
                if dropout_rate > 0 and training:
                    if dropout_type == "normal":
                        A = ActivationFunctions.inverted_dropout(
                            A, dropout_rate, training
                        )
                    elif dropout_type == "alpha":
                        A = ActivationFunctions.alpha_dropout(A, dropout_rate, training)
                    else:
                        raise ValueError(f"Unknown dropout type: {dropout_type}")

            activations.append(A)

        return activations, z_values


class _BackwardPass:
    """
    Internal class for backward propagation operations.

    Implements efficient backpropagation algorithm for computing gradients
    with respect to weights and biases. Includes numerical stability checks
    and handles various activation functions. This class is part of the
    internal API and should not be used directly.
    """

    _warning_counts = Counter()
    _last_warning_time = defaultdict(float)
    _max_warnings_per_type = 3
    _warning_cooldown = 30.0

    @classmethod
    def _print_throttled_warning(cls, warning_type: str, message: str):
        """
        Print warning with throttling to prevent spam.

        Args:
            warning_type: Unique identifier for the warning type
            message: Warning message to print
        """
        current_time = time.time()

        # Check if we've exceeded max warnings for this type
        if cls._warning_counts[warning_type] >= cls._max_warnings_per_type:
            return

        # Check if enough time has passed since last warning of this type
        if (
            current_time - cls._last_warning_time[warning_type]
        ) < cls._warning_cooldown:
            return

        # Print the warning and update counters
        print(message)
        cls._warning_counts[warning_type] += 1
        cls._last_warning_time[warning_type] = current_time

        # If this is the last warning for this type, inform user
        if cls._warning_counts[warning_type] >= cls._max_warnings_per_type:
            print(
                f"(Further {warning_type!r} warnings will be suppressed for this training session)"
            )

    @classmethod
    def reset_warning_throttling(cls):
        """Reset warning counters (useful for new training sessions)."""
        cls._warning_counts.clear()
        cls._last_warning_time.clear()

    @staticmethod
    def backward_mlp(
        y_true,
        activations,
        z_values,
        weights,
        biases,
        X,
        hidden_activation=None,
        out_activation=None,
    ):
        """
        Perform backward propagation to compute gradients.

        Implements the backpropagation algorithm to compute gradients of the loss
        function with respect to all weights and biases in the network. Uses
        chain rule to efficiently propagate errors backwards through layers.

        Args:
            y_true (NDArray[np.float64]): Ground truth labels of shape (N,) or (N, output_dim).
            activations (list[NDArray[np.float64]]): Forward pass activations for each layer.
            z_values (list[NDArray[np.float64]]): Pre-activation values for each layer.
            weights (list[NDArray[np.float64]]): Weight matrices for each layer.
            biases (list[NDArray[np.float64]]): Bias vectors for each layer.
            X (NDArray[np.float64]): Input data of shape (N, input_dim).
            hidden_activation (str, optional): Hidden layer activation function.
            out_activation (str, optional): Output layer activation function.

        Returns:
            tuple: (dW, db) where dW contains weight gradients and db contains bias gradients.

        Raises:
            ValueError: If activation function is not supported.
            RuntimeError: If gradient computation fails due to numerical issues.
        """

        # Input validation
        X = Utils.validate_array_input(X, "X", min_dims=2, max_dims=2)
        y_true = Utils.validate_array_input(y_true, "y_true", min_dims=1, max_dims=2)

        N = X.shape[0]
        L = len(weights)
        out_dim = weights[-1].shape[1]

        y_true = np.asarray(y_true)
        if y_true.ndim == 1:
            y_true = y_true.reshape(-1, 1)
        if y_true.shape[1] != out_dim:
            if out_dim == 1:
                # Binary classification
                y_true = y_true.reshape(N, 1)
            else:
                # Multi-class
                if y_true.shape[1] == 1 and out_dim > 1:
                    y_true_onehot = np.eye(out_dim)[y_true.flatten()]
                    y_true = y_true_onehot
                else:
                    raise ValueError(
                        f"y_true shape {y_true.shape} incompatible with output dim {out_dim}"
                    )

        dW = [np.zeros_like(W) for W in weights]
        db = [np.zeros_like(b) for b in biases]
        AL = activations[-1]  # Y_pred : Activation of last layer (N, out_dim)

        if np.any(np.isnan(AL)) or np.any(np.isinf(AL)):
            raise RuntimeError(
                "Model outputs contain NaN or Inf values. Training failed - check your data and learning rate."
            )

        if out_activation is None:
            dZ = (AL - y_true) / N
        elif out_activation in ("sigmoid", "softmax"):
            dZ = (AL - y_true) / N  # (N, out_dim)
        else:
            raise ValueError("Unsupported final_activation for simplified derivative")

        for layer in range(L - 1, -1, -1):
            try:
                if layer == 0:
                    A_prev = X
                else:
                    A_prev = activations[
                        layer - 1
                    ]  # [A1, A2, ..., AL] , each(N, fan_in)
                dW[layer] = (
                    A_prev.T @ dZ
                )  # (fan_in, N) @ (N, fan_out) -> (fan_in, fan_out)
                db[layer] = np.sum(dZ, axis=0, keepdims=True)
            except Exception as e:
                raise RuntimeError(f"Error computing gradients for layer {layer}: {e}")

            if layer > 0:
                dA_prev = dZ @ weights[layer].T  # (N, fan_in_prev)
                Z_prev = z_values[layer - 1]  # Z_{l}
                if hidden_activation is None:
                    dZ = dA_prev
                elif hidden_activation == "leaky_relu":
                    dZ = dA_prev * ActivationFunctions.leaky_relu_derivative(Z_prev)
                elif hidden_activation == "relu":
                    dZ = dA_prev * ActivationFunctions.relu_derivative(Z_prev)
                elif hidden_activation == "tanh":
                    dZ = dA_prev * ActivationFunctions.tanh_derivative(Z_prev)
                elif hidden_activation == "sigmoid":
                    dZ = dA_prev * ActivationFunctions.sigmoid_derivative(Z_prev)
                elif hidden_activation == "selu":
                    dZ = dA_prev * ActivationFunctions.selu_derivative(Z_prev)
                else:
                    raise ValueError("Unknown hidden_activation: " + hidden_activation)

        return dW, db
