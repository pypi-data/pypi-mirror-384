"""
Optimizers for NeuroScope MLP.

"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import numpy as np


class Optimizer(ABC):
    """
    Base class for all optimizers.

    Provides common interface for parameter updates and state management.
    """

    def __init__(self, learning_rate: float = 0.01):
        """
        Initialize optimizer.

        Args:
            learning_rate: Step size for parameter updates
        """
        if learning_rate <= 0:
            raise ValueError(f"Learning rate must be positive, got {learning_rate}")

        self.learning_rate = learning_rate
        self._state: Dict[str, Any] = {}

    @abstractmethod
    def update(
        self,
        weights: List[np.ndarray],
        biases: List[np.ndarray],
        weight_grads: List[np.ndarray],
        bias_grads: List[np.ndarray],
    ) -> None:
        """
        Update parameters using gradients.

        Args:
            weights: List of weight matrices
            biases: List of bias vectors
            weight_grads: Gradients for weights
            bias_grads: Gradients for biases
        """
        pass

    def state_dict(self) -> Dict[str, Any]:
        """
        Get optimizer state for checkpointing.

        Returns:
            Dictionary containing optimizer configuration and state
        """
        return {
            "type": self.__class__.__name__,
            "learning_rate": self.learning_rate,
            "state": self._state,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """
        Load optimizer state from checkpoint.

        Args:
            state_dict: State dictionary from state_dict()
        """
        self.learning_rate = state_dict["learning_rate"]
        self._state = state_dict["state"]


class SGD(Optimizer):
    """
    Stochastic Gradient Descent optimizer.

    Implements basic gradient descent with fixed learning rate:
        θ_t = θ_{t-1} - α * ∇L(θ_{t-1})

    Args:
        learning_rate: Learning rate (step size), default: 0.01

    References:
        Robbins & Monro (1951). "A Stochastic Approximation Method."
        Annals of Mathematical Statistics.

    Example:
        >>> from neuroscope import MLP
        >>> model = MLP([10, 20, 5])
        >>> model.compile(optimizer="sgd", lr=0.01)
        >>> history = model.fit(X_train, y_train, epochs=100)
    """

    def __init__(self, learning_rate: float = 0.01):
        super().__init__(learning_rate)

    def update(
        self,
        weights: List[np.ndarray],
        biases: List[np.ndarray],
        weight_grads: List[np.ndarray],
        bias_grads: List[np.ndarray],
    ) -> None:
        """Apply gradient descent update."""
        for i in range(len(weights)):
            weights[i] -= self.learning_rate * weight_grads[i]
            biases[i] -= self.learning_rate * bias_grads[i]


class SGDMomentum(Optimizer):
    """
    SGD with Momentum optimizer.

    Implements momentum-accelerated gradient descent. Momentum accumulates
    gradients over time, allowing faster convergence and reduced oscillation.

    Standard Momentum (Polyak, 1964):
        v_t = μ * v_{t-1} + ∇L(θ_{t-1})
        θ_t = θ_{t-1} - α * v_t

    Nesterov Momentum (Nesterov, 1983):
        v_t = μ * v_{t-1} + ∇L(θ_{t-1})
        θ_t = θ_{t-1} - α * (μ * v_t + ∇L(θ_{t-1}))

    Args:
        learning_rate: Learning rate (step size), default: 0.01
        momentum: Momentum coefficient μ ∈ [0, 1), default: 0.9
        nesterov: Enable Nesterov accelerated gradient, default: False

    References:
        - Polyak, B. T. (1964). "Some methods of speeding up the convergence
          of iteration methods." USSR Computational Mathematics and
          Mathematical Physics, 4(5), 1-17.

        - Sutskever, I., Martens, J., Dahl, G., & Hinton, G. (2013).
          "On the importance of initialization and momentum in deep learning."
          ICML 2013.

        - Nesterov, Y. (1983). "A method for unconstrained convex minimization
          problem with the rate of convergence O(1/k^2)." Doklady AN USSR, 269.

    Example:
        >>> from neuroscope import MLP
        >>> model = MLP([784, 128, 64, 10])
        >>> # Standard momentum
        >>> model.compile(optimizer="sgdm", lr=0.01)
        >>> history = model.fit(X_train, y_train, epochs=100)

        >>> # Nesterov momentum (recommended for deep networks)
        >>> model.compile(optimizer="sgdnm", lr=0.01)
        >>> history = model.fit(X_train, y_train, epochs=100)

    Notes:
        - Typical momentum values: 0.9 (default) or 0.95 (aggressive)
        - Nesterov momentum often converges faster than standard momentum
        - Momentum helps escape local minima and traverse flat regions
    """

    def __init__(
        self, learning_rate: float = 0.01, momentum: float = 0.9, nesterov: bool = False
    ):
        super().__init__(learning_rate)

        # Validate momentum
        if not 0 <= momentum < 1:
            raise ValueError(f"Momentum must be in [0, 1), got {momentum}")

        self.momentum = momentum
        self.nesterov = nesterov

        # Initialize velocity buffers (created on first update)
        self._state = {"velocity_w": [], "velocity_b": [], "initialized": False}

    def update(
        self,
        weights: List[np.ndarray],
        biases: List[np.ndarray],
        weight_grads: List[np.ndarray],
        bias_grads: List[np.ndarray],
    ) -> None:
        """
        Apply momentum-accelerated gradient update.

        Implements the momentum update rule from Polyak (1964) with
        optional Nesterov acceleration from Nesterov (1983).
        """
        # Initialize velocity buffers on first call
        if not self._state["initialized"]:
            self._state["velocity_w"] = [np.zeros_like(w) for w in weights]
            self._state["velocity_b"] = [np.zeros_like(b) for b in biases]
            self._state["initialized"] = True

        velocity_w = self._state["velocity_w"]
        velocity_b = self._state["velocity_b"]

        # Update each layer
        for i in range(len(weights)):
            # --- Weight updates ---
            # Momentum update: v_t = μ * v_{t-1} + g_t
            velocity_w[i] = self.momentum * velocity_w[i] + weight_grads[i]

            if self.nesterov:
                # Nesterov: θ_t = θ_{t-1} - α * (μ * v_t + g_t)
                update_w = self.momentum * velocity_w[i] + weight_grads[i]
            else:
                # Standard: θ_t = θ_{t-1} - α * v_t
                update_w = velocity_w[i]

            weights[i] -= self.learning_rate * update_w

            # --- Bias updates (same logic) ---
            velocity_b[i] = self.momentum * velocity_b[i] + bias_grads[i]

            if self.nesterov:
                update_b = self.momentum * velocity_b[i] + bias_grads[i]
            else:
                update_b = velocity_b[i]

            biases[i] -= self.learning_rate * update_b

    def state_dict(self) -> Dict[str, Any]:
        """Get optimizer state including velocity buffers."""
        return {
            "type": self.__class__.__name__,
            "learning_rate": self.learning_rate,
            "momentum": self.momentum,
            "nesterov": self.nesterov,
            "state": self._state,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load optimizer state including velocity buffers."""
        self.learning_rate = state_dict["learning_rate"]
        self.momentum = state_dict["momentum"]
        self.nesterov = state_dict["nesterov"]
        self._state = state_dict["state"]


