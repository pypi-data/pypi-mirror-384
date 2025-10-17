"""
Utilities Module
Helper functions for training, validation, and data processing.
"""

import numpy as np


class Utils:
    """
    Utility functions for neural network training and data processing.

    Provides essential helper functions for batch processing, gradient clipping,
    input validation, and numerical stability checks. All methods are static
    and can be used independently throughout the framework.
    """

    @staticmethod
    def get_batches(X, y, batch_size=32, shuffle=True):
        """
        Generate mini-batches for training.

        Creates mini-batches from input data with optional shuffling for
        stochastic gradient descent training. Handles the last batch even
        if it contains fewer samples than batch_size.

        Args:
            X (NDArray[np.float64]): Input data of shape (N, input_dim).
            y (NDArray[np.float64]): Target data of shape (N,) or (N, output_dim).
            batch_size (int, optional): Size of each mini-batch. Defaults to 32.
            shuffle (bool, optional): Whether to shuffle data before batching. Defaults to True.

        Yields:
            tuple[NDArray, NDArray]: (X_batch, y_batch) for each mini-batch.

        Example:
            >>> for X_batch, y_batch in Utils.get_batches(X_train, y_train, batch_size=64):
            ...     # Process batch
            ...     pass
        """
        N = X.shape[0]

        if y.ndim == 1:
            y = y.reshape(-1, 1)
        if shuffle:
            idx = np.random.permutation(N)
        else:
            idx = np.arange(N)

        for start in range(0, N, batch_size):
            end = min(start + batch_size, N)
            batch_idx = idx[start:end]
            yield X[batch_idx], y[batch_idx]

    @staticmethod
    def get_batches_fast(X, y, batch_size=32, shuffle=True):
        """
        Generate mini-batches for training with optimized memory usage.
        Expected to be 2-5x faster than get_batches() for large datasets.

        Args:
            X (NDArray[np.float64]): Input data of shape (N, input_dim).
            y (NDArray[np.float64]): Target data of shape (N,) or (N, output_dim).
            batch_size (int, optional): Size of each mini-batch. Defaults to 32.
            shuffle (bool, optional): Whether to shuffle data before batching. Defaults to True.

        Yields:
            tuple[NDArray, NDArray]: (X_batch, y_batch) for each mini-batch.

        Note:
            Uses array views (slicing) instead of fancy indexing to avoid memory allocation.
            Pre-reshapes y to avoid repeated reshaping in training loop.

        Example:
            >>> # Fast batch preprocessing for fast training
            >>> for X_batch, y_batch in Utils.get_batches_fast(X_train, y_train, batch_size=64):
            ...     # Process batch
            ...     pass
        """

        N = X.shape[0]

        if y.ndim == 1:
            y = y.reshape(-1, 1)
        if shuffle:
            idx = np.random.permutation(N)
            X_shuffled = X[idx]
            y_shuffled = y[idx]
        else:
            X_shuffled = X
            y_shuffled = y

        for start in range(0, N, batch_size):
            end = min(start + batch_size, N)
            yield X_shuffled[start:end], y_shuffled[start:end]

    @staticmethod
    def gradient_clipping(gradients, max_norm=5.0):
        """
        Apply gradient clipping to prevent exploding gradients.

        Clips gradients by global norm as described in Pascanu et al. (2013).
        If the global norm exceeds max_norm, all gradients are scaled down
        proportionally to maintain their relative magnitudes.

        Args:
            gradients (list[NDArray[np.float64]]): List of gradient arrays.
            max_norm (float, optional): Maximum allowed gradient norm. Defaults to 5.0.

        Returns:
            list[NDArray[np.float64]]: Clipped gradient arrays.

        Note:
            Based on "On the difficulty of training recurrent neural networks"
            (Pascanu et al. 2013) for gradient norm clipping.

        Example:
            >>> clipped_grads = Utils.gradient_clipping(gradients, max_norm=5.0)
        """
        total_norm = 0
        for grad in gradients:
            total_norm += np.sum(grad**2)
        total_norm = np.sqrt(total_norm)
        if total_norm > max_norm:
            clip_coef = max_norm / (total_norm + 1e-8)
            gradients = [grad * clip_coef for grad in gradients]
        return gradients

    @staticmethod
    def validate_array_input(arr, name, min_dims=1, max_dims=3, fast_mode=False):
        """
        Optimized validation for neural network operations.

        Performs efficient validation with optional fast mode for training.
        Automatically converts compatible inputs to numpy arrays when possible.

        Args:
            arr: Input array or array-like object to validate.
            name (str): Name of the array for error messages.
            min_dims (int, optional): Minimum allowed dimensions. Defaults to 1.
            max_dims (int, optional): Maximum allowed dimensions. Defaults to 3.
            fast_mode (bool, optional): Skip expensive NaN/inf checks for speed. Defaults to False.

        Returns:
            NDArray[np.float64]: Validated numpy array.

        Raises:
            TypeError: If input cannot be converted to numpy array.
            ValueError: If dimensions, shape, or values are invalid.

        Example:
            >>> X_valid = Utils.validate_array_input(X, "training_data", min_dims=2, max_dims=2)
            >>> X_fast = Utils.validate_array_input(X, "X_train", fast_mode=True)  # For fit_fast()
        """
        # Fast array conversion
        if not isinstance(arr, np.ndarray):
            try:
                arr = np.asarray(arr)
                if not fast_mode:  # Only warn in non-fast mode
                    print(f"{name} converted to numpy array")
            except Exception as e:
                raise TypeError(f"{name} must be convertible to numpy array: {e}")

        # Essential checks (always performed)
        if arr.ndim < min_dims or arr.ndim > max_dims:
            raise ValueError(
                f"{name} must have {min_dims}-{max_dims} dimensions, got {arr.ndim}"
            )
        if arr.size == 0:
            raise ValueError(f"{name} cannot be empty")

        # Expensive NaN/inf checks only in non-fast mode
        if not fast_mode and np.issubdtype(arr.dtype, np.floating):
            if np.any(np.isnan(arr)):
                raise ValueError(f"{name} contains NaN values")
            if np.any(np.isinf(arr)):
                raise ValueError(f"{name} contains infinite values")

        return arr

    @staticmethod
    def validate_layer_dims(layer_dims, input_dim):
        if not isinstance(layer_dims, (list, tuple)):
            raise TypeError("layer_dims must be a list or tuple")
        if len(layer_dims) < 2:
            raise ValueError(
                "layer_dims must have at least 2 layers (input and output)"
            )
        layer_dims = list(layer_dims)

        for i, dim in enumerate(layer_dims):
            if not isinstance(dim, int) or dim <= 0:
                raise ValueError(
                    f"Layer {i} dimension must be positive integer, got {dim}"
                )
        if layer_dims[0] != input_dim:
            raise ValueError(
                f"First layer dimension {layer_dims[0]} must match input features {input_dim}"
            )
        return layer_dims

    @staticmethod
    def check_numerical_stability(arrays, context="computation", fast_mode=False):
        """
        Simple numerical stability check with user-friendly warnings.

        Provides clear, actionable warnings for common training issues.
        Fast mode only checks for critical problems for performance.

        Args:
            arrays: List of arrays to check for numerical issues.
            context (str, optional): Context description for error messages. Defaults to "computation".
            fast_mode (bool, optional): Skip detailed checks for speed. Defaults to False.

        Returns:
            list: List of simple, actionable issue descriptions.

        Example:
            >>> issues = Utils.check_numerical_stability(activations, "forward_pass")
            >>> if issues:
            ...     print(f"Training Issue: {issues[0]}")
        """
        issues = []

        for i, arr in enumerate(arrays):
            if arr is None:
                continue

            if np.any(np.isnan(arr)):
                if fast_mode:
                    return [
                        "Model has broken (NaN values). Try lower learning rate or check your data."
                    ]
                else:
                    issues.append(
                        "Model has broken (NaN values). Try lower learning rate or check your data."
                    )
                    break
            if np.any(np.isinf(arr)):
                if fast_mode:
                    return [
                        "Gradients exploded (Inf values). Use lower learning rate or normalize your data."
                    ]
                else:
                    issues.append(
                        "Gradients exploded (Inf values). Use lower learning rate or normalize your data."
                    )
                    break

            if not fast_mode:
                max_val = np.max(np.abs(arr))
                if max_val > 1e8:
                    if context == "gradients":
                        issues.append(
                            "Gradients are getting very large. Consider lowering learning rate or normalizing data."
                        )
                    elif context == "forward_pass" or context == "output_activations":
                        issues.append(
                            "Network outputs are getting very large. Check if your data is normalized (e.g., pixels should be 0-1, not 0-255)."
                        )
                    else:
                        issues.append(
                            f"Values in {context} are getting very large. This may cause training instability."
                        )
                    break

                # Note: Vanishing gradients are often normal in deep networks
                # Training monitors (loss tracking) will catch real issues

        return issues
