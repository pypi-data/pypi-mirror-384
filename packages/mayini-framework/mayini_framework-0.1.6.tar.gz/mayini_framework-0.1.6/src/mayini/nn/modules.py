"""
Neural network modules and layers.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from ..tensor import Tensor


# Helper functions for CNN
def im2col_fixed(input_data: np.ndarray, kernel_h: int, kernel_w: int,
                stride: int = 1, padding: int = 0) -> np.ndarray:
    """Optimized im2col transformation for efficient convolution."""
    N, C, H, W = input_data.shape
    
    # Calculate output dimensions
    out_h = (H + 2*padding - kernel_h) // stride + 1
    out_w = (W + 2*padding - kernel_w) // stride + 1
    
    # Add padding
    if padding > 0:
        img = np.pad(input_data, ((0, 0), (0, 0), (padding, padding), (padding, padding)),
                    mode='constant', constant_values=0)
    else:
        img = input_data
    
    # Create column matrix with proper shape
    col = np.zeros((N, C, kernel_h, kernel_w, out_h, out_w), dtype=input_data.dtype)
    
    # Extract patches efficiently
    for j in range(kernel_h):
        j_lim = j + stride * out_h
        for i in range(kernel_w):
            i_lim = i + stride * out_w
            col[:, :, j, i, :, :] = img[:, :, j:j_lim:stride, i:i_lim:stride]
    
    # Reshape to column format: (N*out_h*out_w, C*kernel_h*kernel_w)
    col = col.transpose(0, 4, 5, 1, 2, 3).reshape(N * out_h * out_w, -1)
    return col


def col2im_fixed(col: np.ndarray, input_shape: tuple, kernel_h: int, kernel_w: int,
                stride: int = 1, padding: int = 0) -> np.ndarray:
    """Convert column matrix back to image format."""
    N, C, H, W = input_shape
    out_h = (H + 2*padding - kernel_h) // stride + 1
    out_w = (W + 2*padding - kernel_w) // stride + 1
    
    # Reshape column back to tensor format
    col = col.reshape(N, out_h, out_w, C, kernel_h, kernel_w).transpose(0, 3, 4, 5, 1, 2)
    
    # Create padded image for accumulation
    img = np.zeros((N, C, H + 2*padding*stride - 1, W + 2*padding*stride - 1),
                   dtype=col.dtype)
    
    # Accumulate gradients
    for j in range(kernel_h):
        j_lim = j + stride * out_h
        for i in range(kernel_w):
            i_lim = i + stride * out_w
            img[:, :, j:j_lim:stride, i:i_lim:stride] += col[:, :, j, i, :, :]
    
    # Remove padding
    return img[:, :, padding:H + padding, padding:W + padding]


# Base classes
class Module(ABC):
    """Base class for all neural network modules."""
    
    def __init__(self):
        self._parameters = []
        self._modules = []
        self.training = True
    
    @abstractmethod
    def forward(self, x: Tensor) -> Tensor:
        """Forward pass - must be implemented by subclasses."""
        pass
    
    def __call__(self, x: Tensor) -> Tensor:
        return self.forward(x)
    
    def parameters(self) -> List[Tensor]:
        """Return all parameters in this module and submodules."""
        params = self._parameters.copy()
        for module in self._modules:
            params.extend(module.parameters())
        return params
    
    def zero_grad(self):
        """Zero all parameter gradients."""
        for param in self.parameters():
            param.zero_grad()
    
    def train(self, mode: bool = True):
        """Set training mode."""
        self.training = mode
        for module in self._modules:
            module.train(mode)
        return self
    
    def eval(self):
        """Set evaluation mode."""
        return self.train(False)
    
    def add_module(self, name: str, module: 'Module'):
        """Add a submodule."""
        self._modules.append(module)
        setattr(self, name, module)


class Sequential(Module):
    """Sequential container for modules."""
    
    def __init__(self, *modules):
        super().__init__()
        self._modules = list(modules)
    
    def forward(self, x: Tensor) -> Tensor:
        for module in self._modules:
            x = module(x)
        return x
    
    def __getitem__(self, idx):
        return self._modules[idx]
    
    def __len__(self):
        return len(self._modules)
    
    def append(self, module):
        self._modules.append(module)
    
    def __repr__(self):
        lines = []
        for i, module in enumerate(self._modules):
            lines.append(f"  ({i}): {module}")
        return f"Sequential(\n{chr(10).join(lines)}\n)"


# Core neural network layers
class Linear(Module):
    """Linear (Dense) layer with multiple initialization methods."""
    
    def __init__(self, in_features: int, out_features: int, bias: bool = True,
                 init_method: str = "xavier"):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.use_bias = bias
        
        # Initialize weights based on method
        if init_method == "xavier":
            limit = np.sqrt(6.0 / (in_features + out_features))
            weight_data = np.random.uniform(-limit, limit, (out_features, in_features))
        elif init_method == "he":
            std = np.sqrt(2.0 / in_features)
            weight_data = np.random.normal(0, std, (out_features, in_features))
        elif init_method == "normal":
            weight_data = np.random.normal(0, 0.01, (out_features, in_features))
        else:
            raise ValueError(f"Unknown initialization method: {init_method}")
        
        self.weight = Tensor(weight_data.astype(np.float32), requires_grad=True)
        self._parameters.append(self.weight)
        
        if bias:
            bias_data = np.zeros(out_features, dtype=np.float32)
            self.bias = Tensor(bias_data, requires_grad=True)
            self._parameters.append(self.bias)
        else:
            self.bias = None
    
    def forward(self, x: Tensor) -> Tensor:
        """Forward pass: y = x*W^T + b"""
        # Transpose weight to get (in_features, out_features)
        weight_t = Tensor(self.weight.data.T, requires_grad=self.weight.requires_grad)
        weight_t.op = "TransposeBackward"
        weight_t.is_leaf = False
        
        def weight_backward():
            if self.weight.requires_grad and weight_t.grad is not None:
                if self.weight.grad is None:
                    self.weight.grad = weight_t.grad.T
                else:
                    self.weight.grad = self.weight.grad + weight_t.grad.T
        
        weight_t._backward = weight_backward
        weight_t.prev = {self.weight}
        
        # Matrix multiplication x @ weight_t
        output = x.matmul(weight_t)
        
        if self.bias is not None:
            # Broadcast bias across batch dimension
            output = output + self.bias
        
        return output
    
    def __repr__(self):
        return (f"Linear(in_features={self.in_features}, "
                f"out_features={self.out_features}, bias={self.use_bias})")


class Conv2D(Module):
    """2D Convolutional layer with im2col optimization."""
    
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int,
                 stride: int = 1, padding: int = 0, bias: bool = True):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.use_bias = bias
        
        # Xavier initialization for conv weights
        fan_in = in_channels * kernel_size * kernel_size
        fan_out = out_channels * kernel_size * kernel_size
        limit = np.sqrt(6.0 / (fan_in + fan_out))
        
        weight_shape = (out_channels, in_channels, kernel_size, kernel_size)
        weight_data = np.random.uniform(-limit, limit, weight_shape).astype(np.float32)
        
        self.weight = Tensor(weight_data, requires_grad=True)
        self._parameters.append(self.weight)
        
        if bias:
            bias_data = np.zeros(out_channels, dtype=np.float32)
            self.bias = Tensor(bias_data, requires_grad=True)
            self._parameters.append(self.bias)
        else:
            self.bias = None
    
    def forward(self, x: Tensor) -> Tensor:
        """Forward pass using im2col for efficiency."""
        # Input validation
        if x.data.ndim != 4:
            raise ValueError(f"Conv2D expects 4D input (N,C,H,W), got {x.data.ndim}D")
        
        N, C, H, W = x.shape
        
        if C != self.in_channels:
            raise ValueError(f"Expected {self.in_channels} input channels, got {C}")
        
        # Calculate output dimensions
        out_h = (H + 2*self.padding - self.kernel_size) // self.stride + 1
        out_w = (W + 2*self.padding - self.kernel_size) // self.stride + 1
        
        if out_h <= 0 or out_w <= 0:
            raise ValueError(f"Invalid output size ({out_h}, {out_w}). Check padding/stride.")
        
        # Im2col transformation
        col = im2col_fixed(x.data, self.kernel_size, self.kernel_size,
                          self.stride, self.padding)
        col_tensor = Tensor(col, requires_grad=x.requires_grad)
        
        # Reshape weights for matrix multiplication
        weight_reshaped = self.weight.reshape((self.out_channels, -1))
        
        # Matrix multiplication
        output = weight_reshaped.matmul(col_tensor.transpose())
        
        # Add bias if present
        if self.bias is not None:
            bias_reshaped = self.bias.reshape((-1, 1))
            output = output + bias_reshaped
        
        # Reshape to proper output format (N, out_channels, out_h, out_w)
        output = output.reshape((self.out_channels, N, out_h, out_w))
        output = output.transpose((1, 0, 2, 3))  # (N, out_channels, out_h, out_w)
        
        return output
    
    def __repr__(self):
        return (f"Conv2D(in_channels={self.in_channels}, out_channels={self.out_channels}, "
                f"kernel_size={self.kernel_size}, stride={self.stride}, "
                f"padding={self.padding}, bias={self.use_bias})")


class MaxPool2D(Module):
    """2D Max pooling layer."""
    
    def __init__(self, kernel_size: int, stride: Optional[int] = None, padding: int = 0):
        super().__init__()
        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size
        self.padding = padding
    
    def forward(self, x: Tensor) -> Tensor:
        """Forward pass with max pooling."""
        if x.data.ndim != 4:
            raise ValueError(f"MaxPool2D expects 4D input (N,C,H,W), got {x.data.ndim}D")
        
        N, C, H, W = x.shape
        
        # Calculate output dimensions
        out_h = (H + 2*self.padding - self.kernel_size) // self.stride + 1
        out_w = (W + 2*self.padding - self.kernel_size) // self.stride + 1
        
        if out_h <= 0 or out_w <= 0:
            raise ValueError(f"Invalid output size ({out_h}, {out_w})")
        
        # Perform max pooling
        output_data = np.zeros((N, C, out_h, out_w), dtype=x.data.dtype)
        
        # Apply padding if needed
        if self.padding > 0:
            x_padded = np.pad(x.data, ((0, 0), (0, 0), (self.padding, self.padding),
                                     (self.padding, self.padding)), 
                            mode='constant', constant_values=-np.inf)
        else:
            x_padded = x.data
        
        for n in range(N):
            for c in range(C):
                for h in range(out_h):
                    for w in range(out_w):
                        h_start = h * self.stride
                        h_end = h_start + self.kernel_size
                        w_start = w * self.stride
                        w_end = w_start + self.kernel_size
                        
                        pool_region = x_padded[n, c, h_start:h_end, w_start:w_end]
                        output_data[n, c, h, w] = np.max(pool_region)
        
        out = Tensor(output_data, requires_grad=x.requires_grad)
        out.op = "MaxPool2DBackward"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                grad_input = np.zeros_like(x.data)
                
                # Simplified gradient computation
                for n in range(N):
                    for c in range(C):
                        for h in range(out_h):
                            for w in range(out_w):
                                h_start = h * self.stride
                                h_end = min(h_start + self.kernel_size, H)
                                w_start = w * self.stride
                                w_end = min(w_start + self.kernel_size, W)
                                
                                pool_region = x.data[n, c, h_start:h_end, w_start:w_end]
                                max_idx = np.unravel_index(np.argmax(pool_region), pool_region.shape)
                                
                                grad_input[n, c, h_start + max_idx[0], w_start + max_idx[1]] += \
                                    out.grad[n, c, h, w]
                
                if x.grad is None:
                    x.grad = grad_input
                else:
                    x.grad = x.grad + grad_input
        
        out._backward = _backward
        out.prev = {x}
        return out
    
    def __repr__(self):
        return (f"MaxPool2D(kernel_size={self.kernel_size}, stride={self.stride}, "
                f"padding={self.padding})")


class AvgPool2D(Module):
    """2D Average pooling layer."""
    
    def __init__(self, kernel_size: int, stride: Optional[int] = None, padding: int = 0):
        super().__init__()
        self.kernel_size = kernel_size
        self.stride = stride if stride is not None else kernel_size
        self.padding = padding
    
    def forward(self, x: Tensor) -> Tensor:
        """Forward pass with average pooling."""
        if x.data.ndim != 4:
            raise ValueError(f"AvgPool2D expects 4D input (N,C,H,W), got {x.data.ndim}D")
        
        N, C, H, W = x.shape
        
        # Calculate output dimensions
        out_h = (H + 2*self.padding - self.kernel_size) // self.stride + 1
        out_w = (W + 2*self.padding - self.kernel_size) // self.stride + 1
        
        if out_h <= 0 or out_w <= 0:
            raise ValueError(f"Invalid output size ({out_h}, {out_w})")
        
        output_data = np.zeros((N, C, out_h, out_w), dtype=x.data.dtype)
        
        # Apply padding if needed
        if self.padding > 0:
            x_padded = np.pad(x.data, ((0, 0), (0, 0), (self.padding, self.padding),
                                     (self.padding, self.padding)), 
                            mode='constant', constant_values=0)
        else:
            x_padded = x.data
        
        # Perform average pooling
        for n in range(N):
            for c in range(C):
                for h in range(out_h):
                    for w in range(out_w):
                        h_start = h * self.stride
                        h_end = h_start + self.kernel_size
                        w_start = w * self.stride
                        w_end = w_start + self.kernel_size
                        
                        pool_region = x_padded[n, c, h_start:h_end, w_start:w_end]
                        output_data[n, c, h, w] = np.mean(pool_region)
        
        out = Tensor(output_data, requires_grad=x.requires_grad)
        out.op = "AvgPool2DBackward"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                grad_input = np.zeros_like(x.data)
                pool_size = self.kernel_size * self.kernel_size
                
                for n in range(N):
                    for c in range(C):
                        for h in range(out_h):
                            for w in range(out_w):
                                h_start = h * self.stride
                                h_end = min(h_start + self.kernel_size, H)
                                w_start = w * self.stride
                                w_end = min(w_start + self.kernel_size, W)
                                
                                grad_input[n, c, h_start:h_end, w_start:w_end] += \
                                    out.grad[n, c, h, w] / pool_size
                
                if x.grad is None:
                    x.grad = grad_input
                else:
                    x.grad = x.grad + grad_input
        
        out._backward = _backward
        out.prev = {x}
        return out
    
    def __repr__(self):
        return (f"AvgPool2D(kernel_size={self.kernel_size}, stride={self.stride}, "
                f"padding={self.padding})")


class Dropout(Module):
    """Dropout regularization layer."""
    
    def __init__(self, p: float = 0.5):
        super().__init__()
        if not (0.0 <= p <= 1.0):
            raise ValueError(f"Dropout probability must be between 0 and 1, got {p}")
        self.p = p
    
    def forward(self, x: Tensor) -> Tensor:
        if not self.training:
            return x
        
        # Inverted dropout for training efficiency
        keep_prob = 1.0 - self.p
        
        # Ensure mask shape exactly matches input shape
        mask = (np.random.rand(*x.data.shape) < keep_prob).astype(np.float32)
        
        # Scale by 1/keep_prob to maintain expected value
        result_data = x.data * mask / keep_prob
        
        out = Tensor(result_data, requires_grad=x.requires_grad)
        out.op = f"DropoutBackward(p={self.p})"
        out.is_leaf = False
        
        def _backward():
            if x.requires_grad and out.grad is not None:
                grad = out.grad * mask / keep_prob
                if x.grad is None:
                    x.grad = grad
                else:
                    x.grad = x.grad + grad
        
        out._backward = _backward
        out.prev = {x}
        return out
    
    def __repr__(self):
        return f"Dropout(p={self.p})"


class BatchNorm1d(Module):
    """1D Batch Normalization layer."""
    
    def __init__(self, num_features: int, eps: float = 1e-5, momentum: float = 0.1):
        super().__init__()
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        
        # Learnable parameters
        self.gamma = Tensor(np.ones(num_features, dtype=np.float32), requires_grad=True)
        self.beta = Tensor(np.zeros(num_features, dtype=np.float32), requires_grad=True)
        self._parameters.extend([self.gamma, self.beta])
        
        # Running statistics (not learnable)
        self.running_mean = np.zeros(num_features, dtype=np.float32)
        self.running_var = np.ones(num_features, dtype=np.float32)
    
    def forward(self, x: Tensor) -> Tensor:
        # Handle batch dimension properly
        if x.data.ndim != 2:
            raise ValueError(f"BatchNorm1d expects 2D input (batch_size, features), got {x.data.ndim}D")
        
        batch_size, features = x.data.shape
        if features != self.num_features:
            raise ValueError(f"Expected {self.num_features} features, got {features}")
        
        if self.training:
            # Training mode: use batch statistics
            batch_mean = np.mean(x.data, axis=0, keepdims=False)  # Shape: (features,)
            batch_var = np.var(x.data, axis=0, keepdims=False)   # Shape: (features,)
            
            # Update running statistics
            self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * batch_mean
            self.running_var = (1 - self.momentum) * self.running_var + self.momentum * batch_var
            
            mean, var = batch_mean, batch_var
        else:
            # Evaluation mode: use running statistics
            mean, var = self.running_mean, self.running_var
        
        # Normalize - Fix: Ensure proper broadcasting
        x_norm_data = (x.data - mean[np.newaxis, :]) / np.sqrt(var[np.newaxis, :] + self.eps)
        x_norm = Tensor(x_norm_data, requires_grad=x.requires_grad)
        x_norm.op = "BatchNormBackward"
        x_norm.is_leaf = False
        
        # Add backward pass for batch norm
        def _backward():
            if x.requires_grad and x_norm.grad is not None:
                # Simplified gradient computation for educational purposes
                batch_size = x.data.shape[0]
                std = np.sqrt(var + self.eps)
                
                # Gradient w.r.t. normalized input
                grad_x_norm = x_norm.grad
                
                # Gradient w.r.t. variance
                grad_var = np.sum(grad_x_norm * (x.data - mean[np.newaxis, :]) * 
                                 (-0.5) * (var[np.newaxis, :] + self.eps)**(-1.5), axis=0)
                
                # Gradient w.r.t. mean
                grad_mean = (np.sum(grad_x_norm * (-1.0 / std[np.newaxis, :]), axis=0) + 
                           grad_var * np.sum(-2.0 * (x.data - mean[np.newaxis, :]), axis=0) / batch_size)
                
                # Gradient w.r.t. input
                grad_x = (grad_x_norm / std[np.newaxis, :] + 
                         grad_var[np.newaxis, :] * 2.0 * (x.data - mean[np.newaxis, :]) / batch_size + 
                         grad_mean[np.newaxis, :] / batch_size)
                
                if x.grad is None:
                    x.grad = grad_x
                else:
                    x.grad = x.grad + grad_x
        
        x_norm._backward = _backward
        x_norm.prev = {x}
        
        # Scale and shift
        output = x_norm * self.gamma + self.beta
        
        return output
    
    def __repr__(self):
        return (f"BatchNorm1d(num_features={self.num_features}, "
                f"eps={self.eps}, momentum={self.momentum})")


class Flatten(Module):
    """Flatten layer to convert from 2D/3D/4D to 2D."""
    
    def __init__(self, start_dim: int = 1):
        super().__init__()
        self.start_dim = start_dim
    
    def forward(self, x: Tensor) -> Tensor:
        if x.data.ndim <= 2:
            return x
        
        # Flatten dimensions from start_dim onwards
        batch_size = x.data.shape[0]
        flat_size = np.prod(x.data.shape[self.start_dim:])
        
        return x.reshape((batch_size, flat_size))
    
    def __repr__(self):
        return f"Flatten(start_dim={self.start_dim})"
