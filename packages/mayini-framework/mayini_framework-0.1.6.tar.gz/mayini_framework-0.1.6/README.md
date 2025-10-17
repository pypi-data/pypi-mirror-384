
# MAYINI Deep Learning Framework

[![PyPI version](https://badge.fury.io/py/mayini-framework.svg)](https://badge.fury.io/py/mayini-framework)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/yourusername/mayini-framework/workflows/CI/badge.svg)](https://github.com/yourusername/mayini-framework/actions)

MAYINI is a comprehensive deep learning framework built from scratch in Python, featuring automatic differentiation, neural network components, and complete training infrastructure. It's designed for educational purposes and research, providing a PyTorch-like API with full transparency into the underlying mechanics.

## 🚀 Key Features

### Core Engine
- **Tensor Operations**: Complete tensor class with automatic differentiation
- **Computational Graph**: Cycle detection and gradient computation
- **Broadcasting Support**: NumPy-style broadcasting for operations

### Neural Network Components
- **Linear Layers**: Dense layers with multiple initialization methods (Xavier, He, Normal)
- **Convolutional Layers**: 2D convolution with im2col optimization
- **Pooling Layers**: Max and Average pooling with stride and padding support
- **Normalization**: Batch Normalization for improved training
- **Regularization**: Dropout with inverted dropout implementation

### Activation Functions
- **Standard Functions**: ReLU, Sigmoid, Tanh, Softmax
- **Modern Activations**: GELU, Leaky ReLU
- **Numerical Stability**: Implemented with overflow/underflow protection

### Recurrent Neural Networks
- **RNN Cells**: Vanilla RNN with configurable activations
- **LSTM Cells**: Long Short-Term Memory with proper gate mechanisms
- **GRU Cells**: Gated Recurrent Units for efficient sequence modeling
- **Multi-layer Support**: Stack multiple RNN layers with dropout

### Loss Functions
- **Regression**: MSE Loss, MAE Loss, Huber Loss
- **Classification**: Cross-Entropy Loss, Binary Cross-Entropy Loss
- **Flexible Reduction**: Support for mean, sum, and none reduction modes

### Optimization Algorithms
- **SGD**: Stochastic Gradient Descent with momentum and weight decay
- **Adam**: Adaptive moment estimation with bias correction
- **AdamW**: Adam with decoupled weight decay
- **RMSprop**: Root Mean Square Propagation

### Training Infrastructure
- **DataLoader**: Efficient batch processing with shuffling
- **Metrics**: Comprehensive evaluation (accuracy, precision, recall, F1)
- **Early Stopping**: Prevent overfitting with validation monitoring
- **Learning Rate Scheduling**: Step, exponential, and cosine annealing schedulers
- **Checkpointing**: Save and restore model states

## 📦 Installation

### From PyPI
```bash
pip install mayini-framework
```

### From Source
```bash
git clone https://github.com/yourusername/mayini-framework.git
cd mayini-framework
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/yourusername/mayini-framework.git
cd mayini-framework
pip install -e ".[dev]"
```

## 🏃 Quick Start

### Basic Tensor Operations
```python
import mayini as mn

# Create tensors with automatic differentiation
x = mn.Tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
y = mn.Tensor([[2.0, 1.0], [1.0, 2.0]], requires_grad=True)

# Perform operations
z = x.matmul(y) + x * 2
loss = z.sum()

# Automatic differentiation
loss.backward()
print(f"Gradient of x: {x.grad}")
print(f"Gradient of y: {y.grad}")
```

### Building Neural Networks
```python
from mayini.nn import Sequential, Linear, ReLU, Softmax

# Create a simple neural network
model = Sequential(
    Linear(784, 256, init_method='he'),
    ReLU(),
    Linear(256, 128, init_method='he'), 
    ReLU(),
    Linear(128, 10),
    Softmax(dim=1)
)

# Forward pass
x = mn.Tensor(np.random.randn(32, 784))
output = model(x)
print(f"Output shape: {output.shape}")
```

### Training a Model
```python
from mayini.optim import Adam
from mayini.nn import CrossEntropyLoss
from mayini.data import DataLoader
from mayini.training import Trainer

# Setup training components
optimizer = Adam(model.parameters(), lr=0.001)
criterion = CrossEntropyLoss()
train_loader = DataLoader(X_train, y_train, batch_size=64, shuffle=True)

# Create trainer and train
trainer = Trainer(model, optimizer, criterion)
history = trainer.fit(train_loader, epochs=10, verbose=True)
```

### Convolutional Neural Networks
```python
from mayini.nn import Conv2D, MaxPool2D, Flatten

# CNN for image classification
cnn_model = Sequential(
    Conv2D(1, 32, kernel_size=3, padding=1),
    ReLU(),
    MaxPool2D(kernel_size=2),
    Conv2D(32, 64, kernel_size=3, padding=1),
    ReLU(), 
    MaxPool2D(kernel_size=2),
    Flatten(),
    Linear(64 * 7 * 7, 128),
    ReLU(),
    Linear(128, 10),
    Softmax(dim=1)
)
```

### Recurrent Neural Networks
```python
from mayini.nn import RNN, LSTMCell

# LSTM for sequence modeling
lstm_model = RNN(
    input_size=100,
    hidden_size=128, 
    num_layers=2,
    cell_type='lstm',
    dropout=0.2,
    batch_first=True
)

# Process sequences
x_seq = mn.Tensor(np.random.randn(32, 50, 100))  # (batch, seq_len, features)
output, hidden_states = lstm_model(x_seq)
```

## 📚 Documentation

### API Reference

#### Core Components
- **Tensor**: Core tensor class with automatic differentiation
- **Module**: Base class for all neural network modules
- **Sequential**: Container for chaining modules

#### Neural Network Layers
- **Linear**: Fully connected layer
- **Conv2D**: 2D convolutional layer
- **MaxPool2D, AvgPool2D**: Pooling layers
- **BatchNorm1d**: Batch normalization
- **Dropout**: Dropout regularization

#### Activation Functions
- **ReLU, Sigmoid, Tanh, Softmax**: Standard activations
- **GELU, LeakyReLU**: Modern activation functions

#### Loss Functions
- **MSELoss**: Mean squared error
- **CrossEntropyLoss**: Cross-entropy for classification
- **BCELoss**: Binary cross-entropy
- **HuberLoss**: Robust loss for regression

#### Optimizers
- **SGD**: Stochastic gradient descent
- **Adam**: Adaptive moment estimation
- **AdamW**: Adam with decoupled weight decay
- **RMSprop**: Root mean square propagation

### Examples

Complete examples are available in the `examples/` directory:
- **MNIST Classification**: Train a neural network on handwritten digits
- **CIFAR-10 CNN**: Convolutional neural network for image classification
- **Text Classification**: RNN/LSTM for sequence classification
- **Time Series Prediction**: Forecasting with recurrent networks

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=mayini tests/
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/yourusername/mayini-framework.git
cd mayini-framework
pip install -e ".[dev]"
pre-commit install
```

### Running Tests
```bash
pytest tests/
black src/
flake8 src/
```

## 📖 Educational Use

MAYINI is designed with education in mind. Each component is implemented from scratch with clear, readable code and comprehensive documentation. It's perfect for:

- **Learning Deep Learning**: Understand how neural networks work under the hood
- **Research Projects**: Prototype new architectures and algorithms
- **Teaching**: Demonstrate concepts with transparent implementations
- **Experimentation**: Quick prototyping of ideas

## 🔬 Comparison with Other Frameworks

| Feature | MAYINI | PyTorch | TensorFlow |
|---------|--------|---------|------------|
| Educational Focus | ✅ | ❌ | ❌ |
| Transparent Implementation | ✅ | ❌ | ❌ |
| Automatic Differentiation | ✅ | ✅ | ✅ |
| GPU Support | ❌ | ✅ | ✅ |
| Production Ready | ❌ | ✅ | ✅ |
| Easy to Understand | ✅ | ⚠️ | ❌ |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by PyTorch's design philosophy
- Built for educational purposes and research
- Thanks to the open-source community for inspiration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mayini-framework/issues)
- **Documentation**: [Read the Docs](https://mayini-framework.readthedocs.io/)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mayini-framework/discussions)

## 🗺️ Roadmap

- [ ] GPU support with CUDA
- [ ] More activation functions (Swish, Mish, etc.)
- [ ] Transformer components
- [ ] Model serialization/deserialization
- [ ] Distributed training support
- [ ] Mobile deployment utilities

---

**MAYINI** - Making AI Neural Intelligence Intuitive 🧠✨# MAYINI Deep Learning Framework

[![PyPI version](https://badge.fury.io/py/mayini-framework.svg)](https://badge.fury.io/py/mayini-framework)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/yourusername/mayini-framework/workflows/CI/badge.svg)](https://github.com/yourusername/mayini-framework/actions)

MAYINI is a comprehensive deep learning framework built from scratch in Python, featuring automatic differentiation, neural network components, and complete training infrastructure. It's designed for educational purposes and research, providing a PyTorch-like API with full transparency into the underlying mechanics.

## 🚀 Key Features

### Core Engine
- **Tensor Operations**: Complete tensor class with automatic differentiation
- **Computational Graph**: Cycle detection and gradient computation
- **Broadcasting Support**: NumPy-style broadcasting for operations

### Neural Network Components
- **Linear Layers**: Dense layers with multiple initialization methods (Xavier, He, Normal)
- **Convolutional Layers**: 2D convolution with im2col optimization
- **Pooling Layers**: Max and Average pooling with stride and padding support
- **Normalization**: Batch Normalization for improved training
- **Regularization**: Dropout with inverted dropout implementation

### Activation Functions
- **Standard Functions**: ReLU, Sigmoid, Tanh, Softmax
- **Modern Activations**: GELU, Leaky ReLU
- **Numerical Stability**: Implemented with overflow/underflow protection

### Recurrent Neural Networks
- **RNN Cells**: Vanilla RNN with configurable activations
- **LSTM Cells**: Long Short-Term Memory with proper gate mechanisms
- **GRU Cells**: Gated Recurrent Units for efficient sequence modeling
- **Multi-layer Support**: Stack multiple RNN layers with dropout

### Loss Functions
- **Regression**: MSE Loss, MAE Loss, Huber Loss
- **Classification**: Cross-Entropy Loss, Binary Cross-Entropy Loss
- **Flexible Reduction**: Support for mean, sum, and none reduction modes

### Optimization Algorithms
- **SGD**: Stochastic Gradient Descent with momentum and weight decay
- **Adam**: Adaptive moment estimation with bias correction
- **AdamW**: Adam with decoupled weight decay
- **RMSprop**: Root Mean Square Propagation

### Training Infrastructure
- **DataLoader**: Efficient batch processing with shuffling
- **Metrics**: Comprehensive evaluation (accuracy, precision, recall, F1)
- **Early Stopping**: Prevent overfitting with validation monitoring
- **Learning Rate Scheduling**: Step, exponential, and cosine annealing schedulers
- **Checkpointing**: Save and restore model states

## 📦 Installation

### From PyPI
```bash
pip install mayini-framework
```

### From Source
```bash
git clone https://github.com/yourusername/mayini-framework.git
cd mayini-framework
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/yourusername/mayini-framework.git
cd mayini-framework
pip install -e ".[dev]"
```

## 🏃 Quick Start

### Basic Tensor Operations
```python
import mayini as mn

# Create tensors with automatic differentiation
x = mn.Tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
y = mn.Tensor([[2.0, 1.0], [1.0, 2.0]], requires_grad=True)

# Perform operations
z = x.matmul(y) + x * 2
loss = z.sum()

# Automatic differentiation
loss.backward()
print(f"Gradient of x: {x.grad}")
print(f"Gradient of y: {y.grad}")
```

### Building Neural Networks
```python
from mayini.nn import Sequential, Linear, ReLU, Softmax

# Create a simple neural network
model = Sequential(
    Linear(784, 256, init_method='he'),
    ReLU(),
    Linear(256, 128, init_method='he'), 
    ReLU(),
    Linear(128, 10),
    Softmax(dim=1)
)

# Forward pass
x = mn.Tensor(np.random.randn(32, 784))
output = model(x)
print(f"Output shape: {output.shape}")
```

### Training a Model
```python
from mayini.optim import Adam
from mayini.nn import CrossEntropyLoss
from mayini.data import DataLoader
from mayini.training import Trainer

# Setup training components
optimizer = Adam(model.parameters(), lr=0.001)
criterion = CrossEntropyLoss()
train_loader = DataLoader(X_train, y_train, batch_size=64, shuffle=True)

# Create trainer and train
trainer = Trainer(model, optimizer, criterion)
history = trainer.fit(train_loader, epochs=10, verbose=True)
```

### Convolutional Neural Networks
```python
from mayini.nn import Conv2D, MaxPool2D, Flatten

# CNN for image classification
cnn_model = Sequential(
    Conv2D(1, 32, kernel_size=3, padding=1),
    ReLU(),
    MaxPool2D(kernel_size=2),
    Conv2D(32, 64, kernel_size=3, padding=1),
    ReLU(), 
    MaxPool2D(kernel_size=2),
    Flatten(),
    Linear(64 * 7 * 7, 128),
    ReLU(),
    Linear(128, 10),
    Softmax(dim=1)
)
```

### Recurrent Neural Networks
```python
from mayini.nn import RNN, LSTMCell

# LSTM for sequence modeling
lstm_model = RNN(
    input_size=100,
    hidden_size=128, 
    num_layers=2,
    cell_type='lstm',
    dropout=0.2,
    batch_first=True
)

# Process sequences
x_seq = mn.Tensor(np.random.randn(32, 50, 100))  # (batch, seq_len, features)
output, hidden_states = lstm_model(x_seq)
```

## 📚 Documentation

### API Reference

#### Core Components
- **Tensor**: Core tensor class with automatic differentiation
- **Module**: Base class for all neural network modules
- **Sequential**: Container for chaining modules

#### Neural Network Layers
- **Linear**: Fully connected layer
- **Conv2D**: 2D convolutional layer
- **MaxPool2D, AvgPool2D**: Pooling layers
- **BatchNorm1d**: Batch normalization
- **Dropout**: Dropout regularization

#### Activation Functions
- **ReLU, Sigmoid, Tanh, Softmax**: Standard activations
- **GELU, LeakyReLU**: Modern activation functions

#### Loss Functions
- **MSELoss**: Mean squared error
- **CrossEntropyLoss**: Cross-entropy for classification
- **BCELoss**: Binary cross-entropy
- **HuberLoss**: Robust loss for regression

#### Optimizers
- **SGD**: Stochastic gradient descent
- **Adam**: Adaptive moment estimation
- **AdamW**: Adam with decoupled weight decay
- **RMSprop**: Root mean square propagation

### Examples

Complete examples are available in the `examples/` directory:
- **MNIST Classification**: Train a neural network on handwritten digits
- **CIFAR-10 CNN**: Convolutional neural network for image classification
- **Text Classification**: RNN/LSTM for sequence classification
- **Time Series Prediction**: Forecasting with recurrent networks

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=mayini tests/
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/yourusername/mayini-framework.git
cd mayini-framework
pip install -e ".[dev]"
pre-commit install
```

### Running Tests
```bash
pytest tests/
black src/
flake8 src/
```

## 📖 Educational Use

MAYINI is designed with education in mind. Each component is implemented from scratch with clear, readable code and comprehensive documentation. It's perfect for:

- **Learning Deep Learning**: Understand how neural networks work under the hood
- **Research Projects**: Prototype new architectures and algorithms
- **Teaching**: Demonstrate concepts with transparent implementations
- **Experimentation**: Quick prototyping of ideas

## 🔬 Comparison with Other Frameworks

| Feature | MAYINI | PyTorch | TensorFlow |
|---------|--------|---------|------------|
| Educational Focus | ✅ | ❌ | ❌ |
| Transparent Implementation | ✅ | ❌ | ❌ |
| Automatic Differentiation | ✅ | ✅ | ✅ |
| GPU Support | ❌ | ✅ | ✅ |
| Production Ready | ❌ | ✅ | ✅ |
| Easy to Understand | ✅ | ⚠️ | ❌ |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by PyTorch's design philosophy
- Built for educational purposes and research
- Thanks to the open-source community for inspiration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mayini-framework/issues)
- **Documentation**: [Read the Docs](https://mayini-framework.readthedocs.io/)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mayini-framework/discussions)

## 🗺️ Roadmap

- [ ] GPU support with CUDA
- [ ] More activation functions (Swish, Mish, etc.)
- [ ] Transformer components
- [ ] Model serialization/deserialization
- [ ] Distributed training support
- [ ] Mobile deployment utilities

---

**MAYINI** - Making AI Neural Intelligence Intuitive 🧠✨
