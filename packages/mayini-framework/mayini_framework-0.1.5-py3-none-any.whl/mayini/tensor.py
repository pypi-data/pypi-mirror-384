"""
Core Tensor class with automatic differentiation.
"""

import numpy as np
from typing import Union, List, Tuple, Optional, Set


class Tensor:
    """Enhanced Tensor class with complete automatic differentiation."""
    
    _tensor_id = 0  # Global tensor ID counter
    
    def __init__(
        self,
        data: Union[list, tuple, np.ndarray, float, int],
        requires_grad: bool = False,
        dtype: type = np.float32
    ):
        """Initialize tensor with data and gradient tracking."""
        # Convert input to numpy array
        if isinstance(data, (int, float)):
            self.data = np.array(data, dtype=dtype)
        else:
            self.data = np.array(data, dtype=dtype)
        
        # Gradient tracking
        self.requires_grad = requires_grad
        self.grad = None
        
        # Computational graph for backpropagation
        self._backward = None
        self.prev: Set['Tensor'] = set()
        self.op = ""
        
        # Metadata
        self.is_leaf = True
        self.id = Tensor._tensor_id
        Tensor._tensor_id += 1
    
    def __repr__(self) -> str:
        """String representation of tensor."""
        grad_str = f", grad_fn={self.op}" if self.op else ""
        requires_grad_str = f", requires_grad={self.requires_grad}" if self.requires_grad else ""
        
        if self.data.size <= 8:
            data_str = str(self.data.tolist())
        else:
            data_str = f"tensor of shape {self.shape}"
        
        return f"Tensor({data_str}{requires_grad_str}{grad_str})"
    
    # Properties
    @property
    def shape(self) -> tuple:
        return self.data.shape
    
    @property
    def ndim(self) -> int:
        return self.data.ndim
    
    @property
    def size(self) -> int:
        return self.data.size
    
    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype
    
    def _handle_broadcasting(self, grad, original_shape):
        """Handle gradient broadcasting for operations with different shapes."""
        # Sum over added dimensions
        ndims_added = grad.ndim - len(original_shape)
        for _ in range(ndims_added):
            grad = grad.sum(axis=0)
        
        # Sum over broadcasted dimensions
        for i, (dim_size, orig_size) in enumerate(zip(grad.shape, original_shape)):
            if orig_size == 1 and dim_size > 1:
                grad = grad.sum(axis=i, keepdims=True)
        
        return grad
    
    def __add__(self, other):
        """Element-wise addition with gradient support."""
        if not isinstance(other, Tensor):
            other = Tensor(other)
        
        result_data = self.data + other.data
        out = Tensor(result_data, requires_grad=(self.requires_grad or other.requires_grad))
        out.op = "AddBackward"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                grad = self._handle_broadcasting(out.grad, self.shape)
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
            
            if other.requires_grad:
                grad = self._handle_broadcasting(out.grad, other.shape)
                if other.grad is None:
                    other.grad = grad
                else:
                    other.grad = other.grad + grad
        
        out._backward = _backward
        out.prev = {self, other}
        return out
    
    def __mul__(self, other):
        """Element-wise multiplication with gradient support."""
        if not isinstance(other, Tensor):
            other = Tensor(other)
        
        result_data = self.data * other.data
        out = Tensor(result_data, requires_grad=(self.requires_grad or other.requires_grad))
        out.op = "MulBackward"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                grad = self._handle_broadcasting(other.data * out.grad, self.shape)
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
            
            if other.requires_grad:
                grad = self._handle_broadcasting(self.data * out.grad, other.shape)
                if other.grad is None:
                    other.grad = grad
                else:
                    other.grad = other.grad + grad
        
        out._backward = _backward
        out.prev = {self, other}
        return out
    
    def matmul(self, other):
        """Matrix multiplication with proper gradient computation."""
        if not isinstance(other, Tensor):
            other = Tensor(other)
        
        result_data = np.dot(self.data, other.data)
        out = Tensor(result_data, requires_grad=(self.requires_grad or other.requires_grad))
        out.op = "MatMulBackward"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                grad = np.dot(out.grad, other.data.T)
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
            
            if other.requires_grad:
                grad = np.dot(self.data.T, out.grad)
                if other.grad is None:
                    other.grad = grad
                else:
                    other.grad = other.grad + grad
        
        out._backward = _backward
        out.prev = {self, other}
        return out
    
    def __pow__(self, power):
        """Power operation with gradient support."""
        assert isinstance(power, (int, float))
        
        result_data = np.power(self.data, power)
        out = Tensor(result_data, requires_grad=self.requires_grad)
        out.op = f"PowBackward({power})"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                grad = power * np.power(self.data, power - 1) * out.grad
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
        
        out._backward = _backward
        out.prev = {self}
        return out
    
    def sum(self, axis=None, keepdims=False):
        """Sum operation with gradient support."""
        result_data = np.sum(self.data, axis=axis, keepdims=keepdims)
        out = Tensor(result_data, requires_grad=self.requires_grad)
        out.op = f"SumBackward(axis={axis})"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                grad = out.grad
                
                if axis is not None:
                    if isinstance(axis, int):
                        axes = (axis,)
                    else:
                        axes = axis
                    
                    if not keepdims:
                        for ax in sorted(axes):
                            grad = np.expand_dims(grad, ax)
                
                grad = np.broadcast_to(grad, self.data.shape)
                
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
        
        out._backward = _backward
        out.prev = {self}
        return out
    
    def mean(self, axis=None, keepdims=False):
        """Mean operation with gradient support."""
        if axis is None:
            n = self.data.size
        else:
            if isinstance(axis, int):
                n = self.data.shape[axis]
            else:
                n = np.prod([self.data.shape[i] for i in axis])
        
        return self.sum(axis=axis, keepdims=keepdims) / n
    
    def reshape(self, shape):
        """Reshape operation with gradient support."""
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            shape = shape[0]
        
        result_data = self.data.reshape(shape)
        out = Tensor(result_data, requires_grad=self.requires_grad)
        out.op = f"ReshapeBackward({shape})"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                grad = out.grad.reshape(self.data.shape)
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
        
        out._backward = _backward
        out.prev = {self}
        return out
    
    def transpose(self, axes=None):
        """Transpose tensor dimensions."""
        result_data = np.transpose(self.data, axes)
        out = Tensor(result_data, requires_grad=self.requires_grad)
        out.op = "TransposeBackward"
        out.is_leaf = False
        
        def _backward():
            if self.requires_grad:
                # Reverse the transpose for gradient
                if axes:
                    # Create reverse permutation
                    reverse_axes = [0] * len(axes)
                    for i, ax in enumerate(axes):
                        reverse_axes[ax] = i
                    grad = np.transpose(out.grad, reverse_axes)
                else:
                    grad = np.transpose(out.grad)
                
                if self.grad is None:
                    self.grad = grad
                else:
                    self.grad = self.grad + grad
        
        out._backward = _backward
        out.prev = {self}
        return out
    
    def backward(self, gradient=None):
        """Enhanced backpropagation with cycle detection."""
        if gradient is None:
            if self.data.size == 1:
                gradient = np.ones_like(self.data)
            else:
                raise RuntimeError("gradient can only be implicitly created for scalar outputs")
        
        self.grad = gradient
        
        # Topological sort with cycle detection
        topo_order = []
        visited = set()
        rec_stack = set()
        
        def build_topo(node):
            if node.id in rec_stack:
                raise RuntimeError("Cycle detected in computational graph")
            
            if node.id not in visited:
                visited.add(node.id)
                rec_stack.add(node.id)
                
                for child in node.prev:
                    build_topo(child)
                
                rec_stack.remove(node.id)
                topo_order.append(node)
        
        build_topo(self)
        
        # Apply chain rule
        for node in reversed(topo_order):
            if node._backward:
                node._backward()
    
    def zero_grad(self):
        """Zero the gradient."""
        self.grad = None
    
    def detach(self):
        """Detach from computational graph."""
        return Tensor(self.data.copy(), requires_grad=False)
    
    def numpy(self):
        """Convert to numpy array."""
        return self.data.copy()
    
    def item(self):
        """Get scalar value."""
        if self.data.size != 1:
            raise ValueError("item() can only be called on single-element tensors")
        return self.data.item()
    
    # Convenience methods
    def __neg__(self):
        return self * Tensor(-1.0)
    
    def __sub__(self, other):
        return self + (-other if isinstance(other, Tensor) else Tensor(-other))
    
    def __truediv__(self, other):
        if isinstance(other, Tensor):
            return self * (other ** -1)
        else:
            return self * (1.0 / other)
    
    def __radd__(self, other):
        return Tensor(other) + self
    
    def __rmul__(self, other):
        return Tensor(other) * self
