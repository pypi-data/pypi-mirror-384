"""
Weight Initialization Module
Professional weight initialization strategies for neural networks.
"""

import numpy as np


class WeightInits:
    """
    Research-validated weight initialization strategies for neural networks.

    Provides implementations of modern weight initialization methods that
    help maintain proper gradient flow and accelerate training convergence.
    All methods follow established theoretical foundations from deep learning
    research.
    """

    @staticmethod
    def he_init(layer_dims: list, seed=42):
        """
        He initialization for ReLU and ReLU-variant activations.

        Optimal for ReLU-based networks as derived in He et al. (2015).
        Uses standard deviation of sqrt(2/fan_in) to maintain proper
        variance propagation through ReLU activations.

        Args:
            layer_dims (list[int]): Layer dimensions [input_dim, hidden_dim, ..., output_dim].
            seed (int, optional): Random seed for reproducibility. Defaults to 42.

        Returns:
            tuple[list, list]: (weights, biases) where weights are initialized
                according to He initialization and biases are zero-initialized.

        Note:
            Based on "Delving Deep into Rectifiers: Surpassing Human-Level
            Performance on ImageNet Classification" (He et al. 2015).

        Example:
            >>> weights, biases = WeightInits.he_init([784, 128, 10])
        """
        np.random.seed(seed)
        weights = (
            []
        )  # [(inputxhidden), (hiddenxhidden), (hiddenxhidden),...,(hidden, out)]
        biases = []  # [(1, hidden), (1, hidden),...,(1, out)]
        for i in range(len(layer_dims) - 1):
            fan_in = layer_dims[i]
            fan_out = layer_dims[i + 1]
            # Weight matrix: (fan_in, fan_out)
            W = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)
            weights.append(W)
            # Bias vector: (1, fan_out)
            b = np.zeros((1, fan_out), dtype=np.float64)
            biases.append(b)
        return weights, biases

    @staticmethod
    def xavier_init(layer_dims: list, seed=42):
        """
        Xavier/Glorot initialization for sigmoid and tanh activations.

        Optimal for symmetric activations like tanh and sigmoid. Uses
        standard deviation of sqrt(2/(fan_in + fan_out)) to maintain
        constant variance across layers.

        Args:
            layer_dims (list[int]): Layer dimensions [input_dim, hidden_dim, ..., output_dim].
            seed (int, optional): Random seed for reproducibility. Defaults to 42.

        Returns:
            tuple[list, list]: (weights, biases) with Xavier-initialized weights and zero biases.

        Note:
            Based on "Understanding the difficulty of training deep feedforward
            neural networks" (Glorot & Bengio 2010).

        Example:
            >>> weights, biases = WeightInits.xavier_init([784, 128, 10])
        """
        np.random.seed(seed)
        weights = []
        biases = []
        for i in range(len(layer_dims) - 1):
            fan_in = layer_dims[i]
            fan_out = layer_dims[i + 1]
            xavier_std = np.sqrt(2.0 / (fan_in + fan_out))
            W = np.random.randn(fan_in, fan_out) * xavier_std
            weights.append(W)
            b = np.zeros((1, fan_out), dtype=np.float64)
            biases.append(b)
        return weights, biases

    @staticmethod
    def random_init(layer_dims: list, scale=0.01, seed=42):
        np.random.seed(seed)
        weights = []
        biases = []
        for i in range(len(layer_dims) - 1):
            fan_in = layer_dims[i]
            fan_out = layer_dims[i + 1]
            W = np.random.randn(fan_in, fan_out) * scale
            weights.append(W)
            b = np.random.randn(1, fan_out) * (scale * 0.1)
            biases.append(b)
        return weights, biases

    @staticmethod
    def selu_init(layer_dims: list, seed=42):
        np.random.seed(seed)
        weights = []
        biases = []
        for i in range(len(layer_dims) - 1):
            fan_in = layer_dims[i]
            fan_out = layer_dims[i + 1]
            W = np.random.randn(fan_in, fan_out) / np.sqrt(fan_in)
            weights.append(W)
            b = np.zeros((1, fan_out), dtype=np.float64)
            biases.append(b)
        return weights, biases

    @staticmethod
    def smart_init(layer_dims: list, hidden_activation="leaky_relu", seed=42):
        """
        Intelligent initialization selection based on activation function.

        Automatically selects the optimal initialization strategy based on
        the chosen activation function. Combines research-validated best
        practices to ensure proper gradient flow from the start of training.

        Args:
            layer_dims (list[int]): Layer dimensions [input_dim, hidden_dim, ..., output_dim].
            hidden_activation (str, optional): Hidden layer activation function. Defaults to 'leaky_relu'.
            seed (int, optional): Random seed for reproducibility. Defaults to 42.

        Returns:
            tuple[list, list]: (weights, biases) with optimally initialized weights for the activation.

        Initialization Strategy:
            - ReLU/Leaky ReLU: He initialization
            - Tanh/Sigmoid: Xavier initialization
            - SELU: LeCun initialization
            - Unknown: Xavier initialization (safe default)

        Example:
            >>> weights, biases = WeightInits.smart_init([784, 128, 10], 'relu')
        """
        if hidden_activation.lower() in ["relu", "leaky_relu"]:
            return WeightInits.he_init(layer_dims, seed)
        elif hidden_activation.lower() in ["tanh", "sigmoid"]:
            return WeightInits.xavier_init(layer_dims, seed)
        elif hidden_activation.lower() == "selu":
            return WeightInits.selu_init(layer_dims, seed)
        else:
            return WeightInits.xavier_init(layer_dims, seed)
