<div align="center">
  <img src="https://raw.githubusercontent.com/ahmadrazacdx/neuro-scope/main/docs/_static/logo.svg" alt="Framework Logo" width="300" height="135" />
</div>

[![PyPI](https://img.shields.io/pypi/v/neuroscope.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/neuroscope.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/neuroscope)][pypi status]
[![License](https://img.shields.io/pypi/l/neuroscope)][license]
[![Documentation](https://img.shields.io/badge/docs-github--pages-blue)][read the docs]
[![Tests](https://github.com/ahmadrazacdx/neuro-scope/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/ahmadrazacdx/neuro-scope/branch/main/graph/badge.svg)][codecov]
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/neuroscope/
[read the docs]: https://www.neuroscope.dev/
[tests]: https://github.com/ahmadrazacdx/neuro-scope/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/ahmadrazacdx/neuro-scope
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

**A microscope for neural networks** - Comprehensive framework for building, training, and diagnosing multi-layer perceptrons with advanced monitoring and visualization capabilities.

## Features

### Modern MLP Implementation
- **Flexible Architecture**: Arbitrary layer sizes with customizable activations
- **Advanced Optimizers**: 5 production-ready optimizers validated against literature
  - **SGD**: Classic stochastic gradient descent (Robbins & Monro, 1951)
  - **SGD+Momentum**: Polyak momentum for accelerated convergence (Polyak, 1964)
  - **SGD+Nesterov**: Lookahead momentum for superior convergence (Nesterov, 1983)
  - **RMSprop**: Adaptive learning rates (Hinton, 2012) with optional Nesterov
  - **Adam**: Default choice with bias-corrected moments (Kingma & Ba, 2014)
- **Smart Initialization**: He, Xavier, SELU, and intelligent auto-selection
- **Regularization**: L2 regularization, dropout with multiple variants
- **Model Persistence**: Complete save/load system with optimizer state preservation

### High-Performance Training
- **Ultra-Fast Training**: `fit_fast()` method with 10-80x speedup over standard training
- **Memory Efficient**: 60-80% memory reduction with optimized batch processing
- **Flexible Performance**: Choose between speed (`fit_fast()`) and diagnostics (`fit()`)

### Comprehensive Diagnostics
- **Pre-Training Analysis**: Architecture validation, weight initialization checks
- **Real-Time Monitoring**: Dead neuron detection, gradient flow analysis and 8 other moitors
- **Post-Training Evaluation**: Robustness testing, performance profiling
- **Research-Validated Metrics**: Based on established deep learning principles

### High Quality Visualization
- **Training Dynamics**: Learning curves, loss landscapes, convergence analysis
- **Network Internals**: Activation distributions, gradient flows, weight evolution
- **Diagnostic Plots**: Health indicators, training stability metrics
- **Interactive Animations**: Training progress visualization

### Developer Experience
- **Clean API**: Intuitive interface with sensible defaults
- **Type Safety**: Full type hints and runtime validation
- **Comprehensive Testing**: 60%+ test coverage with property-based testing
- **Production Ready**: Extensive documentation, CI/CD, and quality assurance

## Requirements

- **Python**: 3.11+ (3.12 recommended)
- **Core Dependencies**: NumPy 2.3+, Matplotlib 3.10+
- **Optional**: Jupyter for interactive examples

## Quick Start

### Installation

```bash
# Install from PyPI (recommended)
pip install neuroscope

# Install from source (development)
git clone https://github.com/ahmadrazacdx/neuro-scope.git
cd neuro-scope
pip install -e .
```

### Fast Training

```python
import numpy as np
from neuroscope import MLP

# Create and configure model
model = MLP([784, 128, 64, 10], 
           hidden_activation="relu", 
           out_activation="softmax")

# Choose your optimizer: "adam", "sgd", "sgdm", "sgdnm", "rmsprop"
model.compile(optimizer="adam", lr=1e-3)

# Ultra-fast training - 10-100x speedup!
history = model.fit_fast(
    X_train, y_train, X_val, y_val,
    epochs=100, 
    batch_size=256,
    eval_freq=5 
)

# Save trained model
model.save("my_model.ns", save_optimizer=True)

# Load and use later
loaded_model = MLP.load("my_model.ns", load_optimizer=True)
predictions = loaded_model.predict(X_test)
```

### Full Diagnostic Training

```python
from neuroscope import MLP, PreTrainingAnalyzer, TrainingMonitor, Visualizer

# Create model
model = MLP([784, 128, 64, 10])
model.compile(optimizer="adam", lr=1e-3)

# Pre-training analysis
analyzer = PreTrainingAnalyzer(model)
pre_results = analyzer.analyze(X_train, y_train)

# Train with comprehensive monitoring
monitor = TrainingMonitor()
history = model.fit(X_train, y_train, X_val, y_val,
                   epochs=100, monitor=monitor)

# Visualize results
viz = Visualizer(history)
viz.plot_learning_curves()
viz.plot_activation_hist()
```

### Direct Function Access

```python
from neuroscope import mse, accuracy_binary, relu, he_init

# Use functions directly without class instantiation
loss = mse(y_true, y_pred)
acc = accuracy_binary(y_true, y_pred)
activated = relu(z)
weights, biases = he_init([784, 128, 10])
```

## Documentation

- **[Full Documentation](https://www.neuroscope.dev/)**: Complete API reference and guides
- **[Quickstart Guide](https://www.neuroscope.dev/quickstart.html)**: Get up and running in minutes
- **[API Reference](https://www.neuroscope.dev/reference.html)**: Detailed function and class documentation
- **[Examples](https://github.com/ahmadrazacdx/neuro-scope/tree/main/examples)**: Jupyter notebooks and scripts

## Use Cases

### Educational
- **Learning Deep Learning**: Understand neural network internals with detailed diagnostics
- **Research Projects**: Rapid prototyping with comprehensive analysis tools
- **Teaching**: Visual demonstrations of training dynamics and common issues

### Research & Development
- **Algorithm Development**: Test new optimization techniques and architectures
- **Proof of Concepts**: Quick validation of neural network approaches
- **Debugging**: Identify and resolve training issues with diagnostic tools

## Comparison with Other Frameworks

| Feature | NeuroScope | PyTorch | TensorFlow | Scikit-learn |
|---------|------------|---------|------------|--------------|
| **Training Speed** | Fast (`fit_fast()`) | Fast | Fast | Moderate |
| **Learning Focus** | Educational + Production | Production | Production | Traditional ML |
| **Built-in Diagnostics** | Rich | Manual | Manual | Limited |
| **Visualization** | High Quality | Manual | Manual | Basic |
| **Ease of Use** | Intuitive | Complex | Complex | Simple |
| **MLP Focus** | Specialized | General | General | Limited |

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ahmadrazacdx/neuro-scope.git
cd neuro-scope

# Set up development environment
make dev

# Run tests
make test

# Build documentation
make docs
```

## License

Distributed under the terms of the [Apache 2.0 license][license],
NeuroScope is free and open source software.

## Issues & Support

If you encounter any problems:
- **[File an Issue](https://github.com/ahmadrazacdx/neuro-scope/issues)**: Bug reports and feature requests
- **[Discussions](https://github.com/ahmadrazacdx/neuro-scope/discussions)**: Questions and community support
- **[Documentation](https://www.neuroscope.dev/)**: Comprehensive guides and API reference

## Acknowledgments

We extend our sincere gratitude to the following individuals and works that have profoundly influenced the development of NeuroScope:

### Foundational Inspirations

- **Geoffrey Hinton** - The _Godfather of Deep Learning_ whose groundbreaking work on neural networks, backpropagation, and deep learning architectures laid the foundation for modern AI. 

- **Andrej Karpathy** ([@karpathy](https://github.com/karpathy)) - His philosophy of "building neural networks from scratch" and granular mastery has been instrumental in shaping NeuroScope's educational approach and commitment to algorithmic transparency.
  
- **Jeremy Howard** ([@jph00](https://github.com/jph00)) - His work has inspired NeuroScope's philosophy of combining educational clarity, literature adherance, compliance with best practices and ease of use.
  
- **Deep Learning (MIT Press, 2016)** ([Goodfellow et al.](https://www.deeplearningbook.org/)) . This seminal work provided the theoretical foundation and mathematical rigor that underlies NeuroScope's diagnostic capabilities and research-validated implementations.



### Technical Contributions
 
- **Muhammad Talha** ([@mtalhacdx](https://github.com/mtalhacdx)) - For the elegant logo design and visual identity that captures NeuroScope's beauty of simplicity.

- **GitHub Copilot (Claude Sonnet 4)** - For invaluable assistance in documentation generation, comprehensive test suite development, workflows optimization, and guidance throughout the development process.



### Research Community

Special recognition to the neural network research community whose decades of theoretical advances and empirical insights have made frameworks like NeuroScope possible. We stand on the shoulders of giants in machine learning, optimization theory, and computational neuroscience.

---

*"NeuroScope is built with modern Python best practices and inspired by the educational philosophy of making neural networks transparent, understandable, and accessible to learners and researchers worldwide."*

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ahmadrazacdx/neuro-scope.git
cd neuro-scope

# Set up development environment
make dev

# Run tests
make test

# Build documentation
make docs
```

## License

Distributed under the terms of the [Apache 2.0 license][license],
NeuroScope is free and open source software.

## Issues & Support

If you encounter any problems:
- **[File an Issue](https://github.com/ahmadrazacdx/neuro-scope/issues)**: Bug reports and feature requests
- **[Discussions](https://github.com/ahmadrazacdx/neuro-scope/discussions)**: Questions and community support
- **[Documentation](https://www.neuroscope.dev/)**: Comprehensive guides and API reference

<!-- github-only -->

[license]: https://github.com/ahmadrazacdx/neuro-scope/blob/main/LICENSE
[contributor guide]: https://github.com/ahmadrazacdx/neuro-scope/blob/main/CONTRIBUTING.md
