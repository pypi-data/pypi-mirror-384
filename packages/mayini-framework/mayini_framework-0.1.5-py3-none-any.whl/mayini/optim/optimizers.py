"""
Optimization algorithms for training neural networks.
"""

import numpy as np
import math
from abc import ABC, abstractmethod
from typing import List
from ..tensor import Tensor


class Optimizer(ABC):
    """Base class for all optimizers."""
    
    def __init__(self, parameters: List[Tensor], lr: float):
        self.parameters = parameters
        self.lr = lr
        self.step_count = 0
    
    @abstractmethod
    def step(self):
        """Perform one optimization step."""
        pass
    
    def zero_grad(self):
        """Zero all parameter gradients."""
        for param in self.parameters:
            param.zero_grad()
    
    def __repr__(self):
        return f"{self.__class__.__name__}(lr={self.lr})"


class SGD(Optimizer):
    """Stochastic Gradient Descent with momentum and weight decay."""
    
    def __init__(self, parameters: List[Tensor], lr: float = 0.01,
                 momentum: float = 0.0, weight_decay: float = 0.0):
        super().__init__(parameters, lr)
        self.momentum = momentum
        self.weight_decay = weight_decay
        self.velocity = [np.zeros_like(param.data) for param in self.parameters]
    
    def step(self):
        """Perform SGD optimization step with momentum."""
        for i, param in enumerate(self.parameters):
            if param.grad is None:
                continue
            
            grad = param.grad.copy()
            
            # Add weight decay
            if self.weight_decay != 0:
                grad += self.weight_decay * param.data
            
            # Apply momentum
            if self.momentum != 0:
                self.velocity[i] = self.momentum * self.velocity[i] + grad
                grad = self.velocity[i]
            
            # Update parameters
            param.data -= self.lr * grad
        
        self.step_count += 1
    
    def __repr__(self):
        return f"SGD(lr={self.lr}, momentum={self.momentum}, weight_decay={self.weight_decay})"


class Adam(Optimizer):
    """Adam optimizer with bias correction."""
    
    def __init__(self, parameters: List[Tensor], lr: float = 0.001,
                 beta1: float = 0.9, beta2: float = 0.999,
                 eps: float = 1e-8, weight_decay: float = 0.0):
        super().__init__(parameters, lr)
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        
        # Initialize moment estimates
        self.m = [np.zeros_like(param.data) for param in self.parameters]
        self.v = [np.zeros_like(param.data) for param in self.parameters]
    
    def step(self):
        """Perform Adam optimization step with bias correction."""
        self.step_count += 1
        
        for i, param in enumerate(self.parameters):
            if param.grad is None:
                continue
            
            grad = param.grad.copy()
            
            # Add weight decay
            if self.weight_decay != 0:
                grad += self.weight_decay * param.data
            
            # Update biased first moment estimate
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
            
            # Update biased second raw moment estimate
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)
            
            # Compute bias-corrected first moment estimate
            m_hat = self.m[i] / (1 - self.beta1 ** self.step_count)
            
            # Compute bias-corrected second raw moment estimate
            v_hat = self.v[i] / (1 - self.beta2 ** self.step_count)
            
            # Update parameters
            param.data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
    
    def __repr__(self):
        return (f"Adam(lr={self.lr}, beta1={self.beta1}, beta2={self.beta2}, "
                f"eps={self.eps}, weight_decay={self.weight_decay})")


class AdamW(Optimizer):
    """AdamW optimizer with decoupled weight decay."""
    
    def __init__(self, parameters: List[Tensor], lr: float = 0.001,
                 beta1: float = 0.9, beta2: float = 0.999,
                 eps: float = 1e-8, weight_decay: float = 0.01):
        super().__init__(parameters, lr)
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.weight_decay = weight_decay
        
        # Initialize moment estimates
        self.m = [np.zeros_like(param.data) for param in self.parameters]
        self.v = [np.zeros_like(param.data) for param in self.parameters]
    
    def step(self):
        """Perform AdamW optimization step with decoupled weight decay."""
        self.step_count += 1
        
        for i, param in enumerate(self.parameters):
            if param.grad is None:
                continue
            
            grad = param.grad.copy()
            
            # Update biased first moment estimate
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
            
            # Update biased second raw moment estimate
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)
            
            # Compute bias-corrected first moment estimate
            m_hat = self.m[i] / (1 - self.beta1 ** self.step_count)
            
            # Compute bias-corrected second raw moment estimate
            v_hat = self.v[i] / (1 - self.beta2 ** self.step_count)
            
            # Update parameters with Adam step
            param.data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
            
            # Apply decoupled weight decay
            if self.weight_decay != 0:
                param.data -= self.lr * self.weight_decay * param.data
    
    def __repr__(self):
        return (f"AdamW(lr={self.lr}, beta1={self.beta1}, beta2={self.beta2}, "
                f"eps={self.eps}, weight_decay={self.weight_decay})")


