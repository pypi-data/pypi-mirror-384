# Create the missing losses.py file
losses_py_content = '''"""
Loss functions for training neural networks.
"""

import numpy as np
from abc import ABC, abstractmethod
from ..tensor import Tensor

class LossFunction(ABC):
    """Base class for loss functions."""
    
    def __init__(self, reduction='mean'):
        """
        Initialize loss function.
        
        Args:
            reduction (str): Reduction type - 'mean', 'sum', or 'none'
        """
        if reduction not in ['mean', 'sum', 'none']:
            raise ValueError(f"Invalid reduction '{reduction}'. Must be 'mean', 'sum', or 'none'")
        self.reduction = reduction
    
    @abstractmethod
    def forward(self, predictions: Tensor, targets: Tensor) -> Tensor:
        pass
    
    def __call__(self, predictions: Tensor, targets: Tensor) -> Tensor:
        return self.forward(predictions, targets)
    
    def _apply_reduction(self, loss_tensor: Tensor) -> Tensor:
        """Apply reduction to loss tensor."""
        if self.reduction == 'mean':
            return loss_tensor.mean()
        elif self.reduction == 'sum':
            return loss_tensor.sum()
        else:  # 'none'
            return loss_tensor

class MSELoss(LossFunction):
    """Mean Squared Error Loss."""
    
    def forward(self, predictions: Tensor, targets: Tensor) -> Tensor:
        if not isinstance(targets, Tensor):
            targets = Tensor(targets)
        
        diff = predictions - targets
        loss = diff * diff
        return self._apply_reduction(loss)

class MAELoss(LossFunction):
    """Mean Absolute Error Loss."""
    
    def forward(self, predictions: Tensor, targets: Tensor) -> Tensor:
        if not isinstance(targets, Tensor):
            targets = Tensor(targets)
        
        diff = predictions - targets
        # Implement absolute value with gradient
        abs_diff_data = np.abs(diff.data)
        out = Tensor(abs_diff_data, requires_grad=diff.requires_grad)
        out.op = "AbsBackward"
        out.is_leaf = False
        
        def _backward():
            if diff.requires_grad and out.grad is not None:
                sign_grad = np.sign(diff.data)
                grad = out.grad * sign_grad
                if diff.grad is None:
                    diff.grad = grad
                else:
                    diff.grad = diff.grad + grad
        
        out._backward = _backward
        out.prev = {diff}
        
        return self._apply_reduction(out)

class CrossEntropyLoss(LossFunction):
    """Cross Entropy Loss for classification."""
    
    def forward(self, predictions: Tensor, targets: Tensor) -> Tensor:
        if not isinstance(targets, Tensor):
            targets = Tensor(targets)
        
        # Apply softmax to predictions for numerical stability
        pred_max = np.max(predictions.data, axis=1, keepdims=True)
        exp_pred = np.exp(predictions.data - pred_max)
        sum_exp = np.sum(exp_pred, axis=1, keepdims=True)
        log_softmax = (predictions.data - pred_max) - np.log(sum_exp)
        
        # Compute cross entropy
        if targets.data.ndim == 1:  # Class indices
            batch_size = predictions.data.shape[0]
            loss_data = -log_softmax[np.arange(batch_size), targets.data.astype(int)]
        else:  # One-hot encoded
            loss_data = -np.sum(targets.data * log_softmax, axis=1)
        
        out = Tensor(loss_data, requires_grad=predictions.requires_grad)
        out.op = "CrossEntropyBackward"
        out.is_leaf = False
        
        def _backward():
            if predictions.requires_grad and out.grad is not None:
                batch_size = predictions.data.shape[0]
                softmax_pred = exp_pred / sum_exp
                
                if targets.data.ndim == 1:  # Class indices
                    grad = softmax_pred.copy()
                    grad[np.arange(batch_size), targets.data.astype(int)] -= 1
                else:  # One-hot encoded
                    grad = softmax_pred - targets.data
                
                # Apply chain rule
                if out.grad.ndim == 0:
                    grad = grad * out.grad
                else:
                    grad = grad * out.grad.reshape(-1, 1)
                
                if predictions.grad is None:
                    predictions.grad = grad
                else:
                    predictions.grad = predictions.grad + grad
        
        out._backward = _backward
        out.prev = {predictions}
        
        return self._apply_reduction(out)

class BCELoss(LossFunction):
    """Binary Cross Entropy Loss."""
    
    def forward(self, predictions: Tensor, targets: Tensor) -> Tensor:
        if not isinstance(targets, Tensor):
            targets = Tensor(targets)
        
        # Clamp predictions for numerical stability
        eps = 1e-7
        pred_clamped = np.clip(predictions.data, eps, 1 - eps)
        
        loss_data = -(targets.data * np.log(pred_clamped) + 
                     (1 - targets.data) * np.log(1 - pred_clamped))
        
        out = Tensor(loss_data, requires_grad=predictions.requires_grad)
        out.op = "BCEBackward"
        out.is_leaf = False
        
        def _backward():
            if predictions.requires_grad and out.grad is not None:
                # BCE gradient: (pred - target) / (pred * (1 - pred))
                grad = (pred_clamped - targets.data) / (pred_clamped * (1 - pred_clamped))
                
                if out.grad.ndim == 0:
                    grad = grad * out.grad
                else:
                    grad = grad * out.grad
                
                if predictions.grad is None:
                    predictions.grad = grad
                else:
                    predictions.grad = predictions.grad + grad
        
        out._backward = _backward
        out.prev = {predictions}
        
        return self._apply_reduction(out)

class HuberLoss(LossFunction):
    """Huber Loss (smooth L1 loss)."""
    
    def __init__(self, delta=1.0, reduction='mean'):
        super().__init__(reduction)
        self.delta = delta
    
    def forward(self, predictions: Tensor, targets: Tensor) -> Tensor:
        if not isinstance(targets, Tensor):
            targets = Tensor(targets)
        
        diff = predictions - targets
        abs_diff = np.abs(diff.data)
        
        # Huber loss: 0.5 * diff^2 if |diff| <= delta, else delta * (|diff| - 0.5 * delta)
        loss_data = np.where(
            abs_diff <= self.delta,
            0.5 * diff.data**2,
            self.delta * (abs_diff - 0.5 * self.delta)
        )
        
        out = Tensor(loss_data, requires_grad=diff.requires_grad)
        out.op = f"HuberBackward(delta={self.delta})"
        out.is_leaf = False
        
        def _backward():
            if diff.requires_grad and out.grad is not None:
                # Huber gradient: diff if |diff| <= delta, else delta * sign(diff)
                grad = np.where(
                    abs_diff <= self.delta,
                    diff.data,
                    self.delta * np.sign(diff.data)
                )
                
                if out.grad.ndim == 0:
                    grad = grad * out.grad
                else:
                    grad = grad * out.grad
                
                if diff.grad is None:
                    diff.grad = grad
                else:
                    diff.grad = diff.grad + grad
        
        out._backward = _backward
        out.prev = {diff}
        
        return self._apply_reduction(out)

__all__ = ['LossFunction', 'MSELoss', 'MAELoss', 'CrossEntropyLoss', 'BCELoss', 'HuberLoss']
'''