class Adam(Optimizer):
    """
    Adam (Adaptive Moment Estimation) optimizer.

    Combines momentum with adaptive learning rates. Maintains exponential moving
    averages of gradients (first moment) and squared gradients (second moment).
    Includes bias correction to account for initialization at zero.

    Algorithm (Kingma & Ba, 2014):
        m_t = β₁ * m_{t-1} + (1 - β₁) * g_t       [First moment estimate]
        v_t = β₂ * v_{t-1} + (1 - β₂) * g_t²      [Second moment estimate]
        m̂_t = m_t / (1 - β₁ᵗ)                     [Bias-corrected first moment]
        v̂_t = v_t / (1 - β₂ᵗ)                     [Bias-corrected second moment]
        θ_t = θ_{t-1} - α * m̂_t / (√v̂_t + ε)     [Parameter update]

    Args:
        learning_rate: Learning rate α, default: 0.001
        beta1: First moment decay rate β₁ ∈ [0, 1), default: 0.9
        beta2: Second moment decay rate β₂ ∈ [0, 1), default: 0.999
        eps: Numerical stability constant ε, default: 1e-8

    References:
        Kingma, D. P., & Ba, J. (2014). "Adam: A Method for Stochastic
        Optimization." arXiv preprint arXiv:1412.6980.

    Example:
        >>> from neuroscope import MLP
        >>> model = MLP([784, 128, 64, 10])
        >>> # Standard Adam (recommended default)
        >>> model.compile(optimizer="adam", lr=0.001)
        >>> history = model.fit(X_train, y_train, epochs=100)

        >>> # Higher learning rate for faster convergence
        >>> model.compile(optimizer="adam", lr=0.01)
        >>> history = model.fit(X_train, y_train, epochs=100)

    Notes:
        - Default hyperparameters work well for most problems
        - Adam is particularly effective for sparse gradients and noisy data
        - Less sensitive to learning rate than SGD
        - Memory overhead: 2x parameters (stores m and v)
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
    ):
        super().__init__(learning_rate)

        # Validate hyperparameters
        if not 0 <= beta1 < 1:
            raise ValueError(f"beta1 must be in [0, 1), got {beta1}")
        if not 0 <= beta2 < 1:
            raise ValueError(f"beta2 must be in [0, 1), got {beta2}")
        if eps <= 0:
            raise ValueError(f"eps must be positive, got {eps}")

        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps

        # Initialize state (created on first update)
        self._state = {
            "m_weights": [],
            "v_weights": [],
            "m_biases": [],
            "v_biases": [],
            "t": 0,
            "initialized": False,
        }

    def update(
        self,
        weights: List[np.ndarray],
        biases: List[np.ndarray],
        weight_grads: List[np.ndarray],
        bias_grads: List[np.ndarray],
    ) -> None:
        """
        Apply Adam adaptive gradient update.

        Implements the Adam algorithm from Kingma & Ba (2014) with
        exponential moving averages and bias correction.
        """
        # Initialize moment buffers on first call
        if not self._state["initialized"]:
            self._state["m_weights"] = [np.zeros_like(w) for w in weights]
            self._state["v_weights"] = [np.zeros_like(w) for w in weights]
            self._state["m_biases"] = [np.zeros_like(b) for b in biases]
            self._state["v_biases"] = [np.zeros_like(b) for b in biases]
            self._state["initialized"] = True

        # Increment timestep
        self._state["t"] += 1
        t = self._state["t"]

        # Retrieve moment buffers
        m_w = self._state["m_weights"]
        v_w = self._state["v_weights"]
        m_b = self._state["m_biases"]
        v_b = self._state["v_biases"]

        # Update each layer
        for i in range(len(weights)):
            # --- Weight updates ---
            # Update biased first moment: m_t = β₁ * m_{t-1} + (1 - β₁) * g_t
            m_w[i] = self.beta1 * m_w[i] + (1 - self.beta1) * weight_grads[i]

            # Update biased second moment: v_t = β₂ * v_{t-1} + (1 - β₂) * g_t²
            v_w[i] = self.beta2 * v_w[i] + (1 - self.beta2) * (weight_grads[i] ** 2)

            # Bias correction
            m_hat_w = m_w[i] / (1 - self.beta1**t)
            v_hat_w = v_w[i] / (1 - self.beta2**t)

            # Parameter update: θ_t = θ_{t-1} - α * m̂_t / (√v̂_t + ε)
            weights[i] -= self.learning_rate * m_hat_w / (np.sqrt(v_hat_w) + self.eps)

            # --- Bias updates (same logic) ---
            m_b[i] = self.beta1 * m_b[i] + (1 - self.beta1) * bias_grads[i]
            v_b[i] = self.beta2 * v_b[i] + (1 - self.beta2) * (bias_grads[i] ** 2)

            m_hat_b = m_b[i] / (1 - self.beta1**t)
            v_hat_b = v_b[i] / (1 - self.beta2**t)

            biases[i] -= self.learning_rate * m_hat_b / (np.sqrt(v_hat_b) + self.eps)

    def state_dict(self) -> Dict[str, Any]:
        """Get optimizer state including moment estimates and timestep."""
        return {
            "type": self.__class__.__name__,
            "learning_rate": self.learning_rate,
            "beta1": self.beta1,
            "beta2": self.beta2,
            "eps": self.eps,
            "state": self._state,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load optimizer state including moment estimates and timestep."""
        self.learning_rate = state_dict["learning_rate"]
        self.beta1 = state_dict["beta1"]
        self.beta2 = state_dict["beta2"]
        self.eps = state_dict["eps"]
        self._state = state_dict["state"]