class RMSprop(Optimizer):
    """RMSprop optimizer with momentum support."""
    
    def __init__(self, parameters: List[Tensor], lr: float = 0.01,
                 alpha: float = 0.99, eps: float = 1e-8,
                 momentum: float = 0.0, weight_decay: float = 0.0):
        super().__init__(parameters, lr)
        self.alpha = alpha
        self.eps = eps
        self.momentum = momentum
        self.weight_decay = weight_decay
        
        # Initialize squared gradient average
        self.sq_avg = [np.zeros_like(param.data) for param in self.parameters]
        
        # Initialize momentum buffer
        if momentum > 0:
            self.momentum_buffer = [np.zeros_like(param.data) for param in self.parameters]
        else:
            self.momentum_buffer = None
    
    def step(self):
        """Perform RMSprop optimization step."""
        for i, param in enumerate(self.parameters):
            if param.grad is None:
                continue
            
            grad = param.grad.copy()
            
            # Add weight decay
            if self.weight_decay != 0:
                grad += self.weight_decay * param.data
            
            # Update squared gradient average
            self.sq_avg[i] = self.alpha * self.sq_avg[i] + (1 - self.alpha) * (grad ** 2)
            
            # Compute step
            if self.momentum > 0:
                # Apply momentum
                self.momentum_buffer[i] = (self.momentum * self.momentum_buffer[i] + 
                                         grad / (np.sqrt(self.sq_avg[i]) + self.eps))
                step = self.momentum_buffer[i]
            else:
                step = grad / (np.sqrt(self.sq_avg[i]) + self.eps)
            
            # Update parameters
            param.data -= self.lr * step
        
        self.step_count += 1
    
    def __repr__(self):
        return (f"RMSprop(lr={self.lr}, alpha={self.alpha}, eps={self.eps}, "
                f"momentum={self.momentum}, weight_decay={self.weight_decay})")


# Learning rate schedulers
class LRScheduler(ABC):
    """Base class for learning rate schedulers."""
    
    def __init__(self, optimizer: Optimizer):
        self.optimizer = optimizer
        self.last_epoch = 0
    
    @abstractmethod
    def get_lr(self) -> float:
        """Calculate the learning rate for current epoch."""
        pass
    
    def step(self, epoch: int = None):
        """Update the learning rate."""
        if epoch is None:
            epoch = self.last_epoch + 1
        self.last_epoch = epoch
        self.optimizer.lr = self.get_lr()


class StepLR(LRScheduler):
    """Step learning rate scheduler."""
    
    def __init__(self, optimizer: Optimizer, step_size: int, gamma: float = 0.1):
        super().__init__(optimizer)
        self.step_size = step_size
        self.gamma = gamma
        self.base_lr = optimizer.lr
    
    def get_lr(self) -> float:
        return self.base_lr * (self.gamma ** (self.last_epoch // self.step_size))


class ExponentialLR(LRScheduler):
    """Exponential learning rate scheduler."""
    
    def __init__(self, optimizer: Optimizer, gamma: float):
        super().__init__(optimizer)
        self.gamma = gamma
        self.base_lr = optimizer.lr
    
    def get_lr(self) -> float:
        return self.base_lr * (self.gamma ** self.last_epoch)


class CosineAnnealingLR(LRScheduler):
    """Cosine annealing learning rate scheduler."""
    
    def __init__(self, optimizer: Optimizer, T_max: int, eta_min: float = 0):
        super().__init__(optimizer)
        self.T_max = T_max
        self.eta_min = eta_min
        self.base_lr = optimizer.lr
    
    def get_lr(self) -> float:
        return (self.eta_min + (self.base_lr - self.eta_min) * 
                (1 + math.cos(math.pi * self.last_epoch / self.T_max)) / 2)