print("✅ Created missing losses.py")
print(f"Length: {len(losses_py_content)} characters")
print("- Complete loss functions with proper gradients")
print("- Support for different reduction modes")
print("- Numerical stability improvements")

# Now create a complete installation guide
installation_guide = '''
# MAYINI Framework - Complete Installation Fix

## Issues Found and Fixed:

### 1. **TOML Syntax Errors**
- Fixed regex escaping in pyproject.toml
- Corrected string formatting issues
- Added proper dependency version bounds

### 2. **Configuration Conflicts**
- Simplified setup.py to defer to pyproject.toml
- Eliminated dual configuration conflicts
- Used modern Python packaging standards

### 3. **Missing Dependencies**
- Added proper version bounds for all dependencies
- Included development and testing dependencies
- Added optional dependency groups

### 4. **Package Discovery Issues**
- Fixed package discovery settings
- Added proper include/exclude patterns
- Ensured all __init__.py files are present

## Installation Steps:

1. **Replace Configuration Files:**
   - Replace setup.py with the debugged minimal version
   - Replace pyproject.toml with the corrected version
   - Add missing activations.py and losses.py files

2. **Build and Test:**
   ```bash
   # Clean previous builds
   rm -rf build/ dist/ *.egg-info/
   
   # Install in development mode
   pip install -e .
   
   # Run tests
   python -c "import mayini; print('✅ Import successful')"
   ```

3. **Publish to PyPI:**
   ```bash
   # Build distributions
   python -m build
   
   # Upload to PyPI
   python -m twine upload dist/*
   ```

## Key Improvements:

✅ **Modern Python Support**: Updated to Python 3.8+
✅ **Proper Version Bounds**: Added upper bounds for stability
✅ **Development Tools**: Added comprehensive dev dependencies
✅ **Testing Framework**: Configured pytest with coverage
✅ **Code Quality**: Added black, ruff, mypy configurations
✅ **Documentation**: Ready for Sphinx documentation

The framework should now install and import without errors!
'''

print("\n" + "="*60)
print("COMPLETE INSTALLATION GUIDE")
print("="*60)
print(installation_guide)