class RMSprop(Optimizer):
    """
    RMSprop (Root Mean Square Propagation) optimizer.

    Maintains moving average of squared gradients to normalize learning rates.
    Particularly effective for non-stationary objectives and recurrent networks.
    Can be seen as a precursor to Adam, using only second moment adaptation.

    Algorithm (Hinton, 2012; Tieleman & Hinton, 2012):
        E[g²]_t = ρ * E[g²]_{t-1} + (1 - ρ) * g_t²     [Moving average of squared gradients]
        θ_t = θ_{t-1} - α * g_t / (√E[g²]_t + ε)       [Parameter update]

    With momentum (optional):
        v_t = μ * v_{t-1} + α * g_t / (√E[g²]_t + ε)   [Momentum accumulation]
        θ_t = θ_{t-1} - v_t                             [Parameter update]

    Args:
        learning_rate: Learning rate α, default: 0.001
        rho: Decay rate for moving average ρ ∈ [0, 1), default: 0.9
        eps: Numerical stability constant ε, default: 1e-8
        momentum: Momentum coefficient μ ∈ [0, 1), default: 0.0 (disabled)

    References:
        - Tieleman, T., & Hinton, G. (2012). "Lecture 6.5 - RMSprop: Divide
          the gradient by a running average of its recent magnitude."
          COURSERA: Neural Networks for Machine Learning.

        - Hinton, G., Srivastava, N., & Swersky, K. (2012). "Neural Networks
          for Machine Learning Lecture 6a Overview of mini-batch gradient descent."

    Example:
        >>> from neuroscope import MLP
        >>> model = MLP([784, 128, 64, 10])
        >>> # Standard RMSprop (recommended for RNNs)
        >>> model.compile(optimizer="rmsprop", lr=0.001)
        >>> history = model.fit(X_train, y_train, epochs=100)

        >>> # Note: RMSprop uses built-in momentum=0.0 by default
        >>> # For momentum-based training, use "sgdm" or "sgdnm" instead

    Notes:
        - Default rho=0.9 works well for most problems
        - RMSprop handles sparse gradients better than standard SGD
        - Adding momentum can improve convergence stability
        - Less memory intensive than Adam (no first moment)
    """

    def __init__(
        self,
        learning_rate: float = 0.001,
        rho: float = 0.9,
        eps: float = 1e-8,
        momentum: float = 0.0,
    ):
        super().__init__(learning_rate)

        # Validate hyperparameters
        if not 0 <= rho < 1:
            raise ValueError(f"rho must be in [0, 1), got {rho}")
        if eps <= 0:
            raise ValueError(f"eps must be positive, got {eps}")
        if not 0 <= momentum < 1:
            raise ValueError(f"momentum must be in [0, 1), got {momentum}")

        self.rho = rho
        self.eps = eps
        self.momentum = momentum

        # Initialize state (created on first update)
        self._state = {
            "square_avg_weights": [],
            "square_avg_biases": [],
            "velocity_w": [],  # Only used if momentum > 0
            "velocity_b": [],  # Only used if momentum > 0
            "initialized": False,
        }

    def update(
        self,
        weights: List[np.ndarray],
        biases: List[np.ndarray],
        weight_grads: List[np.ndarray],
        bias_grads: List[np.ndarray],
    ) -> None:
        """
        Apply RMSprop adaptive gradient update.

        Implements the RMSprop algorithm from Tieleman & Hinton (2012)
        with optional momentum acceleration.
        """
        # Initialize buffers on first call
        if not self._state["initialized"]:
            self._state["square_avg_weights"] = [np.zeros_like(w) for w in weights]
            self._state["square_avg_biases"] = [np.zeros_like(b) for b in biases]
            if self.momentum > 0:
                self._state["velocity_w"] = [np.zeros_like(w) for w in weights]
                self._state["velocity_b"] = [np.zeros_like(b) for b in biases]
            self._state["initialized"] = True

        # Retrieve buffers
        sq_avg_w = self._state["square_avg_weights"]
        sq_avg_b = self._state["square_avg_biases"]

        # Update each layer
        for i in range(len(weights)):
            # --- Weight updates ---
            # Update moving average of squared gradients: E[g²]_t = ρ * E[g²]_{t-1} + (1-ρ) * g_t²
            sq_avg_w[i] = self.rho * sq_avg_w[i] + (1 - self.rho) * (
                weight_grads[i] ** 2
            )

            # Compute adaptive update: g_t / √E[g²]_t
            adaptive_grad_w = weight_grads[i] / (np.sqrt(sq_avg_w[i]) + self.eps)

            if self.momentum > 0:
                # Apply momentum: v_t = μ * v_{t-1} + α * adaptive_grad
                velocity_w = self._state["velocity_w"]
                velocity_w[i] = (
                    self.momentum * velocity_w[i] + self.learning_rate * adaptive_grad_w
                )
                weights[i] -= velocity_w[i]
            else:
                # Direct update: θ_t = θ_{t-1} - α * adaptive_grad
                weights[i] -= self.learning_rate * adaptive_grad_w

            # --- Bias updates (same logic) ---
            sq_avg_b[i] = self.rho * sq_avg_b[i] + (1 - self.rho) * (bias_grads[i] ** 2)
            adaptive_grad_b = bias_grads[i] / (np.sqrt(sq_avg_b[i]) + self.eps)

            if self.momentum > 0:
                velocity_b = self._state["velocity_b"]
                velocity_b[i] = (
                    self.momentum * velocity_b[i] + self.learning_rate * adaptive_grad_b
                )
                biases[i] -= velocity_b[i]
            else:
                biases[i] -= self.learning_rate * adaptive_grad_b

    def state_dict(self) -> Dict[str, Any]:
        """Get optimizer state including squared gradient averages and momentum."""
        return {
            "type": self.__class__.__name__,
            "learning_rate": self.learning_rate,
            "rho": self.rho,
            "eps": self.eps,
            "momentum": self.momentum,
            "state": self._state,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load optimizer state including squared gradient averages and momentum."""
        self.learning_rate = state_dict["learning_rate"]
        self.rho = state_dict["rho"]
        self.eps = state_dict["eps"]
        self.momentum = state_dict["momentum"]
        self._state = state_dict["state"]
