"""
Activation functions for neural networks.
"""
import numpy as np
from abc import ABC, abstractmethod
from ..tensor import Tensor


class ActivationFunction(ABC):
    """Base class for activation functions."""
    
    @abstractmethod
    def forward(self, x: Tensor) -> Tensor:
        pass
    
    def __call__(self, x: Tensor) -> Tensor:
        return self.forward(x)


class ReLU(ActivationFunction):
    """Rectified Linear Unit activation function."""
    
    def forward(self, x: Tensor) -> Tensor:
        result_data = np.maximum(0, x.data)
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = "ReLUBackward"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                grad = out.grad * (x.data > 0).astype(x.data.dtype)
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out


class Sigmoid(ActivationFunction):
    """Sigmoid activation function."""
    
    def forward(self, x: Tensor) -> Tensor:
        # Numerical stability: clip input to prevent overflow
        clipped_data = np.clip(x.data, -500, 500)
        result_data = 1 / (1 + np.exp(-clipped_data))
        
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = "SigmoidBackward"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                sigmoid_grad = result_data * (1 - result_data)
                grad = out.grad * sigmoid_grad
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out


class Tanh(ActivationFunction):
    """Hyperbolic tangent activation function."""
    
    def forward(self, x: Tensor) -> Tensor:
        result_data = np.tanh(x.data)
        
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = "TanhBackward"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                tanh_grad = 1 - result_data**2
                grad = out.grad * tanh_grad
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out


class Softmax(ActivationFunction):
    """Softmax activation function."""
    
    def __init__(self, dim=-1):
        self.dim = dim
    
    def forward(self, x: Tensor) -> Tensor:
        # Numerical stability: subtract max
        x_max = np.max(x.data, axis=self.dim, keepdims=True)
        exp_data = np.exp(x.data - x_max)
        sum_exp = np.sum(exp_data, axis=self.dim, keepdims=True)
        result_data = exp_data / sum_exp
        
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = f"SoftmaxBackward(dim={self.dim})"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                # Softmax gradient: s * (grad - sum(s * grad))
                s_dot_grad = result_data * out.grad
                sum_s_dot_grad = np.sum(s_dot_grad, axis=self.dim, keepdims=True)
                grad = result_data * (out.grad - sum_s_dot_grad)
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out


class GELU(ActivationFunction):
    """Gaussian Error Linear Unit activation function."""
    
    def forward(self, x: Tensor) -> Tensor:
        # GELU approximation: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
        sqrt_2_over_pi = np.sqrt(2 / np.pi)
        tanh_arg = sqrt_2_over_pi * (x.data + 0.044715 * x.data**3)
        result_data = 0.5 * x.data * (1 + np.tanh(tanh_arg))
        
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = "GELUBackward"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                # Approximate GELU derivative
                tanh_term = np.tanh(tanh_arg)
                sech2_term = 1 - tanh_term**2
                grad_term = 0.5 * (1 + tanh_term) + 0.5 * x.data * sech2_term * sqrt_2_over_pi * (1 + 3 * 0.044715 * x.data**2)
                grad = out.grad * grad_term
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out


class LeakyReLU(ActivationFunction):
    """Leaky ReLU activation function."""
    
    def __init__(self, negative_slope=0.01):
        self.negative_slope = negative_slope
    
    def forward(self, x: Tensor) -> Tensor:
        result_data = np.where(x.data > 0, x.data, self.negative_slope * x.data)
        
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = f"LeakyReLUBackward(negative_slope={self.negative_slope})"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                grad = out.grad * np.where(x.data > 0, 1.0, self.negative_slope)
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out


# Functional interface
def relu(x: Tensor) -> Tensor:
    """Apply ReLU activation function."""
    return ReLU()(x)


def sigmoid(x: Tensor) -> Tensor:
    """Apply Sigmoid activation function."""
    return Sigmoid()(x)


def tanh(x: Tensor) -> Tensor:
    """Apply Tanh activation function."""
    return Tanh()(x)


def softmax(x: Tensor, dim=-1) -> Tensor:
    """Apply Softmax activation function."""
    return Softmax(dim)(x)


def gelu(x: Tensor) -> Tensor:
    """Apply GELU activation function."""
    return GELU()(x)


def leaky_relu(x: Tensor, negative_slope=0.01) -> Tensor:
    """Apply Leaky ReLU activation function."""
    return LeakyReLU(negative_slope)(x)


__all__ = [
    'ActivationFunction', 'ReLU', 'Sigmoid', 'Tanh', 'Softmax', 'GELU', 'LeakyReLU',
    'relu', 'sigmoid', 'tanh', 'softmax', 'gelu', 'leaky_relu'
]
