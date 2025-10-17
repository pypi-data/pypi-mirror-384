"""
Activation Functions Module
A comprehensive collection of activation functions and their derivatives for neural networks.
"""

import numpy as np


class ActivationFunctions:
    """
    Comprehensive collection of activation functions and their derivatives.

    Provides implementations of popular activation functions used in neural networks,
    including their derivatives for backpropagation. All functions are numerically
    stable and handle edge cases appropriately.
    """

    @staticmethod
    def sigmoid(x):
        """
        Compute sigmoid activation function.

        Applies the logistic sigmoid function that maps input to (0, 1) range.
        Includes numerical clipping to prevent overflow in exponential computation.

        Args:
            x (NDArray[np.float64]): Input array of any shape.

        Returns:
            NDArray[np.float64]: Sigmoid-activated values in range (0, 1).

        Example:
            >>> activated = ActivationFunctions.sigmoid(z)
            >>> # Values are now between 0 and 1
        """
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    @staticmethod
    def sigmoid_derivative(x):
        sig = ActivationFunctions.sigmoid(x)
        return sig * (1 - sig)

    @staticmethod
    def softmax(z):  # Z = (N, C)
        z_shift = z - np.max(z, axis=1, keepdims=True)
        exp_z = np.exp(z_shift)
        return exp_z / np.sum(exp_z, axis=1, keepdims=True)

    @staticmethod
    def tanh(x):
        return np.tanh(x)

    @staticmethod
    def tanh_derivative(z):
        tanh_z = np.tanh(z)
        return 1 - tanh_z * tanh_z

    @staticmethod
    def relu(x):
        """
        Compute ReLU (Rectified Linear Unit) activation.

        Applies the rectified linear activation function that outputs the input
        for positive values and zero for negative values. Most popular activation
        for hidden layers in modern neural networks.

        Args:
            x (NDArray[np.float64]): Input array of any shape.

        Returns:
            NDArray[np.float64]: ReLU-activated values (non-negative).

        Example:
            >>> activated = ActivationFunctions.relu(z)
            >>> # Negative values become 0, positive values unchanged
        """
        return np.maximum(0, x)

    @staticmethod
    def relu_derivative(x):
        return (x > 0).astype(np.float64)

    @staticmethod
    def leaky_relu(x, negative_slope=0.01):
        """
        Compute Leaky ReLU activation function.

        Variant of ReLU that allows small negative values to flow through,
        helping to mitigate the "dying ReLU" problem where neurons can become
        permanently inactive.

        Args:
            x (NDArray[np.float64]): Input array of any shape.
            negative_slope (float, optional): Slope for negative values. Defaults to 0.01.

        Returns:
            NDArray[np.float64]: Leaky ReLU-activated values.

        Example:
            >>> activated = ActivationFunctions.leaky_relu(z, negative_slope=0.01)
            >>> # Positive values unchanged, negative values scaled by 0.01
        """
        return np.where(x > 0, x, negative_slope * x)

    @staticmethod
    def leaky_relu_derivative(x, negative_slope=0.01):
        grad = np.ones_like(x, dtype=np.float64)
        grad[x < 0] = negative_slope
        return grad

    @staticmethod
    def selu(x):
        alpha = 1.6732632423543772848170429916717
        scale = 1.0507009873554804934193349852946
        return scale * np.where(x > 0, x, alpha * (np.exp(x) - 1))

    @staticmethod
    def selu_derivative(x):
        alpha = 1.6732632423543772848170429916717
        scale = 1.0507009873554804934193349852946
        return scale * np.where(x > 0, 1, alpha * np.exp(x))

    @staticmethod
    def inverted_dropout(x, rate=0.5, training=True):
        if not training or rate == 0.0:
            return x
        keep_prob = 1 - rate
        mask = np.random.binomial(1, keep_prob, size=x.shape) / keep_prob
        return x * mask

    @staticmethod
    def alpha_dropout(x, rate=0.5, training=True):
        if not training or rate == 0:
            return x
        alpha = 1.6732632423543772848170429916717
        scale = 1.0507009873554804934193349852946  # lambda
        alpha0 = -scale * alpha
        q = 1 - rate  # Keep probability
        a = (q * (1.0 + rate * (alpha0**2))) ** (-0.5)
        b = -a * (1.0 - q) * alpha0
        x_float = x.astype(np.float32, copy=False)
        mask = np.random.binomial(1, q, size=x.shape).astype(np.float32)
        out = a * (x_float * mask + alpha0 * (1 - mask)) + b
        return out
