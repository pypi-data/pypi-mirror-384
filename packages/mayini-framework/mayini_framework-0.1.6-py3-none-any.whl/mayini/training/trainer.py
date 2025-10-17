"""
Training framework with DataLoader, Trainer, Metrics, and Early Stopping.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Union
from tqdm import tqdm
import time
import pickle
import json

from ..tensor import Tensor
from ..nn.modules import Module
from ..nn.losses import LossFunction
from ..optim.optimizers import Optimizer


class DataLoader:
    """DataLoader for batch processing with shuffling."""
    
    def __init__(self, X: Union[np.ndarray, Tensor], y: Union[np.ndarray, Tensor],
                 batch_size: int = 32, shuffle: bool = True):
        """
        Initialize DataLoader.
        
        Args:
            X: Input features
            y: Target labels
            batch_size: Batch size for training
            shuffle: Whether to shuffle data each epoch
        """
        # Convert to numpy arrays if needed
        if isinstance(X, Tensor):
            X = X.data
        if isinstance(y, Tensor):
            y = y.data
            
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        self.num_samples = len(X)
        self.num_batches = (self.num_samples + batch_size - 1) // batch_size
    
    def __iter__(self):
        """Iterator for batch processing."""
        if self.shuffle:
            indices = np.random.permutation(self.num_samples)
        else:
            indices = np.arange(self.num_samples)
        
        for i in range(0, self.num_samples, self.batch_size):
            batch_indices = indices[i:i + self.batch_size]
            batch_X = self.X[batch_indices]
            batch_y = self.y[batch_indices]
            
            # Convert to tensors
            batch_X_tensor = Tensor(batch_X, requires_grad=False)
            batch_y_tensor = Tensor(batch_y, requires_grad=False)
            
            yield batch_X_tensor, batch_y_tensor
    
    def __len__(self):
        """Return number of batches."""
        return self.num_batches


class Metrics:
    """Comprehensive metrics for model evaluation."""
    
    @staticmethod
    def accuracy(predictions: Tensor, targets: Tensor) -> float:
        """Compute classification accuracy."""
        if predictions.ndim > 1 and predictions.shape[1] > 1:
            pred_labels = np.argmax(predictions.data, axis=1)
        else:
            pred_labels = predictions.data.flatten().astype(int)
        
        if targets.ndim > 1 and targets.shape[1] > 1:
            true_labels = np.argmax(targets.data, axis=1)
        else:
            true_labels = targets.data.flatten().astype(int)
        
        return np.mean(pred_labels == true_labels)
    
    @staticmethod
    def precision_recall_f1(predictions: Tensor, targets: Tensor, 
                           num_classes: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute precision, recall, and F1-score for each class."""
        if predictions.ndim > 1 and predictions.shape[1] > 1:
            pred_labels = np.argmax(predictions.data, axis=1)
        else:
            pred_labels = predictions.data.flatten().astype(int)
        
        if targets.ndim > 1 and targets.shape[1] > 1:
            true_labels = np.argmax(targets.data, axis=1)
        else:
            true_labels = targets.data.flatten().astype(int)
        
        precision = np.zeros(num_classes)
        recall = np.zeros(num_classes)
        f1 = np.zeros(num_classes)
        
        for c in range(num_classes):
            tp = np.sum((pred_labels == c) & (true_labels == c))
            fp = np.sum((pred_labels == c) & (true_labels != c))
            fn = np.sum((pred_labels != c) & (true_labels == c))
            
            if tp + fp > 0:
                precision[c] = tp / (tp + fp)
            if tp + fn > 0:
                recall[c] = tp / (tp + fn)
            if precision[c] + recall[c] > 0:
                f1[c] = 2 * precision[c] * recall[c] / (precision[c] + recall[c])
        
        return precision, recall, f1
    
    @staticmethod
    def confusion_matrix(predictions: Tensor, targets: Tensor, 
                        num_classes: int) -> np.ndarray:
        """Compute confusion matrix."""
        if predictions.ndim > 1 and predictions.shape[1] > 1:
            pred_labels = np.argmax(predictions.data, axis=1)
        else:
            pred_labels = predictions.data.flatten().astype(int)
        
        if targets.ndim > 1 and targets.shape[1] > 1:
            true_labels = np.argmax(targets.data, axis=1)
        else:
            true_labels = targets.data.flatten().astype(int)
        
        cm = np.zeros((num_classes, num_classes), dtype=int)
        for true_label, pred_label in zip(true_labels, pred_labels):
            if 0 <= true_label < num_classes and 0 <= pred_label < num_classes:
                cm[true_label, pred_label] += 1
        
        return cm
    
    @staticmethod
    def mse(predictions: Tensor, targets: Tensor) -> float:
        """Compute mean squared error."""
        diff = predictions.data - targets.data
        return np.mean(diff ** 2)
    
    @staticmethod
    def mae(predictions: Tensor, targets: Tensor) -> float:
        """Compute mean absolute error."""
        diff = predictions.data - targets.data
        return np.mean(np.abs(diff))
    
    @staticmethod
    def r2_score(predictions: Tensor, targets: Tensor) -> float:
        """Compute R² score for regression."""
        ss_res = np.sum((targets.data - predictions.data) ** 2)
        ss_tot = np.sum((targets.data - np.mean(targets.data)) ** 2)
        
        if ss_tot == 0:
            return 1.0  # Perfect prediction when all targets are the same
        
        return 1 - (ss_res / ss_tot)


