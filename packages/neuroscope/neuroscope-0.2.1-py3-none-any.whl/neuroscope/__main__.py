"""
NeuroScope Command Line Interface.

This module provides a command-line interface for NeuroScope, allowing users to:
- Get version information
- Validate installation
- Access help and documentation

Usage:
    python -m neuroscope --version
    python -m neuroscope --validate
    python -m neuroscope --help

Examples:
    # Check version
    python -m neuroscope --version

    # Validate installation
    python -m neuroscope --validate

    # Get help
    python -m neuroscope --help
"""

import argparse
import sys
from typing import Optional

import matplotlib
import numpy as np

from neuroscope import __version__


def print_banner() -> None:
    """Print the NeuroScope banner."""
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                         NeuroScope                           ║
║              A Microscope for Neural Networks                ║
║                                                              ║
║  Version   : {__version__:<10}                                      ║
║  Python    : {sys.version.split()[0]:<10}                                      ║
║  NumPy     : {np.__version__:<10}                                      ║
║  Matplotlib: {matplotlib.__version__:<10}                                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def validate_installation() -> bool:
    """
    Validate NeuroScope installation by testing core functionality.

    Returns:
        bool: True if validation passes, False otherwise.
    """
    print("Validating NeuroScope installation...")

    try:
        # Test 1: Import validation
        print("1. Testing imports...")
        from neuroscope import PreTrainingAnalyzer  # noqa: F401
        from neuroscope import TrainingMonitor  # noqa: F401
        from neuroscope import Visualizer  # noqa: F401
        from neuroscope import he_init  # noqa: F401
        from neuroscope import relu  # noqa: F401
        from neuroscope import MLP, accuracy_binary, mse

        # Test 2: Basic MLP creation
        print("2. Testing MLP creation...")
        model = MLP([4, 8, 2], hidden_activation="relu", out_activation="sigmoid")

        # Test 3: Model compilation
        print("3. Testing model compilation...")
        model.compile(optimizer="adam", lr=0.01)

        # Test 4: Synthetic data creation and forward pass
        print("4. Testing forward pass...")
        X_test = np.random.randn(10, 4)
        y_test = np.random.randint(0, 2, (10, 1))

        predictions = model.predict(X_test)
        assert predictions.shape == (
            10,
            2,
        ), f"Expected shape (10, 2), got {predictions.shape}"

        # Test 5: Loss and metric computation
        print("5. Testing loss and metrics...")
        loss_val = mse(y_test, predictions[:, :1])
        acc_val = accuracy_binary(y_test, predictions[:, :1])

        assert isinstance(loss_val, (int, float, np.number)), "Loss should be numeric"
        assert isinstance(
            acc_val, (int, float, np.number)
        ), "Accuracy should be numeric"

        # Test 6: Quick training test
        print("6. Testing training functionality...")
        # Use binary classification format - reshape y to match output
        y_binary = np.column_stack(
            [1 - y_test.flatten(), y_test.flatten()]
        )  # One-hot encode
        history = model.fit_fast(X_test, y_binary, epochs=2, batch_size=5, verbose=0)

        # Check if history contains training data (could be different key names)
        assert isinstance(history, dict), "Training should return history dictionary"
        assert len(history) > 0, "History should not be empty"

        print("All validation tests passed!")
        return True

    except Exception as e:
        print(f"Validation failed: {e}")
        return False


def show_help() -> None:
    """Show detailed help information."""
    help_text = """
NeuroScope - A Microscope for Neural Networks

USAGE:
    python -m neuroscope [OPTIONS]

OPTIONS:
    --version, -v     Show version information
    --validate        Validate installation
    --help, -h        Show this help message

EXAMPLES:
    # Check version
    python -m neuroscope --version
    
    # Validate installation
    python -m neuroscope --validate

GETTING STARTED:
    1. Import NeuroScope components:
       from neuroscope import MLP, PreTrainingAnalyzer, TrainingMonitor, Visualizer
    
    2. Create a model:
       model = MLP([784, 128, 10], activation="relu", out_activation="softmax")
    
    3. Compile the model:
       model.compile(optimizer="adam", lr=1e-3)
    
    4. Train with diagnostics:
       history = model.fit(X_train, y_train, X_val, y_val, epochs=100)
    
    5. Or train ultra-fast:
       history = model.fit_fast(X_train, y_train, X_val, y_val, epochs=100)

DOCUMENTATION:
    Online: https://www.neuroscope.dev/
    Examples: Check the examples/ directory in the repository

SUPPORT:
    GitHub: https://github.com/ahmadrazacdx/neuro-scope
    Issues: https://github.com/ahmadrazacdx/neuro-scope/issues
"""
    print(help_text)


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the NeuroScope CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="neuroscope",
        description="NeuroScope - A Microscope for Neural Networks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m neuroscope --version    Show version information
  python -m neuroscope --validate   Validate installation
        """,
    )

    parser.add_argument(
        "--version", "-v", action="store_true", help="Show version information"
    )

    parser.add_argument(
        "--validate", action="store_true", help="Validate NeuroScope installation"
    )

    # Parse arguments
    args = parser.parse_args(argv)

    # No arguments - show help
    if not any(vars(args).values()):
        print_banner()
        show_help()
        return 0

    # Version
    if args.version:
        print_banner()
        return 0

    # Validation
    if args.validate:
        print_banner()
        success = validate_installation()
        return 0 if success else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