class EarlyStopping:
    """Early stopping to prevent overfitting."""
    
    def __init__(self, patience: int = 7, min_delta: float = 0.0, 
                 restore_best_weights: bool = True, mode: str = 'min'):
        """
        Initialize early stopping.
        
        Args:
            patience: Number of epochs with no improvement after which training will be stopped
            min_delta: Minimum change in the monitored quantity to qualify as an improvement
            restore_best_weights: Whether to restore model weights from the epoch with the best value
            mode: One of 'min' or 'max'. In 'min' mode, training will stop when the quantity 
                  monitored has stopped decreasing; in 'max' mode it will stop when the quantity 
                  monitored has stopped increasing
        """
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best_weights = restore_best_weights
        self.mode = mode
        
        self.wait = 0
        self.stopped_epoch = 0
        self.best_weights = None
        
        if mode == 'min':
            self.best = np.inf
            self.monitor_op = np.less
        else:
            self.best = -np.inf
            self.monitor_op = np.greater
    
    def __call__(self, current: float, model: Module) -> bool:
        """
        Check if training should be stopped.
        
        Args:
            current: Current value of the monitored quantity
            model: Model to potentially save weights from
            
        Returns:
            True if training should be stopped, False otherwise
        """
        if self.monitor_op(current - self.min_delta, self.best):
            self.best = current
            self.wait = 0
            if self.restore_best_weights:
                self.best_weights = self._save_weights(model)
        else:
            self.wait += 1
            if self.wait >= self.patience:
                self.stopped_epoch = True
                if self.restore_best_weights and self.best_weights is not None:
                    self._restore_weights(model, self.best_weights)
                return True
        
        return False
    
    def _save_weights(self, model: Module) -> Dict:
        """Save model weights."""
        weights = {}
        for i, param in enumerate(model.parameters()):
            weights[i] = param.data.copy()
        return weights
    
    def _restore_weights(self, model: Module, weights: Dict):
        """Restore model weights."""
        for i, param in enumerate(model.parameters()):
            if i in weights:
                param.data = weights[i].copy()


class Trainer:
    """Complete training framework with logging and checkpointing."""
    
    def __init__(self, model: Module, optimizer: Optimizer, criterion: LossFunction):
        """
        Initialize trainer.
        
        Args:
            model: Neural network model
            optimizer: Optimization algorithm
            criterion: Loss function
        """
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'epoch_times': []
        }
    
    def fit(self, train_loader: DataLoader, epochs: int = 10,
            val_loader: Optional[DataLoader] = None,
            early_stopping: Optional[EarlyStopping] = None,
            verbose: bool = True, save_best: bool = True,
            checkpoint_path: Optional[str] = None) -> Dict:
        """
        Train the model.
        
        Args:
            train_loader: Training data loader
            epochs: Number of training epochs
            val_loader: Validation data loader (optional)
            early_stopping: Early stopping callback (optional)
            verbose: Whether to print training progress
            save_best: Whether to save the best model
            checkpoint_path: Path to save checkpoints
            
        Returns:
            Dictionary containing training history
        """
        self.model.train()
        
        if verbose:
            print(f"Starting training for {epochs} epochs...")
            print("=" * 60)
        
        best_val_loss = np.inf
        
        for epoch in range(epochs):
            epoch_start_time = time.time()
            
            # Training phase
            train_loss, train_acc = self._train_epoch(train_loader, verbose)
            
            # Validation phase
            if val_loader is not None:
                val_loss, val_acc = self._validate_epoch(val_loader)
                self.history['val_loss'].append(val_loss)
                self.history['val_acc'].append(val_acc)
                
                # Check for best model
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    if save_best and checkpoint_path:
                        self.save_checkpoint(checkpoint_path, epoch, val_loss)
                
                # Early stopping
                if early_stopping is not None:
                    if early_stopping(val_loss, self.model):
                        if verbose:
                            print(f"\\nEarly stopping at epoch {epoch+1}")
                        break
            
            # Record history
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            
            epoch_time = time.time() - epoch_start_time
            self.history['epoch_times'].append(epoch_time)
            
            # Print progress
            if verbose:
                if val_loader is not None:
                    print(f"Epoch {epoch+1:3d}/{epochs} - "
                          f"train_loss: {train_loss:.4f} - train_acc: {train_acc:.4f} - "
                          f"val_loss: {val_loss:.4f} - val_acc: {val_acc:.4f} - "
                          f"time: {epoch_time:.2f}s")
                else:
                    print(f"Epoch {epoch+1:3d}/{epochs} - "
                          f"train_loss: {train_loss:.4f} - train_acc: {train_acc:.4f} - "
                          f"time: {epoch_time:.2f}s")
        
        if verbose:
            total_time = sum(self.history['epoch_times'])
            print("=" * 60)
            print(f"Training completed in {total_time:.2f}s")
            print(f"Best validation loss: {best_val_loss:.4f}")
        
        return self.history
    
    def _train_epoch(self, train_loader: DataLoader, verbose: bool = True) -> Tuple[float, float]:
        """Train for one epoch."""
        self.model.train()
        
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        
        if verbose:
            pbar = tqdm(train_loader, desc="Training", leave=False)
        else:
            pbar = train_loader
        
        for batch_X, batch_y in pbar:
            # Forward pass
            predictions = self.model(batch_X)
            loss = self.criterion(predictions, batch_y)
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            # Statistics
            total_loss += loss.item()
            total_correct += np.sum(np.argmax(predictions.data, axis=1) == batch_y.data.flatten())
            total_samples += len(batch_y.data)
            
            if verbose:
                pbar.set_postfix({'loss': f'{loss.item():.4f}'})
        
        avg_loss = total_loss / len(train_loader)
        accuracy = total_correct / total_samples
        
        return avg_loss, accuracy
    
    def _validate_epoch(self, val_loader: DataLoader) -> Tuple[float, float]:
        """Validate for one epoch."""
        self.model.eval()
        
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        
        for batch_X, batch_y in val_loader:
            # Forward pass (no gradient computation)
            predictions = self.model(batch_X)
            loss = self.criterion(predictions, batch_y)
            
            # Statistics
            total_loss += loss.item()
            total_correct += np.sum(np.argmax(predictions.data, axis=1) == batch_y.data.flatten())
            total_samples += len(batch_y.data)
        
        avg_loss = total_loss / len(val_loader)
        accuracy = total_correct / total_samples
        
        return avg_loss, accuracy
    
    def evaluate(self, test_loader: DataLoader, detailed: bool = True) -> Dict:
        """
        Evaluate the model on test data.
        
        Args:
            test_loader: Test data loader
            detailed: Whether to compute detailed metrics
            
        Returns:
            Dictionary containing evaluation metrics
        """
        self.model.eval()
        
        all_predictions = []
        all_targets = []
        total_loss = 0.0
        
        for batch_X, batch_y in test_loader:
            predictions = self.model(batch_X)
            loss = self.criterion(predictions, batch_y)
            
            all_predictions.append(predictions.data)
            all_targets.append(batch_y.data)
            total_loss += loss.item()
        
        # Concatenate all predictions and targets
        all_predictions = Tensor(np.concatenate(all_predictions, axis=0))
        all_targets = Tensor(np.concatenate(all_targets, axis=0))
        
        # Compute metrics
        results = {
            'test_loss': total_loss / len(test_loader),
            'accuracy': Metrics.accuracy(all_predictions, all_targets)
        }
        
        if detailed:
            num_classes = all_predictions.shape[1] if all_predictions.ndim > 1 else 2
            precision, recall, f1 = Metrics.precision_recall_f1(all_predictions, all_targets, num_classes)
            cm = Metrics.confusion_matrix(all_predictions, all_targets, num_classes)
            
            results.update({
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'confusion_matrix': cm
            })
        
        return results
    
    def predict(self, X: Union[np.ndarray, Tensor]) -> np.ndarray:
        """Make predictions on new data."""
        self.model.eval()
        
        if isinstance(X, np.ndarray):
            X = Tensor(X)
        
        predictions = self.model(X)
        return predictions.data
    
    def save_checkpoint(self, filepath: str, epoch: int, loss: float):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state': {i: param.data for i, param in enumerate(self.model.parameters())},
            'optimizer_state': {
                'lr': self.optimizer.lr,
                'step_count': self.optimizer.step_count
            },
            'loss': loss,
            'history': self.history
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)
    
    def load_checkpoint(self, filepath: str):
        """Load model checkpoint."""
        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)
        
        # Restore model parameters
        model_params = list(self.model.parameters())
        for i, param_data in checkpoint['model_state'].items():
            if i < len(model_params):
                model_params[i].data = param_data
        
        # Restore optimizer state
        self.optimizer.lr = checkpoint['optimizer_state']['lr']
        self.optimizer.step_count = checkpoint['optimizer_state']['step_count']
        
        # Restore history
        self.history = checkpoint['history']
        
        print(f"Loaded checkpoint from epoch {checkpoint['epoch']} with loss {checkpoint['loss']:.4f}")
        
        return checkpoint['epoch']
